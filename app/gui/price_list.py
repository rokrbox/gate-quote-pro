"""Price list management view for Gate Quote Pro."""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import webbrowser
from typing import Optional

from ..models.materials import Material
from ..services.supplier_api import get_supplier_api, PriceResult


class PriceListManager(ctk.CTkFrame):
    """View for managing the price list."""

    def __init__(self, parent, main_window=None):
        super().__init__(parent, fg_color="transparent")
        self.main_window = main_window
        self.selected_material: Optional[Material] = None

        self._create_layout()
        self._load_materials()

    def _create_layout(self):
        """Create the layout."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        title = ctk.CTkLabel(
            header,
            text="Price List",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left")

        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        add_btn = ctk.CTkButton(
            btn_frame,
            text="+ Add Item",
            command=self._add_material
        )
        add_btn.pack(side="left", padx=5)

        import_btn = ctk.CTkButton(
            btn_frame,
            text="Import CSV",
            fg_color="gray50",
            command=self._import_csv
        )
        import_btn.pack(side="left", padx=5)

        export_btn = ctk.CTkButton(
            btn_frame,
            text="Export CSV",
            fg_color="gray50",
            command=self._export_csv
        )
        export_btn.pack(side="left", padx=5)

        # Category filter and search
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(filter_frame, text="Category:").pack(side="left", padx=(0, 5))

        categories = ["All"] + Material.get_categories()
        self.category_var = ctk.StringVar(value="All")
        self.category_filter = ctk.CTkComboBox(
            filter_frame,
            values=categories,
            variable=self.category_var,
            command=self._filter_materials,
            width=150
        )
        self.category_filter.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(filter_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_materials())
        search_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=self.search_var,
            placeholder_text="Search materials...",
            width=200
        )
        search_entry.pack(side="left")

        # Materials table
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True)

        # Table header
        header_frame = ctk.CTkFrame(table_frame, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x")

        headers = [
            ("Category", 100),
            ("Name", 250),
            ("Unit", 60),
            ("Cost", 80),
            ("Markup", 70),
            ("Supplier", 100),
            ("Actions", 120)
        ]

        for text, width in headers:
            ctk.CTkLabel(
                header_frame,
                text=text,
                width=width,
                font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=5, pady=8)

        # Scrollable content
        self.table_content = ctk.CTkScrollableFrame(table_frame)
        self.table_content.pack(fill="both", expand=True)

        # Price check section
        self._create_price_check_section()

    def _create_price_check_section(self):
        """Create the supplier price check section."""
        section = ctk.CTkFrame(self)
        section.pack(fill="x", pady=(15, 0))

        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            header,
            text="Check Supplier Prices",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 15))

        # URL input
        url_frame = ctk.CTkFrame(content, fg_color="transparent")
        url_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(url_frame, text="Product URL:").pack(side="left", padx=(0, 10))
        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Paste product URL from Home Depot, Lowe's, etc.",
            width=400
        )
        self.url_entry.pack(side="left", padx=(0, 10))

        check_btn = ctk.CTkButton(
            url_frame,
            text="Check Price",
            command=self._check_price_url
        )
        check_btn.pack(side="left")

        # Quick search links
        links_frame = ctk.CTkFrame(content, fg_color="transparent")
        links_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(links_frame, text="Quick Search:").pack(side="left", padx=(0, 10))

        suppliers = [
            ("Home Depot", "https://www.homedepot.com/s/{query}"),
            ("Lowe's", "https://www.lowes.com/search?searchTerm={query}"),
            ("Tractor Supply", "https://www.tractorsupply.com/tsc/search/{query}"),
            ("Walmart", "https://www.walmart.com/search?q={query}")
        ]

        for name, url_template in suppliers:
            btn = ctk.CTkButton(
                links_frame,
                text=name,
                width=100,
                height=28,
                fg_color="gray50",
                command=lambda u=url_template: self._open_supplier_search(u)
            )
            btn.pack(side="left", padx=3)

        # Price result display
        self.price_result_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.price_result_frame.pack(fill="x", pady=10)

    def _load_materials(self, materials=None):
        """Load materials into the table."""
        for widget in self.table_content.winfo_children():
            widget.destroy()

        if materials is None:
            materials = Material.get_all()

        if not materials:
            empty = ctk.CTkLabel(
                self.table_content,
                text="No materials found. Add items or import from CSV.",
                text_color="gray50"
            )
            empty.pack(pady=30)
            return

        for material in materials:
            self._create_material_row(material)

    def _create_material_row(self, material: Material):
        """Create a row for a material."""
        row = ctk.CTkFrame(self.table_content, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=material.category, width=100, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=material.name[:35], width=250, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=material.unit, width=60).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"${material.cost:.2f}", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"{(material.markup - 1) * 100:.0f}%", width=70).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=material.supplier[:12] if material.supplier else "-", width=100, anchor="w").pack(side="left", padx=5)

        # Action buttons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=120)
        btn_frame.pack(side="left", padx=5)

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            width=50,
            height=24,
            command=lambda m=material: self._edit_material(m)
        )
        edit_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            btn_frame,
            text="Del",
            width=50,
            height=24,
            fg_color="red",
            hover_color="darkred",
            command=lambda m=material: self._delete_material(m)
        )
        del_btn.pack(side="left", padx=2)

    def _filter_materials(self, *args):
        """Filter materials by category and search."""
        category = self.category_var.get()
        search = self.search_var.get().strip()

        if category == "All":
            if search:
                materials = Material.search(search)
            else:
                materials = Material.get_all()
        else:
            materials = Material.get_by_category(category)
            if search:
                search_lower = search.lower()
                materials = [m for m in materials if search_lower in m.name.lower()]

        self._load_materials(materials)

    def _add_material(self):
        """Add a new material."""
        dialog = MaterialEditDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            self._refresh_categories()
            self._load_materials()

    def _edit_material(self, material: Material):
        """Edit a material."""
        dialog = MaterialEditDialog(self, material=material)
        self.wait_window(dialog)

        if dialog.result:
            self._load_materials()

    def _delete_material(self, material: Material):
        """Delete a material."""
        if messagebox.askyesno("Confirm Delete", f"Delete '{material.name}'?"):
            material.delete()
            self._load_materials()

    def _refresh_categories(self):
        """Refresh category filter options."""
        categories = ["All"] + Material.get_categories()
        self.category_filter.configure(values=categories)

    def _import_csv(self):
        """Import materials from CSV."""
        file_path = filedialog.askopenfilename(
            title="Import Price List",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                count = Material.import_from_csv(file_path)
                messagebox.showinfo("Import Complete", f"Imported {count} materials.")
                self._refresh_categories()
                self._load_materials()
            except Exception as e:
                messagebox.showerror("Import Error", str(e))

    def _export_csv(self):
        """Export materials to CSV."""
        file_path = filedialog.asksaveasfilename(
            title="Export Price List",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                Material.export_to_csv(file_path)
                messagebox.showinfo("Export Complete", f"Price list exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def _check_price_url(self):
        """Check price from entered URL."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a product URL")
            return

        # Clear previous result
        for widget in self.price_result_frame.winfo_children():
            widget.destroy()

        loading = ctk.CTkLabel(
            self.price_result_frame,
            text="Checking price...",
            text_color="gray50"
        )
        loading.pack()

        # Fetch price in background
        self.after(100, lambda: self._fetch_price(url))

    def _fetch_price(self, url: str):
        """Fetch price from URL."""
        api = get_supplier_api()
        result = api.get_price_from_url(url)

        # Clear loading
        for widget in self.price_result_frame.winfo_children():
            widget.destroy()

        if result:
            self._show_price_result(result)
        else:
            error = ctk.CTkLabel(
                self.price_result_frame,
                text="Could not fetch price. The page may require JavaScript or the format is not supported.",
                text_color="orange"
            )
            error.pack()

    def _show_price_result(self, result: PriceResult):
        """Display price check result."""
        result_frame = ctk.CTkFrame(self.price_result_frame)
        result_frame.pack(fill="x", pady=5)

        info_frame = ctk.CTkFrame(result_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            info_frame,
            text=result.product_name,
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame,
            text=f"{result.supplier} - ${result.price:.2f}",
            text_color="green",
            anchor="w"
        ).pack(anchor="w")

        # Add to price list button
        add_btn = ctk.CTkButton(
            result_frame,
            text="Add to Price List",
            command=lambda r=result: self._add_from_result(r)
        )
        add_btn.pack(side="right", padx=10, pady=10)

    def _add_from_result(self, result: PriceResult):
        """Add a material from price check result."""
        material = Material(
            category="misc",
            name=result.product_name[:100],
            unit="each",
            cost=result.price,
            supplier=result.supplier,
            supplier_url=result.url
        )

        dialog = MaterialEditDialog(self, material=material)
        self.wait_window(dialog)

        if dialog.result:
            self._refresh_categories()
            self._load_materials()

    def _open_supplier_search(self, url_template: str):
        """Open supplier search in browser."""
        # Use selected material name or prompt
        search_term = ""
        if self.selected_material:
            search_term = self.selected_material.name

        if not search_term:
            dialog = ctk.CTkInputDialog(
                text="Enter product to search:",
                title="Supplier Search"
            )
            search_term = dialog.get_input()

        if search_term:
            url = url_template.format(query=search_term.replace(' ', '+'))
            webbrowser.open(url)


class MaterialEditDialog(ctk.CTkToplevel):
    """Dialog for editing a material."""

    def __init__(self, parent, material: Material = None):
        super().__init__(parent)
        self.material = material or Material()
        self.result: Optional[Material] = None

        self.title("Edit Material" if material and material.id else "New Material")
        self.geometry("450x400")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self._create_form()

    def _create_form(self):
        """Create the form."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Category
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        ctk.CTkLabel(row1, text="Category:", width=80).pack(side="left")
        categories = Material.get_categories() or ["gates", "operators", "hardware", "access_control", "electrical", "misc"]
        self.category_var = ctk.StringVar(value=self.material.category or "misc")
        self.category = ctk.CTkComboBox(
            row1,
            values=categories,
            variable=self.category_var,
            width=150
        )
        self.category.pack(side="left")

        # Name
        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text="Name*:", width=80).pack(side="left")
        self.name_entry = ctk.CTkEntry(row2, width=280)
        self.name_entry.insert(0, self.material.name or "")
        self.name_entry.pack(side="left")

        # Unit
        row3 = ctk.CTkFrame(frame, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        ctk.CTkLabel(row3, text="Unit:", width=80).pack(side="left")
        self.unit_entry = ctk.CTkEntry(row3, width=100)
        self.unit_entry.insert(0, self.material.unit or "each")
        self.unit_entry.pack(side="left")

        # Cost
        row4 = ctk.CTkFrame(frame, fg_color="transparent")
        row4.pack(fill="x", pady=5)

        ctk.CTkLabel(row4, text="Cost $:", width=80).pack(side="left")
        self.cost_entry = ctk.CTkEntry(row4, width=100)
        self.cost_entry.insert(0, f"{self.material.cost:.2f}")
        self.cost_entry.pack(side="left")

        # Markup
        row5 = ctk.CTkFrame(frame, fg_color="transparent")
        row5.pack(fill="x", pady=5)

        ctk.CTkLabel(row5, text="Markup %:", width=80).pack(side="left")
        self.markup_entry = ctk.CTkEntry(row5, width=100)
        markup_percent = (self.material.markup - 1) * 100
        self.markup_entry.insert(0, f"{markup_percent:.0f}")
        self.markup_entry.pack(side="left")

        # Supplier
        row6 = ctk.CTkFrame(frame, fg_color="transparent")
        row6.pack(fill="x", pady=5)

        ctk.CTkLabel(row6, text="Supplier:", width=80).pack(side="left")
        self.supplier_entry = ctk.CTkEntry(row6, width=280)
        self.supplier_entry.insert(0, self.material.supplier or "")
        self.supplier_entry.pack(side="left")

        # Supplier URL
        row7 = ctk.CTkFrame(frame, fg_color="transparent")
        row7.pack(fill="x", pady=5)

        ctk.CTkLabel(row7, text="URL:", width=80).pack(side="left")
        self.url_entry = ctk.CTkEntry(row7, width=280)
        self.url_entry.insert(0, self.material.supplier_url or "")
        self.url_entry.pack(side="left")

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
            text="Save",
            command=self._save
        ).pack(side="right")

    def _save(self):
        """Save the material."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return

        try:
            cost = float(self.cost_entry.get())
            markup_percent = float(self.markup_entry.get())
            markup = 1 + (markup_percent / 100)
        except ValueError:
            messagebox.showerror("Error", "Invalid cost or markup")
            return

        self.material.category = self.category_var.get()
        self.material.name = name
        self.material.unit = self.unit_entry.get().strip() or "each"
        self.material.cost = cost
        self.material.markup = markup
        self.material.supplier = self.supplier_entry.get().strip()
        self.material.supplier_url = self.url_entry.get().strip()

        self.material.save()
        self.result = self.material
        self.destroy()
