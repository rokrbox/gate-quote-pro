"""Customer model for Gate Quote Pro."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from .database import get_db


@dataclass
class Customer:
    """Customer data model."""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    notes: str = ""
    created_at: datetime = None

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address]
        if self.city or self.state or self.zip_code:
            city_state = f"{self.city}, {self.state} {self.zip_code}".strip()
            parts.append(city_state)
        return "\n".join(p for p in parts if p.strip())

    def save(self) -> int:
        """Save customer to database."""
        db = get_db()
        if self.id:
            # Update existing
            db.execute("""
                UPDATE customers SET
                    name = ?, email = ?, phone = ?, address = ?,
                    city = ?, state = ?, zip_code = ?, notes = ?
                WHERE id = ?
            """, (self.name, self.email, self.phone, self.address,
                  self.city, self.state, self.zip_code, self.notes, self.id))
        else:
            # Insert new
            cursor = db.execute("""
                INSERT INTO customers (name, email, phone, address, city, state, zip_code, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.name, self.email, self.phone, self.address,
                  self.city, self.state, self.zip_code, self.notes))
            self.id = cursor.lastrowid
        db.commit()
        return self.id

    def delete(self):
        """Delete customer from database."""
        if self.id:
            db = get_db()
            db.execute("DELETE FROM customers WHERE id = ?", (self.id,))
            db.commit()

    @classmethod
    def get_by_id(cls, customer_id: int) -> Optional['Customer']:
        """Get customer by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        if row:
            return cls._from_row(row)
        return None

    @classmethod
    def get_all(cls) -> List['Customer']:
        """Get all customers."""
        db = get_db()
        cursor = db.execute("SELECT * FROM customers ORDER BY name")
        return [cls._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def search(cls, query: str) -> List['Customer']:
        """Search customers by name, email, or phone."""
        db = get_db()
        search_term = f"%{query}%"
        cursor = db.execute("""
            SELECT * FROM customers
            WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
            ORDER BY name
        """, (search_term, search_term, search_term))
        return [cls._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def _from_row(cls, row) -> 'Customer':
        """Create Customer from database row."""
        return cls(
            id=row['id'],
            name=row['name'],
            email=row['email'] or "",
            phone=row['phone'] or "",
            address=row['address'] or "",
            city=row['city'] or "",
            state=row['state'] or "",
            zip_code=row['zip_code'] or "",
            notes=row['notes'] or "",
            created_at=row['created_at']
        )
