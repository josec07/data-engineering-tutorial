"""
SOLUTION: Migration script from SQLite to PostgreSQL
Migrates Type43 data from SQLite to normalized PostgreSQL schema
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

# Configuration
SQLITE_DB = "type43.db"
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'type43_db',
    'user': 'type43_user',
    'password': 'type43_pass'
}


def get_or_create_dimension(cursor, table, name_column, name_value, cache):
    """
    Helper function to get or create dimension record
    Uses cache to avoid repeated database lookups
    """
    cache_key = f"{table}:{name_value}"

    if cache_key in cache:
        return cache[cache_key]

    # Look up in database
    cursor.execute(f"SELECT id FROM {table} WHERE {name_column} = %s", (name_value,))
    result = cursor.fetchone()

    if result:
        dim_id = result[0]
    else:
        # Create new dimension record
        cursor.execute(
            f"INSERT INTO {table} ({name_column}) VALUES (%s) RETURNING id",
            (name_value,)
        )
        dim_id = cursor.fetchone()[0]

    cache[cache_key] = dim_id
    return dim_id


def migrate_receipts(sqlite_conn, pg_conn):
    """Migrate receipts from SQLite to PostgreSQL"""
    print("Migrating receipts...")

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Dimension cache
    vendor_cache = {}

    # Fetch all receipts from SQLite
    sqlite_cursor.execute("SELECT * FROM receipts")
    receipts = sqlite_cursor.fetchall()

    migrated = 0
    for receipt in receipts:
        # receipt = (id, scan_filename, vendor_name, purchase_date, total_amount, is_digitized, notes)
        old_id, scan_filename, vendor_name, purchase_date, total_amount, is_digitized, notes = receipt

        # Get or create vendor
        vendor_id = get_or_create_dimension(
            pg_cursor, 'vendors', 'name', vendor_name, vendor_cache
        )

        # Insert receipt
        pg_cursor.execute("""
            INSERT INTO receipts
            (scan_filename, vendor_id, purchase_date, total_amount, is_digitized, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (scan_filename, vendor_id, purchase_date, total_amount, bool(is_digitized), notes))

        new_id = pg_cursor.fetchone()[0]
        migrated += 1

        # Store ID mapping for inventory migration
        vendor_cache[f"receipt_id_map:{old_id}"] = new_id

    pg_conn.commit()
    print(f"  ✓ Migrated {migrated} receipts")
    return vendor_cache  # Return cache with ID mappings


def migrate_inventory(sqlite_conn, pg_conn, id_cache):
    """Migrate inventory from SQLite to PostgreSQL"""
    print("Migrating inventory...")

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Dimension caches
    category_cache = {}
    condition_cache = {}

    # Fetch all inventory from SQLite
    sqlite_cursor.execute("SELECT * FROM inventory")
    items = sqlite_cursor.fetchall()

    migrated = 0
    for item in items:
        # item = (id, name, category, condition, quantity, receipt_id, purchase_price, date_acquired)
        old_id, name, category, condition, quantity, receipt_id, purchase_price, date_acquired = item

        # Get or create dimensions
        category_id = get_or_create_dimension(
            pg_cursor, 'categories', 'name', category or 'Tool', category_cache
        )

        condition_id = get_or_create_dimension(
            pg_cursor, 'conditions', 'name', condition or 'Good', condition_cache
        )

        # Map old receipt ID to new receipt ID
        new_receipt_id = id_cache.get(f"receipt_id_map:{receipt_id}") if receipt_id else None

        # Insert inventory
        pg_cursor.execute("""
            INSERT INTO inventory
            (name, category_id, condition_id, quantity_on_hand, original_receipt_id, purchase_price, date_acquired)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (name, category_id, condition_id, quantity, new_receipt_id, purchase_price, date_acquired))

        new_id = pg_cursor.fetchone()[0]
        migrated += 1

        # Store ID mapping for market valuations
        id_cache[f"inventory_id_map:{old_id}"] = new_id

    pg_conn.commit()
    print(f"  ✓ Migrated {migrated} inventory items")


def migrate_market_valuations(sqlite_conn, pg_conn, id_cache):
    """Migrate market valuations from SQLite to PostgreSQL"""
    print("Migrating market valuations...")

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Fetch all market valuations
    sqlite_cursor.execute("SELECT * FROM market_valuations")
    valuations = sqlite_cursor.fetchall()

    migrated = 0
    for valuation in valuations:
        # valuation = (id, inventory_id, valuation_date, current_market_price, source)
        old_id, inventory_id, valuation_date, current_market_price, source = valuation

        # Map old inventory ID to new
        new_inventory_id = id_cache.get(f"inventory_id_map:{inventory_id}")

        if not new_inventory_id:
            print(f"  ⚠ Skipping valuation for unknown inventory_id: {inventory_id}")
            continue

        # Insert valuation
        pg_cursor.execute("""
            INSERT INTO market_valuations
            (inventory_id, valuation_date, current_market_price, source)
            VALUES (%s, %s, %s, %s)
        """, (new_inventory_id, valuation_date, current_market_price, source))

        migrated += 1

    pg_conn.commit()
    print(f"  ✓ Migrated {migrated} market valuations")


def verify_migration(pg_conn):
    """Verify data was migrated correctly"""
    print("\nVerifying migration...")

    cursor = pg_conn.cursor()

    # Count records
    tables = ['receipts', 'inventory', 'market_valuations', 'vendors', 'categories', 'conditions']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    # Test a join query
    cursor.execute("""
        SELECT
            v.name as vendor,
            COUNT(r.id) as receipt_count,
            SUM(r.total_amount) as total_spent
        FROM receipts r
        JOIN vendors v ON r.vendor_id = v.id
        GROUP BY v.name
        ORDER BY total_spent DESC
        LIMIT 5
    """)

    print("\n  Top vendors by spending:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]} receipts, ${row[2]:,.2f}")


def main():
    """Main migration function"""
    print("=" * 50)
    print("Type43 Analytics: SQLite → PostgreSQL Migration")
    print("=" * 50)

    # Connect to databases
    print("\nConnecting to databases...")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        print(f"  ✓ Connected to SQLite: {SQLITE_DB}")
    except Exception as e:
        print(f"  ✗ Failed to connect to SQLite: {e}")
        return

    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        print(f"  ✓ Connected to PostgreSQL: {PG_CONFIG['database']}")
    except Exception as e:
        print(f"  ✗ Failed to connect to PostgreSQL: {e}")
        print(f"    Make sure PostgreSQL is running and schema is created")
        return

    try:
        # Start migration
        print("\nStarting migration...")

        # Migrate in order (respecting foreign keys)
        id_cache = migrate_receipts(sqlite_conn, pg_conn)
        migrate_inventory(sqlite_conn, pg_conn, id_cache)
        migrate_market_valuations(sqlite_conn, pg_conn, id_cache)

        # Verify
        verify_migration(pg_conn)

        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        pg_conn.rollback()
        raise

    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
