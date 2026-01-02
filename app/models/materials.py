"""Materials/Price list model for Gate Quote Pro."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json
from pathlib import Path
from .database import get_db


@dataclass
class Material:
    """Material/product data model."""
    id: Optional[int] = None
    category: str = ""
    name: str = ""
    unit: str = "each"
    cost: float = 0.0
    markup: float = 1.3
    supplier: str = ""
    supplier_url: str = ""
    last_updated: datetime = None

    @property
    def price_with_markup(self) -> float:
        """Get price with markup applied."""
        return self.cost * self.markup

    def save(self) -> int:
        """Save material to database."""
        db = get_db()
        if self.id:
            db.execute("""
                UPDATE materials SET
                    category = ?, name = ?, unit = ?, cost = ?,
                    markup = ?, supplier = ?, supplier_url = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (self.category, self.name, self.unit, self.cost,
                  self.markup, self.supplier, self.supplier_url, self.id))
        else:
            cursor = db.execute("""
                INSERT INTO materials (category, name, unit, cost, markup, supplier, supplier_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.category, self.name, self.unit, self.cost,
                  self.markup, self.supplier, self.supplier_url))
            self.id = cursor.lastrowid
        db.commit()
        return self.id

    def delete(self):
        """Delete material from database."""
        if self.id:
            db = get_db()
            db.execute("DELETE FROM materials WHERE id = ?", (self.id,))
            db.commit()

    @classmethod
    def get_by_id(cls, material_id: int) -> Optional['Material']:
        """Get material by ID."""
        db = get_db()
        cursor = db.execute("SELECT * FROM materials WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        if row:
            return cls._from_row(row)
        return None

    @classmethod
    def get_all(cls) -> List['Material']:
        """Get all materials."""
        db = get_db()
        cursor = db.execute("SELECT * FROM materials ORDER BY category, name")
        return [cls._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_by_category(cls, category: str) -> List['Material']:
        """Get materials by category."""
        db = get_db()
        cursor = db.execute(
            "SELECT * FROM materials WHERE category = ? ORDER BY name",
            (category,)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of unique categories."""
        db = get_db()
        cursor = db.execute("SELECT DISTINCT category FROM materials ORDER BY category")
        return [row['category'] for row in cursor.fetchall()]

    @classmethod
    def search(cls, query: str) -> List['Material']:
        """Search materials by name."""
        db = get_db()
        search_term = f"%{query}%"
        cursor = db.execute(
            "SELECT * FROM materials WHERE name LIKE ? ORDER BY category, name",
            (search_term,)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]

    @classmethod
    def load_defaults(cls, json_path: str = None):
        """Load default materials from JSON file."""
        if json_path is None:
            # Try to find the default prices file
            possible_paths = [
                Path(__file__).parent.parent.parent / "resources" / "default_prices.json",
                Path.home() / "GateQuotePro" / "resources" / "default_prices.json",
            ]
            for path in possible_paths:
                if path.exists():
                    json_path = str(path)
                    break

        if not json_path or not Path(json_path).exists():
            return

        with open(json_path, 'r') as f:
            data = json.load(f)

        db = get_db()

        # Check if we already have materials
        cursor = db.execute("SELECT COUNT(*) as count FROM materials")
        if cursor.fetchone()['count'] > 0:
            return  # Don't overwrite existing materials

        # Load materials from each category
        for category, items in data.items():
            for item in items:
                material = cls(
                    category=item.get('category', category),
                    name=item['name'],
                    unit=item.get('unit', 'each'),
                    cost=item['cost'],
                    markup=1.3
                )
                material.save()

    @classmethod
    def import_from_csv(cls, csv_path: str) -> int:
        """Import materials from CSV file. Returns count of imported items."""
        import csv
        count = 0
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                material = cls(
                    category=row.get('category', 'misc'),
                    name=row['name'],
                    unit=row.get('unit', 'each'),
                    cost=float(row.get('cost', 0)),
                    markup=float(row.get('markup', 1.3)),
                    supplier=row.get('supplier', ''),
                    supplier_url=row.get('supplier_url', '')
                )
                material.save()
                count += 1
        return count

    @classmethod
    def export_to_csv(cls, csv_path: str):
        """Export all materials to CSV file."""
        import csv
        materials = cls.get_all()
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'category', 'name', 'unit', 'cost', 'markup', 'supplier', 'supplier_url'
            ])
            writer.writeheader()
            for m in materials:
                writer.writerow({
                    'category': m.category,
                    'name': m.name,
                    'unit': m.unit,
                    'cost': m.cost,
                    'markup': m.markup,
                    'supplier': m.supplier,
                    'supplier_url': m.supplier_url
                })

    @classmethod
    def _from_row(cls, row) -> 'Material':
        """Create Material from database row."""
        return cls(
            id=row['id'],
            category=row['category'] or "",
            name=row['name'],
            unit=row['unit'] or "each",
            cost=row['cost'] or 0.0,
            markup=row['markup'] or 1.3,
            supplier=row['supplier'] or "",
            supplier_url=row['supplier_url'] or "",
            last_updated=row['last_updated']
        )
