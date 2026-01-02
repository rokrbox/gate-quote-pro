"""Quote model for Gate Quote Pro."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .database import get_db
from .customer import Customer


@dataclass
class QuoteItem:
    """Individual line item in a quote."""
    id: Optional[int] = None
    quote_id: Optional[int] = None
    category: str = ""
    description: str = ""
    quantity: float = 1.0
    unit: str = "each"
    unit_cost: float = 0.0
    total_cost: float = 0.0

    def calculate_total(self):
        """Calculate total cost for this item."""
        self.total_cost = self.quantity * self.unit_cost


@dataclass
class Quote:
    """Quote data model."""
    id: Optional[int] = None
    customer_id: Optional[int] = None
    quote_number: str = ""

    # Gate specifications
    gate_type: str = "swing"  # swing, sliding, cantilever, bi-fold, pedestrian
    gate_style: str = "standard"  # basic, standard, ornamental, custom
    width: float = 12.0  # feet
    height: float = 6.0  # feet
    material: str = "steel"  # steel, aluminum, wrought_iron, wood, chain_link
    automation: str = "none"  # none, single_swing, dual_swing, slide
    access_control: str = "none"  # none, keypad, remote, intercom, full_system

    # Site conditions
    ground_type: str = "concrete"  # concrete, asphalt, gravel, dirt
    slope: str = "flat"  # flat, slight, moderate, steep
    power_distance: float = 0.0  # feet from power source
    removal_needed: bool = False

    # Costs
    labor_hours: float = 0.0
    labor_rate: float = 125.0
    materials_cost: float = 0.0
    markup_percent: float = 30.0
    tax_rate: float = 0.0
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0

    # Status
    status: str = "draft"  # draft, sent, accepted, declined
    notes: str = ""

    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None

    # Related objects
    customer: Optional[Customer] = None
    items: List[QuoteItem] = field(default_factory=list)

    def generate_quote_number(self) -> str:
        """Generate a unique quote number."""
        db = get_db()
        prefix = db.get_setting('quote_prefix', 'GQ')
        cursor = db.execute("SELECT MAX(id) as max_id FROM quotes")
        row = cursor.fetchone()
        next_id = (row['max_id'] or 0) + 1
        date_str = datetime.now().strftime('%Y%m')
        return f"{prefix}-{date_str}-{next_id:04d}"

    def calculate_totals(self):
        """Calculate all totals for the quote."""
        # Sum up materials
        self.materials_cost = sum(item.total_cost for item in self.items)

        # Calculate labor cost
        labor_cost = self.labor_hours * self.labor_rate

        # Apply markup to materials
        materials_with_markup = self.materials_cost * (1 + self.markup_percent / 100)

        # Subtotal
        self.subtotal = materials_with_markup + labor_cost

        # Tax
        self.tax_amount = self.subtotal * (self.tax_rate / 100)

        # Total
        self.total = self.subtotal + self.tax_amount

    def save(self) -> int:
        """Save quote to database."""
        db = get_db()

        if not self.quote_number:
            self.quote_number = self.generate_quote_number()

        self.calculate_totals()

        if self.id:
            # Update existing
            db.execute("""
                UPDATE quotes SET
                    customer_id = ?, quote_number = ?, gate_type = ?, gate_style = ?,
                    width = ?, height = ?, material = ?, automation = ?,
                    access_control = ?, ground_type = ?, slope = ?, power_distance = ?,
                    removal_needed = ?, labor_hours = ?, labor_rate = ?,
                    materials_cost = ?, markup_percent = ?, tax_rate = ?,
                    subtotal = ?, tax_amount = ?, total = ?, status = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (self.customer_id, self.quote_number, self.gate_type, self.gate_style,
                  self.width, self.height, self.material, self.automation,
                  self.access_control, self.ground_type, self.slope, self.power_distance,
                  1 if self.removal_needed else 0, self.labor_hours, self.labor_rate,
                  self.materials_cost, self.markup_percent, self.tax_rate,
                  self.subtotal, self.tax_amount, self.total, self.status, self.notes,
                  self.id))
        else:
            # Insert new
            cursor = db.execute("""
                INSERT INTO quotes (
                    customer_id, quote_number, gate_type, gate_style, width, height,
                    material, automation, access_control, ground_type, slope,
                    power_distance, removal_needed, labor_hours, labor_rate,
                    materials_cost, markup_percent, tax_rate, subtotal, tax_amount,
                    total, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.customer_id, self.quote_number, self.gate_type, self.gate_style,
                  self.width, self.height, self.material, self.automation,
                  self.access_control, self.ground_type, self.slope, self.power_distance,
                  1 if self.removal_needed else 0, self.labor_hours, self.labor_rate,
                  self.materials_cost, self.markup_percent, self.tax_rate,
                  self.subtotal, self.tax_amount, self.total, self.status, self.notes))
            self.id = cursor.lastrowid

        db.commit()

        # Save line items
        self._save_items()

        return self.id

    def _save_items(self):
        """Save quote line items."""
        if not self.id:
            return

        db = get_db()

        # Delete existing items
        db.execute("DELETE FROM quote_items WHERE quote_id = ?", (self.id,))

        # Insert new items
        for item in self.items:
            item.quote_id = self.id
            db.execute("""
                INSERT INTO quote_items (quote_id, category, description, quantity, unit, unit_cost, total_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item.quote_id, item.category, item.description, item.quantity,
                  item.unit, item.unit_cost, item.total_cost))

        db.commit()

    def delete(self):
        """Delete quote from database."""
        if self.id:
            db = get_db()
            db.execute("DELETE FROM quote_items WHERE quote_id = ?", (self.id,))
            db.execute("DELETE FROM quotes WHERE id = ?", (self.id,))
            db.commit()

    @classmethod
    def get_by_id(cls, quote_id: int) -> Optional['Quote']:
        """Get quote by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
        row = cursor.fetchone()
        if row:
            quote = cls._from_row(row)
            quote._load_items()
            quote._load_customer()
            return quote
        return None

    @classmethod
    def get_all(cls, status: str = None) -> List['Quote']:
        """Get all quotes, optionally filtered by status."""
        db = get_db()
        if status:
            cursor = db.execute(
                "SELECT * FROM quotes WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
        else:
            cursor = db.execute("SELECT * FROM quotes ORDER BY created_at DESC")

        quotes = []
        for row in cursor.fetchall():
            quote = cls._from_row(row)
            quote._load_customer()
            quotes.append(quote)
        return quotes

    @classmethod
    def get_by_customer(cls, customer_id: int) -> List['Quote']:
        """Get all quotes for a customer."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM quotes WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]

    def _load_items(self):
        """Load line items for this quote."""
        if not self.id:
            return

        db = get_db()
        cursor = db.execute(
            "SELECT * FROM quote_items WHERE quote_id = ?",
            (self.id,)
        )
        self.items = [
            QuoteItem(
                id=row['id'],
                quote_id=row['quote_id'],
                category=row['category'],
                description=row['description'],
                quantity=row['quantity'],
                unit=row['unit'],
                unit_cost=row['unit_cost'],
                total_cost=row['total_cost']
            )
            for row in cursor.fetchall()
        ]

    def _load_customer(self):
        """Load customer for this quote."""
        if self.customer_id:
            self.customer = Customer.get_by_id(self.customer_id)

    @classmethod
    def _from_row(cls, row) -> 'Quote':
        """Create Quote from database row."""
        return cls(
            id=row['id'],
            customer_id=row['customer_id'],
            quote_number=row['quote_number'],
            gate_type=row['gate_type'] or "swing",
            gate_style=row['gate_style'] or "standard",
            width=row['width'] or 12.0,
            height=row['height'] or 6.0,
            material=row['material'] or "steel",
            automation=row['automation'] or "none",
            access_control=row['access_control'] or "none",
            ground_type=row['ground_type'] or "concrete",
            slope=row['slope'] or "flat",
            power_distance=row['power_distance'] or 0.0,
            removal_needed=bool(row['removal_needed']),
            labor_hours=row['labor_hours'] or 0.0,
            labor_rate=row['labor_rate'] or 125.0,
            materials_cost=row['materials_cost'] or 0.0,
            markup_percent=row['markup_percent'] or 30.0,
            tax_rate=row['tax_rate'] or 0.0,
            subtotal=row['subtotal'] or 0.0,
            tax_amount=row['tax_amount'] or 0.0,
            total=row['total'] or 0.0,
            status=row['status'] or "draft",
            notes=row['notes'] or "",
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
