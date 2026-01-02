"""Database connection manager for Gate Quote Pro."""
import sqlite3
import os
from pathlib import Path
from datetime import datetime


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in user's Application Support folder
            app_support = Path.home() / "Library" / "Application Support" / "GateQuotePro"
            app_support.mkdir(parents=True, exist_ok=True)
            db_path = str(app_support / "gatequote.db")

        self.db_path = db_path
        self.connection = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.connection.cursor()

        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER REFERENCES customers(id),
                quote_number TEXT UNIQUE,
                gate_type TEXT,
                gate_style TEXT,
                width REAL,
                height REAL,
                material TEXT,
                automation TEXT,
                access_control TEXT,
                ground_type TEXT,
                slope TEXT,
                power_distance REAL,
                removal_needed INTEGER DEFAULT 0,
                labor_hours REAL,
                labor_rate REAL,
                materials_cost REAL,
                markup_percent REAL DEFAULT 30,
                tax_rate REAL DEFAULT 0,
                subtotal REAL,
                tax_amount REAL,
                total REAL,
                status TEXT DEFAULT 'draft',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Quote line items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quote_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER REFERENCES quotes(id) ON DELETE CASCADE,
                category TEXT,
                description TEXT,
                quantity REAL,
                unit TEXT,
                unit_cost REAL,
                total_cost REAL
            )
        """)

        # Materials/Price list
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                name TEXT NOT NULL,
                unit TEXT,
                cost REAL,
                markup REAL DEFAULT 1.3,
                supplier TEXT,
                supplier_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Company settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.connection.commit()

        # Initialize default settings if not present
        self._init_default_settings()

    def _init_default_settings(self):
        """Initialize default settings."""
        defaults = {
            'company_name': 'Your Gate Company',
            'company_address': '',
            'company_phone': '',
            'company_email': '',
            'company_license': '',
            'labor_rate': '125.00',
            'tax_rate': '0.0',
            'markup_percent': '30',
            'quote_terms': 'Quote valid for 30 days. 50% deposit required to begin work. Balance due upon completion.',
            'quote_prefix': 'GQ'
        }

        cursor = self.connection.cursor()
        for key, value in defaults.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        self.connection.commit()

    def execute(self, query: str, params: tuple = None):
        """Execute a query and return cursor."""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def commit(self):
        """Commit transaction."""
        self.connection.commit()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

    def get_setting(self, key: str, default: str = None) -> str:
        """Get a setting value."""
        cursor = self.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        self.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.commit()

    def get_all_settings(self) -> dict:
        """Get all settings as a dictionary."""
        cursor = self.execute("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in cursor.fetchall()}


# Global database instance
_db_instance = None


def get_db() -> Database:
    """Get or create the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
