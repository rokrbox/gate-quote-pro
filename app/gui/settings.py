"""Settings panel for Gate Quote Pro."""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path

from ..models.database import get_db


class SettingsPanel(ctk.CTkFrame):
    """Settings configuration panel."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.db = get_db()

        self._create_layout()
        self._load_settings()

    def _create_layout(self):
        """Create the settings layout."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        title = ctk.CTkLabel(
            header,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left")

        save_btn = ctk.CTkButton(
            header,
            text="Save Settings",
            command=self._save_settings,
            fg_color="green",
            hover_color="darkgreen"
        )
        save_btn.pack(side="right")

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Company Information Section
        self._create_company_section(scroll)

        # Quote Settings Section
        self._create_quote_section(scroll)

        # Appearance Section
        self._create_appearance_section(scroll)

        # Data Section
        self._create_data_section(scroll)

    def _create_section(self, parent, title: str) -> ctk.CTkFrame:
        """Create a settings section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=10)

        header = ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(anchor="w", padx=15, pady=(15, 10))

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 15))

        return content

    def _create_field(self, parent, label: str, width: int = 300) -> ctk.CTkEntry:
        """Create a labeled entry field."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)

        ctk.CTkLabel(row, text=label, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=width)
        entry.pack(side="left")

        return entry

    def _create_company_section(self, parent):
        """Create company information section."""
        content = self._create_section(parent, "Company Information")

        self.company_name = self._create_field(content, "Company Name:")
        self.company_address = self._create_field(content, "Address:")
        self.company_phone = self._create_field(content, "Phone:")
        self.company_email = self._create_field(content, "Email:")
        self.company_license = self._create_field(content, "License #:")

        # Logo
        logo_row = ctk.CTkFrame(content, fg_color="transparent")
        logo_row.pack(fill="x", pady=5)

        ctk.CTkLabel(logo_row, text="Logo:", width=120, anchor="w").pack(side="left")

        self.logo_path_var = ctk.StringVar(value="No logo selected")
        logo_label = ctk.CTkLabel(
            logo_row,
            textvariable=self.logo_path_var,
            text_color="gray50",
            width=200
        )
        logo_label.pack(side="left")

        ctk.CTkButton(
            logo_row,
            text="Choose...",
            width=80,
            command=self._choose_logo
        ).pack(side="left", padx=10)

    def _create_quote_section(self, parent):
        """Create quote settings section."""
        content = self._create_section(parent, "Quote Settings")

        # Labor rate
        rate_row = ctk.CTkFrame(content, fg_color="transparent")
        rate_row.pack(fill="x", pady=5)

        ctk.CTkLabel(rate_row, text="Labor Rate:", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(rate_row, text="$").pack(side="left")
        self.labor_rate = ctk.CTkEntry(rate_row, width=80)
        self.labor_rate.pack(side="left")
        ctk.CTkLabel(rate_row, text="/hour").pack(side="left")

        # Markup
        markup_row = ctk.CTkFrame(content, fg_color="transparent")
        markup_row.pack(fill="x", pady=5)

        ctk.CTkLabel(markup_row, text="Materials Markup:", width=120, anchor="w").pack(side="left")
        self.markup_percent = ctk.CTkEntry(markup_row, width=80)
        self.markup_percent.pack(side="left")
        ctk.CTkLabel(markup_row, text="%").pack(side="left")

        # Tax rate
        tax_row = ctk.CTkFrame(content, fg_color="transparent")
        tax_row.pack(fill="x", pady=5)

        ctk.CTkLabel(tax_row, text="Tax Rate:", width=120, anchor="w").pack(side="left")
        self.tax_rate = ctk.CTkEntry(tax_row, width=80)
        self.tax_rate.pack(side="left")
        ctk.CTkLabel(tax_row, text="%").pack(side="left")

        # Quote prefix
        self.quote_prefix = self._create_field(content, "Quote Prefix:", width=100)

        # Terms
        terms_row = ctk.CTkFrame(content, fg_color="transparent")
        terms_row.pack(fill="x", pady=5)

        ctk.CTkLabel(terms_row, text="Terms:", width=120, anchor="nw").pack(side="left")
        self.quote_terms = ctk.CTkTextbox(terms_row, width=400, height=100)
        self.quote_terms.pack(side="left")

    def _create_appearance_section(self, parent):
        """Create appearance settings section."""
        content = self._create_section(parent, "Appearance")

        # Theme
        theme_row = ctk.CTkFrame(content, fg_color="transparent")
        theme_row.pack(fill="x", pady=5)

        ctk.CTkLabel(theme_row, text="Theme:", width=120, anchor="w").pack(side="left")

        self.theme_var = ctk.StringVar(value="system")
        themes = ["system", "light", "dark"]
        self.theme_select = ctk.CTkComboBox(
            theme_row,
            values=themes,
            variable=self.theme_var,
            command=self._change_theme,
            width=150
        )
        self.theme_select.pack(side="left")

    def _create_data_section(self, parent):
        """Create data management section."""
        content = self._create_section(parent, "Data Management")

        # Database info
        db_path = self.db.db_path
        info_row = ctk.CTkFrame(content, fg_color="transparent")
        info_row.pack(fill="x", pady=5)

        ctk.CTkLabel(info_row, text="Database:", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(info_row, text=db_path, text_color="gray50").pack(side="left")

        # Action buttons
        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", pady=15)

        ctk.CTkButton(
            btn_row,
            text="Backup Database",
            fg_color="gray50",
            command=self._backup_database
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Reset to Defaults",
            fg_color="orange",
            hover_color="darkorange",
            command=self._reset_defaults
        ).pack(side="left")

    def _load_settings(self):
        """Load settings from database."""
        settings = self.db.get_all_settings()

        self.company_name.insert(0, settings.get('company_name', ''))
        self.company_address.insert(0, settings.get('company_address', ''))
        self.company_phone.insert(0, settings.get('company_phone', ''))
        self.company_email.insert(0, settings.get('company_email', ''))
        self.company_license.insert(0, settings.get('company_license', ''))

        self.labor_rate.insert(0, settings.get('labor_rate', '125.00'))
        self.markup_percent.insert(0, settings.get('markup_percent', '30'))
        self.tax_rate.insert(0, settings.get('tax_rate', '0.0'))
        self.quote_prefix.insert(0, settings.get('quote_prefix', 'GQ'))
        self.quote_terms.insert("1.0", settings.get('quote_terms', ''))

        logo = settings.get('logo_path', '')
        if logo:
            self.logo_path_var.set(Path(logo).name)

        theme = settings.get('theme', 'system')
        self.theme_var.set(theme)

    def _save_settings(self):
        """Save settings to database."""
        try:
            # Validate numeric fields
            float(self.labor_rate.get())
            float(self.markup_percent.get())
            float(self.tax_rate.get())
        except ValueError:
            messagebox.showerror("Error", "Labor rate, markup, and tax must be numbers")
            return

        settings = {
            'company_name': self.company_name.get().strip(),
            'company_address': self.company_address.get().strip(),
            'company_phone': self.company_phone.get().strip(),
            'company_email': self.company_email.get().strip(),
            'company_license': self.company_license.get().strip(),
            'labor_rate': self.labor_rate.get().strip(),
            'markup_percent': self.markup_percent.get().strip(),
            'tax_rate': self.tax_rate.get().strip(),
            'quote_prefix': self.quote_prefix.get().strip() or 'GQ',
            'quote_terms': self.quote_terms.get("1.0", "end").strip(),
            'theme': self.theme_var.get()
        }

        for key, value in settings.items():
            self.db.set_setting(key, value)

        messagebox.showinfo("Saved", "Settings saved successfully!")

    def _choose_logo(self):
        """Choose a logo file."""
        file_path = filedialog.askopenfilename(
            title="Choose Logo",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.db.set_setting('logo_path', file_path)
            self.logo_path_var.set(Path(file_path).name)

    def _change_theme(self, theme: str):
        """Change the application theme."""
        ctk.set_appearance_mode(theme)
        self.db.set_setting('theme', theme)

    def _backup_database(self):
        """Backup the database."""
        import shutil
        from datetime import datetime

        file_path = filedialog.asksaveasfilename(
            title="Backup Database",
            defaultextension=".db",
            initialfile=f"gatequote_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )

        if file_path:
            try:
                shutil.copy2(self.db.db_path, file_path)
                messagebox.showinfo("Backup Complete", f"Database backed up to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Backup Error", str(e))

    def _reset_defaults(self):
        """Reset settings to defaults."""
        if messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n\nThis will not delete customers, quotes, or materials."
        ):
            defaults = {
                'company_name': 'Your Gate Company',
                'company_address': '',
                'company_phone': '',
                'company_email': '',
                'company_license': '',
                'labor_rate': '125.00',
                'markup_percent': '30',
                'tax_rate': '0.0',
                'quote_prefix': 'GQ',
                'quote_terms': 'Quote valid for 30 days. 50% deposit required to begin work. Balance due upon completion.',
                'theme': 'system'
            }

            for key, value in defaults.items():
                self.db.set_setting(key, value)

            # Clear and reload form
            for widget in [self.company_name, self.company_address, self.company_phone,
                          self.company_email, self.company_license, self.labor_rate,
                          self.markup_percent, self.tax_rate, self.quote_prefix]:
                widget.delete(0, 'end')

            self.quote_terms.delete("1.0", "end")
            self._load_settings()

            messagebox.showinfo("Reset Complete", "Settings have been reset to defaults.")
