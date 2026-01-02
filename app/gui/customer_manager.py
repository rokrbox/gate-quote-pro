"""Customer management view for Gate Quote Pro."""
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

from ..models.customer import Customer


class CustomerManager(ctk.CTkFrame):
    """View for managing customers."""

    def __init__(self, parent, main_window=None):
        super().__init__(parent, fg_color="transparent")
        self.main_window = main_window
        self.selected_customer: Optional[Customer] = None

        self._create_layout()
        self._load_customers()

    def _create_layout(self):
        """Create the layout."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        title = ctk.CTkLabel(
            header,
            text="Customers",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left")

        add_btn = ctk.CTkButton(
            header,
            text="+ Add Customer",
            command=self._add_customer
        )
        add_btn.pack(side="right")

        # Search
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 15))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._search())

        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search customers...",
            width=300
        )
        search_entry.pack(side="left")

        # Two column layout
        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.pack(fill="both", expand=True)

        # Customer list
        list_frame = ctk.CTkFrame(columns)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        list_header = ctk.CTkLabel(
            list_frame,
            text="Customer List",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_header.pack(anchor="w", padx=15, pady=10)

        self.customer_list = ctk.CTkScrollableFrame(list_frame)
        self.customer_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Customer details
        self.detail_frame = ctk.CTkFrame(columns)
        self.detail_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        detail_header = ctk.CTkLabel(
            self.detail_frame,
            text="Customer Details",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        detail_header.pack(anchor="w", padx=15, pady=10)

        self.detail_content = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        self.detail_content.pack(fill="both", expand=True, padx=15, pady=10)

        self._show_empty_details()

    def _load_customers(self, customers=None):
        """Load customers into the list."""
        for widget in self.customer_list.winfo_children():
            widget.destroy()

        if customers is None:
            customers = Customer.get_all()

        if not customers:
            empty = ctk.CTkLabel(
                self.customer_list,
                text="No customers found",
                text_color="gray50"
            )
            empty.pack(pady=30)
            return

        for customer in customers:
            self._create_customer_row(customer)

    def _create_customer_row(self, customer: Customer):
        """Create a row for a customer."""
        row = ctk.CTkFrame(self.customer_list)
        row.pack(fill="x", pady=3)

        # Make clickable
        row.bind("<Button-1>", lambda e, c=customer: self._select_customer(c))

        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        info_frame.bind("<Button-1>", lambda e, c=customer: self._select_customer(c))

        name_label = ctk.CTkLabel(
            info_frame,
            text=customer.name,
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        name_label.bind("<Button-1>", lambda e, c=customer: self._select_customer(c))

        contact_parts = []
        if customer.phone:
            contact_parts.append(customer.phone)
        if customer.email:
            contact_parts.append(customer.email)

        if contact_parts:
            contact_label = ctk.CTkLabel(
                info_frame,
                text=" | ".join(contact_parts),
                text_color="gray50",
                anchor="w"
            )
            contact_label.pack(anchor="w")
            contact_label.bind("<Button-1>", lambda e, c=customer: self._select_customer(c))

    def _select_customer(self, customer: Customer):
        """Select a customer and show details."""
        self.selected_customer = customer
        self._show_customer_details(customer)

    def _show_empty_details(self):
        """Show empty state for details."""
        for widget in self.detail_content.winfo_children():
            widget.destroy()

        empty = ctk.CTkLabel(
            self.detail_content,
            text="Select a customer to view details",
            text_color="gray50"
        )
        empty.pack(pady=50)

    def _show_customer_details(self, customer: Customer):
        """Show customer details."""
        for widget in self.detail_content.winfo_children():
            widget.destroy()

        # Name
        name_label = ctk.CTkLabel(
            self.detail_content,
            text=customer.name,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        name_label.pack(anchor="w", pady=(0, 15))

        # Contact info
        if customer.email:
            email_row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
            email_row.pack(fill="x", pady=3)
            ctk.CTkLabel(email_row, text="Email:", width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(email_row, text=customer.email, anchor="w").pack(side="left")

        if customer.phone:
            phone_row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
            phone_row.pack(fill="x", pady=3)
            ctk.CTkLabel(phone_row, text="Phone:", width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(phone_row, text=customer.phone, anchor="w").pack(side="left")

        if customer.address:
            addr_row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
            addr_row.pack(fill="x", pady=3)
            ctk.CTkLabel(addr_row, text="Address:", width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(addr_row, text=customer.address, anchor="w").pack(side="left")

        if customer.city or customer.state:
            city_row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
            city_row.pack(fill="x", pady=3)
            ctk.CTkLabel(city_row, text="", width=80).pack(side="left")
            city_state = f"{customer.city}, {customer.state} {customer.zip_code}".strip()
            ctk.CTkLabel(city_row, text=city_state, anchor="w").pack(side="left")

        if customer.notes:
            notes_row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
            notes_row.pack(fill="x", pady=(15, 3))
            ctk.CTkLabel(notes_row, text="Notes:", anchor="w").pack(anchor="w")
            ctk.CTkLabel(notes_row, text=customer.notes, anchor="w", wraplength=300).pack(anchor="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(self.detail_content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)

        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            width=80,
            command=lambda: self._edit_customer(customer)
        )
        edit_btn.pack(side="left", padx=(0, 10))

        quote_btn = ctk.CTkButton(
            btn_frame,
            text="New Quote",
            width=100,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: self._new_quote_for_customer(customer)
        )
        quote_btn.pack(side="left", padx=(0, 10))

        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            width=80,
            fg_color="red",
            hover_color="darkred",
            command=lambda: self._delete_customer(customer)
        )
        delete_btn.pack(side="left")

        # Quote history
        from ..models.quote import Quote
        quotes = Quote.get_by_customer(customer.id)

        if quotes:
            history_label = ctk.CTkLabel(
                self.detail_content,
                text=f"Quote History ({len(quotes)})",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            history_label.pack(anchor="w", pady=(20, 10))

            for quote in quotes[:5]:  # Show last 5
                quote_row = ctk.CTkFrame(self.detail_content, fg_color="transparent")
                quote_row.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    quote_row,
                    text=f"{quote.quote_number} - ${quote.total:.2f} ({quote.status})"
                ).pack(side="left")

    def _search(self):
        """Search customers."""
        query = self.search_var.get().strip()
        if query:
            customers = Customer.search(query)
        else:
            customers = Customer.get_all()
        self._load_customers(customers)

    def _add_customer(self):
        """Add a new customer."""
        dialog = CustomerEditDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            self._load_customers()
            self._select_customer(dialog.result)

    def _edit_customer(self, customer: Customer):
        """Edit a customer."""
        dialog = CustomerEditDialog(self, customer=customer)
        self.wait_window(dialog)

        if dialog.result:
            self._load_customers()
            self._select_customer(dialog.result)

    def _delete_customer(self, customer: Customer):
        """Delete a customer."""
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {customer.name}?\n\nThis will NOT delete their quotes."
        ):
            customer.delete()
            self._load_customers()
            self._show_empty_details()

    def _new_quote_for_customer(self, customer: Customer):
        """Create a new quote for this customer."""
        from ..models.quote import Quote

        quote = Quote()
        quote.customer_id = customer.id
        quote.customer = customer

        if self.main_window:
            self.main_window.show_quote_form(quote=quote)


class CustomerEditDialog(ctk.CTkToplevel):
    """Dialog for editing a customer."""

    def __init__(self, parent, customer: Customer = None):
        super().__init__(parent)
        self.customer = customer or Customer()
        self.result: Optional[Customer] = None

        self.title("Edit Customer" if customer else "New Customer")
        self.geometry("450x500")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self._create_form()

    def _create_form(self):
        """Create the form."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        fields = [
            ("Name*:", "name", self.customer.name),
            ("Email:", "email", self.customer.email),
            ("Phone:", "phone", self.customer.phone),
            ("Address:", "address", self.customer.address),
            ("City:", "city", self.customer.city),
            ("State:", "state", self.customer.state),
            ("ZIP:", "zip_code", self.customer.zip_code),
        ]

        self.entries = {}

        for label_text, field_name, value in fields:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=5)

            ctk.CTkLabel(row, text=label_text, width=80).pack(side="left")
            entry = ctk.CTkEntry(row, width=280)
            entry.insert(0, value or "")
            entry.pack(side="left")
            self.entries[field_name] = entry

        # Notes
        notes_row = ctk.CTkFrame(frame, fg_color="transparent")
        notes_row.pack(fill="x", pady=5)

        ctk.CTkLabel(notes_row, text="Notes:", width=80).pack(side="left", anchor="n")
        self.notes_text = ctk.CTkTextbox(notes_row, width=280, height=80)
        self.notes_text.pack(side="left")
        if self.customer.notes:
            self.notes_text.insert("1.0", self.customer.notes)

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
        """Save the customer."""
        name = self.entries['name'].get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return

        self.customer.name = name
        self.customer.email = self.entries['email'].get().strip()
        self.customer.phone = self.entries['phone'].get().strip()
        self.customer.address = self.entries['address'].get().strip()
        self.customer.city = self.entries['city'].get().strip()
        self.customer.state = self.entries['state'].get().strip()
        self.customer.zip_code = self.entries['zip_code'].get().strip()
        self.customer.notes = self.notes_text.get("1.0", "end").strip()

        self.customer.save()
        self.result = self.customer
        self.destroy()
