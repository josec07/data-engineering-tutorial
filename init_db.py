import sqlite3
import os
from datetime import datetime

# CONFIGURATION
DB_NAME = "type43.db"

def create_connection():
    """Connect to the SQLite database (or create it if it doesn't exist)."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        print(f"[SUCCESS] Connected to {DB_NAME}")
        return conn
    except sqlite3.Error as e:
        print(f"[ERROR] {e}")
    return conn

def init_schema(conn):
    """Create the Type43 Core Tables."""
    cursor = conn.cursor()
    
    # 1. RECEIPTS (The Paper Truth)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_filename TEXT,
        vendor_name TEXT,
        purchase_date TEXT,
        total_amount REAL,
        is_digitized INTEGER DEFAULT 0, -- 0=False, 1=True
        notes TEXT
    );
    """)

    # 2. INVENTORY (The Physical Truth)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        condition TEXT,
        quantity_on_hand INTEGER DEFAULT 1,
        original_receipt_id INTEGER,
        purchase_price REAL,
        date_acquired TEXT,
        FOREIGN KEY (original_receipt_id) REFERENCES receipts (id)
    );
    """)

    # 3. MARKET INTELLIGENCE (The Valuation Layer)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_valuations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inventory_id INTEGER,
        valuation_date TEXT,
        current_market_price REAL,
        source TEXT,
        FOREIGN KEY (inventory_id) REFERENCES inventory (id)
    );
    """)

    # 4. AUDIT LOG (The Leak Detector)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asset_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inventory_id INTEGER,
        movement_type TEXT,
        job_reference TEXT,
        movement_date TEXT,
        FOREIGN KEY (inventory_id) REFERENCES inventory (id)
    );
    """)
    
    print("[SUCCESS] Schema initialized.")

def seed_data(conn):
    """Add some dummy data to verify the links work."""
    cursor = conn.cursor()
    
    # Check if empty so we don't duplicate on re-runs
    cursor.execute("SELECT count(*) FROM inventory")
    if cursor.fetchone()[0] > 0:
        print("[INFO] Data already exists. Skipping seed.")
        return

    print("[INFO] Seeding dummy data...")
    
    # 1. Add a Receipt
    cursor.execute("""
        INSERT INTO receipts (vendor_name, purchase_date, total_amount, notes)
        VALUES ('Home Depot', '2023-05-12', 450.00, 'Lumber for Smith Job')
    """)
    receipt_id = cursor.lastrowid
    
    # 2. Add the Inventory (Linked to that receipt)
    cursor.execute("""
        INSERT INTO inventory (name, category, condition, quantity_on_hand, original_receipt_id, purchase_price)
        VALUES ('Plywood Sheet 4x8', 'Material', 'Good', 50, ?, 450.00)
    """, (receipt_id,))
    inv_id = cursor.lastrowid
    
    # 3. Add a Market Valuation (Inflation Logic)
    # Bought for 450, Worth 600 today
    cursor.execute("""
        INSERT INTO market_valuations (inventory_id, valuation_date, current_market_price, source)
        VALUES (?, ?, 600.00, 'Commodities Index')
    """, (inv_id, datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    print("[SUCCESS] Dummy data seeded. System is live.")

if __name__ == "__main__":
    # Removes old DB to start fresh (Optional - comment out if you want to keep data)
    # if os.path.exists(DB_NAME):
    #     os.remove(DB_NAME)

    connection = create_connection()
    if connection:
        init_schema(connection)
        seed_data(connection)
        connection.close()
        print(f"\n[DONE] Database created at: {os.path.abspath(DB_NAME)}")