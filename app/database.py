import sqlite3
from pathlib import Path


DB_PATH = Path("data/supermarket.db")


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row

    return connection


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    # Products / Inventory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            cost_price REAL NOT NULL,
            sell_price REAL NOT NULL,
            mrp REAL NOT NULL,
            quantity REAL DEFAULT 0,
            reorder_level REAL DEFAULT 0,
            gst_rate REAL NOT NULL,
            hsn_code TEXT
        )
    """)

    # Customers / Khata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            balance REAL DEFAULT 0
        )
    """)

    # Owner preferences / Memory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS owner_preferences (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Bills
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            subtotal REAL NOT NULL,
            gst_amount REAL NOT NULL,
            cgst_amount REAL DEFAULT 0,
            sgst_amount REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            payment_mode TEXT,
            payment_reference TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bill Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            gst_rate REAL NOT NULL,
            gst_amount REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    connection.commit()
    connection.close()

    print("Database initialized successfully.")


if __name__ == "__main__":
    init_database()