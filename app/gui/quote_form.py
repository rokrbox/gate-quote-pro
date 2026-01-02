"""Quote creation and editing form for Gate Quote Pro."""
import customtkinter as ctk
from tkinter import messagebox
import subprocess
from typing import Optional, List

from ..models.quote import Quote, QuoteItem
from ..models.customer import Customer
from ..models.materials import Material
from ..models.database import get_db
from ..services.quote_calculator import get_calculator
from ..services.pdf_generator import get_pdf_generator


class QuoteForm(ctk.CTkFrame):
    """Form for creating and editing quotes."""

    GATE_TYPES = ["swing", "sliding", "cantilever", "bi-fold", "pedestrian"]
    GATE_STYLES = ["basic", "standard", "ornamental", "custom"]
    MATERIALS = ["steel", "aluminum", "wrought_iron", "wood", "chain_link"]
    AUTOMATION = ["none", "single_swing", "dual_swing", "slide"]
    ACCESS_CONTROL = ["none", "keypad", "remote", "intercom", "full_system"]
    GROUND_TYPES = ["concrete", "asphalt", "gravel", "dirt"]
    SLOPES = ["flat", "slight", "moderate", "steep"]

    def __init__(self, parent, quote: Quote = None, main_window=None):
        super().__init__(parent, fg_color="transparent")
        self.main_window = main_window
        self.quote = quote or Quote()
        self.items: List[QuoteItem] = list(self.quote.items) if self.quote.items else []

        self._create_layout()
        self._populate_form()

    def _create_layout(self):
        """Create the form layout."""
        # Scrollable container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        title_text = "Edit Quote" if self.quote.id else "New Quote"
        title = ctk.CTkLabel(
            header,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left")

        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        self.calculate_btn = ctk.CTkButton(
            btn_frame,
            text="Calculate",
            command=self._calculate_quote,
            fg_color="#3182ce",
            hover_color="#2c5282"
        )
        self.calculate_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Quote",
            command=self._save_quote,
            fg_color="#38a169",
            hover_color="#2f855a"
        )
        self.save_btn.pack(side="left", padx=5)

        self.pdf_btn = ctk.CTkButton(
            btn_frame,
            text="Generate PDF",
            command=self._generate_pdf,
            fg_color="#805ad5",
            hover_color="#6b46c1"
        )
        self.pdf_btn.pack(side="left", padx=5)

        # Two column layout
        columns = ctk.CTkFrame(self.scroll, fg_color="transparent")
        columns.pack(fill="both", expand=True)

        left_col = ctk.CTkFrame(columns, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_col = ctk.CTkFrame(columns, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Customer Section
        self._create_customer_section(left_col)

        # Gate Specifications Section
        self._create_gate_section(left_col)

        # Site Conditions Section
        self._create_site_section(left_col)

        # Materials Section
        self._create_materials_section(right_col)

        # Summary Section
        self._create_summary_section(right_col)

    def _create_section_header(self, parent, title: str):
        """Create a section header."""
        header = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", pady=(15, 10))

    def _create_customer_section(self, parent):
        """Create customer information section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=5)

        self._create_section_header(section, "Customer")

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=10)

        # Customer selection
        select_frame = ctk.CTkFrame(content, fg_color="transparent")
        select_frame.pack(fill="x", pady=5)

        customers = Customer.get_all()
        customer_names = ["-- Select Customer --"] + [c.name for c in customers]
        self.customer_map = {c.name: c for c in customers}

        self.customer_var = ctk.StringVar(value="-- Select Customer --")
        self.customer_select = ctk.CTkComboBox(
            select_frame,
            values=customer_names,
            variable=self.customer_var,
            command=self._on_customer_select,
            width=300
        )
        self.customer_select.pack(side="left")

        new_customer_btn = ctk.CTkButton(
            select_frame,
            text="+ New",
            width=70,
            command=self._new_customer_dialog
        )
        new_customer_btn.pack(side="left", padx=10)

        # Customer info display
        self.customer_info = ctk.CTkLabel(
            content,
            text="",
            justify="left",
            text_color="gray50"
        )
        self.customer_info.pack(anchor="w", pady=5)

    def _create_gate_section(self, parent):
        """Create gate specifications section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=5)

        self._create_section_header(section, "Gate Specifications")

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=10)

        # Grid layout for specs
        grid = ctk.CTkFrame(content, fg_color="transparent")
        grid.pack(fill="x")

        # Row 1: Type and Style
        row1 = ctk.CTkFrame(grid, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        ctk.CTkLabel(row1, text="Gate Type:", width=100).pack(side="left")
        self.gate_type_var = ctk.StringVar(value=self.quote.gate_type)
        self.gate_type = ctk.CTkComboBox(
            row1,
            values=self.GATE_TYPES,
            variable=self.gate_type_var,
            width=150
        )
        self.gate_type.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Style:", width=60).pack(side="left")
        self.gate_style_var = ctk.StringVar(value=self.quote.gate_style)
        self.gate_style = ctk.CTkComboBox(
            row1,
            values=self.GATE_STYLES,
            variable=self.gate_style_var,
            width=150
        )
        self.gate_style.pack(side="left")

        # Row 2: Dimensions
        row2 = ctk.CTkFrame(grid, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text="Width (ft):", width=100).pack(side="left")
        self.width_var = ctk.StringVar(value=str(self.quote.width))
        self.width_entry = ctk.CTkEntry(row2, textvariable=self.width_var, width=80)
        self.width_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row2, text="Height (ft):", width=80).pack(side="left")
        self.height_var = ctk.StringVar(value=str(self.quote.height))
        self.height_entry = ctk.CTkEntry(row2, textvariable=self.height_var, width=80)
        self.height_entry.pack(side="left")

        # Row 3: Material
        row3 = ctk.CTkFrame(grid, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        ctk.CTkLabel(row3, text="Material:", width=100).pack(side="left")
        self.material_var = ctk.StringVar(value=self.quote.material)
        self.material = ctk.CTkComboBox(
            row3,
            values=self.MATERIALS,
            variable=self.material_var,
            width=150
        )
        self.material.pack(side="left")

        # Row 4: Automation
        row4 = ctk.CTkFrame(grid, fg_color="transparent")
        row4.pack(fill="x", pady=5)

        ctk.CTkLabel(row4, text="Automation:", width=100).pack(side="left")
        self.automation_var = ctk.StringVar(value=self.quote.automation)
        self.automation = ctk.CTkComboBox(
            row4,
            values=self.AUTOMATION,
            variable=self.automation_var,
            width=150
        )
        self.automation.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row4, text="Access:", width=60).pack(side="left")
        self.access_var = ctk.StringVar(value=self.quote.access_control)
        self.access = ctk.CTkComboBox(
            row4,
            values=self.ACCESS_CONTROL,
            variable=self.access_var,
            width=150
        )
        self.access.pack(side="left")

    def _create_site_section(self, parent):
        """Create site conditions section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=5)

        self._create_section_header(section, "Site Conditions")

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=10)

        grid = ctk.CTkFrame(content, fg_color="transparent")
        grid.pack(fill="x")

        # Row 1: Ground and Slope
        row1 = ctk.CTkFrame(grid, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        ctk.CTkLabel(row1, text="Ground:", width=100).pack(side="left")
        self.ground_var = ctk.StringVar(value=self.quote.ground_type)
        self.ground = ctk.CTkComboBox(
            row1,
            values=self.GROUND_TYPES,
            variable=self.ground_var,
            width=120
        )
        self.ground.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Slope:", width=60).pack(side="left")
        self.slope_var = ctk.StringVar(value=self.quote.slope)
        self.slope = ctk.CTkComboBox(
            row1,
            values=self.SLOPES,
            variable=self.slope_var,
            width=120
        )
        self.slope.pack(side="left")

        # Row 2: Power distance
        row2 = ctk.CTkFrame(grid, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text="Power Dist (ft):", width=100).pack(side="left")
        self.power_var = ctk.StringVar(value=str(self.quote.power_distance))
        self.power_entry = ctk.CTkEntry(row2, textvariable=self.power_var, width=80)
        self.power_entry.pack(side="left")

        # Row 3: Removal needed
        row3 = ctk.CTkFrame(grid, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        self.removal_var = ctk.BooleanVar(value=self.quote.removal_needed)
        self.removal_check = ctk.CTkCheckBox(
            row3,
            text="Existing gate removal needed",
            variable=self.removal_var
        )
        self.removal_check.pack(side="left")

    def _create_materials_section(self, parent):
        """Create materials/line items section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=5)

        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="Materials & Equipment",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        add_btn = ctk.CTkButton(
            header,
            text="+ Add Item",
            width=80,
            height=28,
            command=self._add_material_dialog
        )
        add_btn.pack(side="right")

        suggest_btn = ctk.CTkButton(
            header,
            text="Auto-Suggest",
            width=100,
            height=28,
            fg_color="gray50",
            command=self._suggest_materials
        )
        suggest_btn.pack(side="right", padx=5)

        # Items list
        self.items_frame = ctk.CTkScrollableFrame(section, height=200)
        self.items_frame.pack(fill="x", padx=15, pady=10)

        self._refresh_items_list()

    def _refresh_items_list(self):
        """Refresh the materials list display."""
        for widget in self.items_frame.winfo_children():
            widget.destroy()

        if not self.items:
            empty = ctk.CTkLabel(
                self.items_frame,
                text="No items added. Click 'Auto-Suggest' or 'Add Item'.",
                text_color="gray50"
            )
            empty.pack(pady=20)
            return

        # Header row
        header = ctk.CTkFrame(self.items_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))

        headers = [("Description", 200), ("Qty", 50), ("Unit", 50), ("Cost", 70), ("Total", 80), ("", 30)]
        for text, width in headers:
            ctk.CTkLabel(
                header,
                text=text,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="left", padx=2)

        # Item rows
        for i, item in enumerate(self.items):
            self._create_item_row(i, item)

    def _create_item_row(self, index: int, item: QuoteItem):
        """Create a row for a line item."""
        row = ctk.CTkFrame(self.items_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=item.description[:30], width=200, anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row, text=f"{item.quantity:.1f}", width=50).pack(side="left", padx=2)
        ctk.CTkLabel(row, text=item.unit, width=50).pack(side="left", padx=2)
        ctk.CTkLabel(row, text=f"${item.unit_cost:.2f}", width=70).pack(side="left", padx=2)
        ctk.CTkLabel(row, text=f"${item.total_cost:.2f}", width=80).pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            row,
            text="X",
            width=30,
            height=24,
            fg_color="red",
            hover_color="darkred",
            command=lambda idx=index: self._remove_item(idx)
        )
        del_btn.pack(side="left", padx=2)

    def _create_summary_section(self, parent):
        """Create quote summary section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=5)

        self._create_section_header(section, "Quote Summary")

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=10)

        # Labor
        labor_frame = ctk.CTkFrame(content, fg_color="transparent")
        labor_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(labor_frame, text="Labor Hours:", width=120).pack(side="left")
        self.labor_hours_var = ctk.StringVar(value=str(self.quote.labor_hours))
        self.labor_hours = ctk.CTkEntry(labor_frame, textvariable=self.labor_hours_var, width=80)
        self.labor_hours.pack(side="left")

        ctk.CTkLabel(labor_frame, text="@ $", width=30).pack(side="left", padx=(10, 0))
        self.labor_rate_var = ctk.StringVar(value=str(self.quote.labor_rate))
        self.labor_rate = ctk.CTkEntry(labor_frame, textvariable=self.labor_rate_var, width=80)
        self.labor_rate.pack(side="left")
        ctk.CTkLabel(labor_frame, text="/hr").pack(side="left")

        # Totals
        totals_frame = ctk.CTkFrame(content)
        totals_frame.pack(fill="x", pady=10)

        self.materials_label = ctk.CTkLabel(totals_frame, text="Materials: $0.00")
        self.materials_label.pack(anchor="e", padx=15, pady=2)

        self.labor_label = ctk.CTkLabel(totals_frame, text="Labor: $0.00")
        self.labor_label.pack(anchor="e", padx=15, pady=2)

        self.subtotal_label = ctk.CTkLabel(totals_frame, text="Subtotal: $0.00")
        self.subtotal_label.pack(anchor="e", padx=15, pady=2)

        self.total_label = ctk.CTkLabel(
            totals_frame,
            text="TOTAL: $0.00",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.total_label.pack(anchor="e", padx=15, pady=5)

        # Notes
        notes_frame = ctk.CTkFrame(content, fg_color="transparent")
        notes_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(notes_frame, text="Notes:").pack(anchor="w")
        self.notes_text = ctk.CTkTextbox(notes_frame, height=80)
        self.notes_text.pack(fill="x", pady=5)
        if self.quote.notes:
            self.notes_text.insert("1.0", self.quote.notes)

    def _populate_form(self):
        """Populate form with existing quote data."""
        if self.quote.customer:
            self.customer_var.set(self.quote.customer.name)
            self._update_customer_info(self.quote.customer)

        self._update_summary()

    def _on_customer_select(self, selection):
        """Handle customer selection."""
        if selection in self.customer_map:
            customer = self.customer_map[selection]
            self.quote.customer_id = customer.id
            self.quote.customer = customer
            self._update_customer_info(customer)
        else:
            self.quote.customer_id = None
            self.quote.customer = None
            self.customer_info.configure(text="")

    def _update_customer_info(self, customer: Customer):
        """Update customer info display."""
        info_parts = []
        if customer.address:
            info_parts.append(customer.address)
        if customer.city or customer.state:
            info_parts.append(f"{customer.city}, {customer.state} {customer.zip_code}".strip())
        if customer.phone:
            info_parts.append(f"Phone: {customer.phone}")
        if customer.email:
            info_parts.append(f"Email: {customer.email}")

        self.customer_info.configure(text="\n".join(info_parts))

    def _new_customer_dialog(self):
        """Show dialog to create new customer."""
        dialog = CustomerDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            # Refresh customer list
            customers = Customer.get_all()
            customer_names = ["-- Select Customer --"] + [c.name for c in customers]
            self.customer_map = {c.name: c for c in customers}
            self.customer_select.configure(values=customer_names)
            self.customer_var.set(dialog.result.name)
            self._on_customer_select(dialog.result.name)

    def _add_material_dialog(self):
        """Show dialog to add material."""
        dialog = MaterialDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            self.items.append(dialog.result)
            self._refresh_items_list()
            self._update_summary()

    def _suggest_materials(self):
        """Auto-suggest materials based on specifications."""
        self._update_quote_from_form()
        calculator = get_calculator()
        suggested = calculator.suggest_materials(self.quote)

        if suggested:
            self.items = suggested
            self._refresh_items_list()
            self._update_summary()
            messagebox.showinfo("Materials Suggested", f"Added {len(suggested)} suggested items based on specifications.")
        else:
            messagebox.showinfo("No Suggestions", "No materials could be suggested. Check your price list.")

    def _remove_item(self, index: int):
        """Remove an item from the list."""
        if 0 <= index < len(self.items):
            del self.items[index]
            self._refresh_items_list()
            self._update_summary()

    def _update_quote_from_form(self):
        """Update quote object from form values."""
        self.quote.gate_type = self.gate_type_var.get()
        self.quote.gate_style = self.gate_style_var.get()
        self.quote.material = self.material_var.get()
        self.quote.automation = self.automation_var.get()
        self.quote.access_control = self.access_var.get()
        self.quote.ground_type = self.ground_var.get()
        self.quote.slope = self.slope_var.get()
        self.quote.removal_needed = self.removal_var.get()

        try:
            self.quote.width = float(self.width_var.get())
        except ValueError:
            self.quote.width = 12.0

        try:
            self.quote.height = float(self.height_var.get())
        except ValueError:
            self.quote.height = 6.0

        try:
            self.quote.power_distance = float(self.power_var.get())
        except ValueError:
            self.quote.power_distance = 0.0

        try:
            self.quote.labor_hours = float(self.labor_hours_var.get())
        except ValueError:
            pass

        try:
            self.quote.labor_rate = float(self.labor_rate_var.get())
        except ValueError:
            pass

        self.quote.notes = self.notes_text.get("1.0", "end").strip()
        self.quote.items = self.items

    def _calculate_quote(self):
        """Calculate quote totals."""
        self._update_quote_from_form()
        calculator = get_calculator()
        self.quote = calculator.calculate_quote(self.quote)

        # Update form with calculated values
        self.labor_hours_var.set(str(self.quote.labor_hours))
        self.labor_rate_var.set(str(self.quote.labor_rate))
        self.items = self.quote.items

        self._refresh_items_list()
        self._update_summary()

    def _update_summary(self):
        """Update the summary display."""
        materials_total = sum(item.total_cost for item in self.items)

        try:
            labor_hours = float(self.labor_hours_var.get())
            labor_rate = float(self.labor_rate_var.get())
        except ValueError:
            labor_hours = 0
            labor_rate = 0

        labor_total = labor_hours * labor_rate

        db = get_db()
        markup = float(db.get_setting('markup_percent', '30'))
        materials_with_markup = materials_total * (1 + markup / 100)

        subtotal = materials_with_markup + labor_total

        self.materials_label.configure(text=f"Materials (w/ {markup:.0f}% markup): ${materials_with_markup:.2f}")
        self.labor_label.configure(text=f"Labor ({labor_hours:.1f} hrs): ${labor_total:.2f}")
        self.subtotal_label.configure(text=f"Subtotal: ${subtotal:.2f}")
        self.total_label.configure(text=f"TOTAL: ${subtotal:.2f}")

    def _save_quote(self):
        """Save the quote to database."""
        self._update_quote_from_form()
        self.quote.calculate_totals()

        try:
            self.quote.save()
            messagebox.showinfo("Saved", f"Quote {self.quote.quote_number} saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save quote: {e}")

    def _generate_pdf(self):
        """Generate and open PDF quote."""
        self._update_quote_from_form()
        self.quote.calculate_totals()

        # Save first if new
        if not self.quote.id:
            self.quote.save()

        try:
            generator = get_pdf_generator()
            pdf_path = generator.generate(self.quote)
            subprocess.run(['open', pdf_path])
            messagebox.showinfo("PDF Generated", f"Quote saved to:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")


class CustomerDialog(ctk.CTkToplevel):
    """Dialog for creating a new customer."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result: Optional[Customer] = None

        self.title("New Customer")
        self.geometry("400x450")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_form()

    def _create_form(self):
        """Create the customer form."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        fields = [
            ("Name*:", "name"),
            ("Email:", "email"),
            ("Phone:", "phone"),
            ("Address:", "address"),
            ("City:", "city"),
            ("State:", "state"),
            ("ZIP:", "zip_code"),
        ]

        self.entries = {}

        for label_text, field_name in fields:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=5)

            ctk.CTkLabel(row, text=label_text, width=80).pack(side="left")
            entry = ctk.CTkEntry(row, width=250)
            entry.pack(side="left")
            self.entries[field_name] = entry

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="gray50",
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Save Customer",
            command=self._save
        ).pack(side="right")

    def _save(self):
        """Save the customer."""
        name = self.entries['name'].get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return

        customer = Customer(
            name=name,
            email=self.entries['email'].get().strip(),
            phone=self.entries['phone'].get().strip(),
            address=self.entries['address'].get().strip(),
            city=self.entries['city'].get().strip(),
            state=self.entries['state'].get().strip(),
            zip_code=self.entries['zip_code'].get().strip()
        )
        customer.save()
        self.result = customer
        self.destroy()


class MaterialDialog(ctk.CTkToplevel):
    """Dialog for adding a material/line item."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result: Optional[QuoteItem] = None

        self.title("Add Material")
        self.geometry("450x350")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self._create_form()

    def _create_form(self):
        """Create the material form."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Category selection
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        ctk.CTkLabel(row1, text="Category:", width=80).pack(side="left")
        categories = Material.get_categories() or ["gates", "operators", "hardware", "access_control", "electrical", "misc"]
        self.category_var = ctk.StringVar(value=categories[0] if categories else "misc")
        self.category = ctk.CTkComboBox(
            row1,
            values=categories,
            variable=self.category_var,
            command=self._on_category_change,
            width=150
        )
        self.category.pack(side="left")

        # Material selection
        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text="Material:", width=80).pack(side="left")
        self.material_var = ctk.StringVar()
        self.material = ctk.CTkComboBox(
            row2,
            values=[],
            variable=self.material_var,
            command=self._on_material_change,
            width=280
        )
        self.material.pack(side="left")

        # Or custom description
        row3 = ctk.CTkFrame(frame, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        ctk.CTkLabel(row3, text="Or Custom:", width=80).pack(side="left")
        self.custom_entry = ctk.CTkEntry(row3, width=280, placeholder_text="Enter custom description")
        self.custom_entry.pack(side="left")

        # Quantity
        row4 = ctk.CTkFrame(frame, fg_color="transparent")
        row4.pack(fill="x", pady=5)

        ctk.CTkLabel(row4, text="Quantity:", width=80).pack(side="left")
        self.qty_var = ctk.StringVar(value="1")
        self.qty_entry = ctk.CTkEntry(row4, textvariable=self.qty_var, width=80)
        self.qty_entry.pack(side="left")

        ctk.CTkLabel(row4, text="Unit:", width=50).pack(side="left", padx=(20, 0))
        self.unit_var = ctk.StringVar(value="each")
        self.unit_entry = ctk.CTkEntry(row4, textvariable=self.unit_var, width=80)
        self.unit_entry.pack(side="left")

        # Unit cost
        row5 = ctk.CTkFrame(frame, fg_color="transparent")
        row5.pack(fill="x", pady=5)

        ctk.CTkLabel(row5, text="Unit Cost $:", width=80).pack(side="left")
        self.cost_var = ctk.StringVar(value="0.00")
        self.cost_entry = ctk.CTkEntry(row5, textvariable=self.cost_var, width=100)
        self.cost_entry.pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="gray50",
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Add Item",
            command=self._add
        ).pack(side="right")

        # Load initial materials
        self._on_category_change(self.category_var.get())

    def _on_category_change(self, category):
        """Handle category change."""
        materials = Material.get_by_category(category)
        names = [m.name for m in materials]
        self.material.configure(values=names)
        self.materials_map = {m.name: m for m in materials}

        if names:
            self.material_var.set(names[0])
            self._on_material_change(names[0])

    def _on_material_change(self, name):
        """Handle material selection."""
        if name in self.materials_map:
            m = self.materials_map[name]
            self.unit_var.set(m.unit)
            self.cost_var.set(f"{m.cost:.2f}")

    def _add(self):
        """Add the item."""
        description = self.custom_entry.get().strip() or self.material_var.get()
        if not description:
            messagebox.showerror("Error", "Select a material or enter custom description")
            return

        try:
            qty = float(self.qty_var.get())
            cost = float(self.cost_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or cost")
            return

        item = QuoteItem(
            category=self.category_var.get(),
            description=description,
            quantity=qty,
            unit=self.unit_var.get(),
            unit_cost=cost
        )
        item.calculate_total()

        self.result = item
        self.destroy()
