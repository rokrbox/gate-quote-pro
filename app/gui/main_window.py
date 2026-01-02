"""Main application window for Gate Quote Pro."""
import customtkinter as ctk
from typing import Optional

from .quote_form import QuoteForm
from .customer_manager import CustomerManager
from .price_list import PriceListManager
from .settings import SettingsPanel
from ..models.database import get_db
from ..models.materials import Material


class MainWindow(ctk.CTk):
    """Main application window with navigation sidebar."""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Gate Quote Pro")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Set appearance
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Initialize database and load defaults
        self._init_database()

        # Create layout
        self._create_sidebar()
        self._create_main_area()

        # Show default view
        self.show_quote_form()

    def _init_database(self):
        """Initialize database and load default materials if needed."""
        db = get_db()
        # Load default materials if none exist
        Material.load_defaults()

    def _create_sidebar(self):
        """Create navigation sidebar."""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # Logo/Title
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 30))

        title_label = ctk.CTkLabel(
            title_frame,
            text="Gate Quote Pro",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack()

        # Navigation buttons
        self.nav_buttons = {}

        nav_items = [
            ("new_quote", "New Quote", self.show_quote_form),
            ("quotes", "Quote History", self.show_quote_history),
            ("customers", "Customers", self.show_customers),
            ("price_list", "Price List", self.show_price_list),
            ("settings", "Settings", self.show_settings),
        ]

        for key, label, command in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                command=command,
                height=40,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                font=ctk.CTkFont(size=14)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons[key] = btn

        # Spacer
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Version info
        version_label = ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        version_label.pack(pady=10)

    def _create_main_area(self):
        """Create main content area."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=0, pady=0)

        # Container for views
        self.view_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.view_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Current view reference
        self.current_view: Optional[ctk.CTkFrame] = None

    def _set_active_nav(self, active_key: str):
        """Set the active navigation button."""
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

    def _clear_view(self):
        """Clear current view."""
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    def show_quote_form(self, quote=None):
        """Show the quote creation/edit form."""
        self._clear_view()
        self._set_active_nav("new_quote")
        self.current_view = QuoteForm(self.view_container, quote=quote, main_window=self)
        self.current_view.pack(fill="both", expand=True)

    def show_quote_history(self):
        """Show quote history list."""
        self._clear_view()
        self._set_active_nav("quotes")
        self.current_view = QuoteHistoryView(self.view_container, main_window=self)
        self.current_view.pack(fill="both", expand=True)

    def show_customers(self):
        """Show customer management view."""
        self._clear_view()
        self._set_active_nav("customers")
        self.current_view = CustomerManager(self.view_container, main_window=self)
        self.current_view.pack(fill="both", expand=True)

    def show_price_list(self):
        """Show price list management view."""
        self._clear_view()
        self._set_active_nav("price_list")
        self.current_view = PriceListManager(self.view_container, main_window=self)
        self.current_view.pack(fill="both", expand=True)

    def show_settings(self):
        """Show settings panel."""
        self._clear_view()
        self._set_active_nav("settings")
        self.current_view = SettingsPanel(self.view_container)
        self.current_view.pack(fill="both", expand=True)


class QuoteHistoryView(ctk.CTkFrame):
    """View for displaying quote history."""

    def __init__(self, parent, main_window=None):
        super().__init__(parent, fg_color="transparent")
        self.main_window = main_window

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        title = ctk.CTkLabel(
            header,
            text="Quote History",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left")

        new_btn = ctk.CTkButton(
            header,
            text="+ New Quote",
            command=lambda: main_window.show_quote_form() if main_window else None
        )
        new_btn.pack(side="right")

        # Filter frame
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(filter_frame, text="Filter:").pack(side="left", padx=(0, 10))

        self.status_filter = ctk.CTkComboBox(
            filter_frame,
            values=["All", "Draft", "Sent", "Accepted", "Declined"],
            command=self._filter_quotes,
            width=150
        )
        self.status_filter.set("All")
        self.status_filter.pack(side="left")

        # Quotes list
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True)

        self._load_quotes()

    def _load_quotes(self, status: str = None):
        """Load quotes from database."""
        from ..models.quote import Quote

        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        quotes = Quote.get_all(status=status.lower() if status and status != "All" else None)

        if not quotes:
            empty_label = ctk.CTkLabel(
                self.list_frame,
                text="No quotes found",
                text_color="gray50"
            )
            empty_label.pack(pady=50)
            return

        for quote in quotes:
            self._create_quote_row(quote)

    def _create_quote_row(self, quote):
        """Create a row for a quote."""
        row = ctk.CTkFrame(self.list_frame)
        row.pack(fill="x", pady=5)

        # Quote info
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        quote_num = ctk.CTkLabel(
            info_frame,
            text=quote.quote_number,
            font=ctk.CTkFont(weight="bold")
        )
        quote_num.pack(anchor="w")

        customer_name = quote.customer.name if quote.customer else "No customer"
        details = f"{customer_name} | {quote.gate_type.title()} {quote.width}ft x {quote.height}ft | ${quote.total:.2f}"
        details_label = ctk.CTkLabel(
            info_frame,
            text=details,
            text_color="gray50"
        )
        details_label.pack(anchor="w")

        # Status badge
        status_colors = {
            'draft': ('gray70', 'gray30'),
            'sent': ('#3182ce', '#2b6cb0'),
            'accepted': ('#38a169', '#2f855a'),
            'declined': ('#e53e3e', '#c53030')
        }

        status_color = status_colors.get(quote.status, ('gray70', 'gray30'))
        status_badge = ctk.CTkLabel(
            row,
            text=quote.status.upper(),
            fg_color=status_color,
            corner_radius=4,
            width=80,
            height=24
        )
        status_badge.pack(side="right", padx=10)

        # Action buttons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            width=60,
            height=28,
            command=lambda q=quote: self._edit_quote(q)
        )
        edit_btn.pack(side="left", padx=2)

        pdf_btn = ctk.CTkButton(
            btn_frame,
            text="PDF",
            width=60,
            height=28,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda q=quote: self._generate_pdf(q)
        )
        pdf_btn.pack(side="left", padx=2)

    def _filter_quotes(self, status: str):
        """Filter quotes by status."""
        self._load_quotes(status if status != "All" else None)

    def _edit_quote(self, quote):
        """Open quote for editing."""
        from ..models.quote import Quote
        full_quote = Quote.get_by_id(quote.id)
        if full_quote and self.main_window:
            self.main_window.show_quote_form(quote=full_quote)

    def _generate_pdf(self, quote):
        """Generate PDF for quote."""
        from ..models.quote import Quote
        from ..services.pdf_generator import get_pdf_generator
        import subprocess

        full_quote = Quote.get_by_id(quote.id)
        if full_quote:
            generator = get_pdf_generator()
            pdf_path = generator.generate(full_quote)

            # Open the PDF
            subprocess.run(['open', pdf_path])
