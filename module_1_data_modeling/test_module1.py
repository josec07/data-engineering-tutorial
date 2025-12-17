"""
Test Module 1: Data Modeling Solutions
Tests schema creation, date dimension, and data operations
"""

import sqlite3
import psycopg2
import sys
import os
from pathlib import Path

# Test configuration
SQLITE_DB = "type43.db"
TEST_SCHEMA_FILE = "solutions/schema_v2_normalized.sql"
TEST_DATE_DIM_FILE = "solutions/date_dimension.sql"

# PostgreSQL configuration from environment or defaults
PG_HOST = os.getenv('PGHOST', 'localhost')
PG_PORT = os.getenv('PGPORT', '5432')
PG_USER = os.getenv('PGUSER', 'type43_user')
PG_PASSWORD = os.getenv('PGPASSWORD', 'type43_pass')
PG_DATABASE = os.getenv('PGDATABASE', 'type43_db')

def test_sqlite_exists():
    """Test if SQLite database exists with data"""
    print("\n" + "="*60)
    print("TEST 1: Checking SQLite Database (Optional)")
    print("="*60)

    if not Path(SQLITE_DB).exists():
        print(f"⚠ SQLite database not found: {SQLITE_DB}")
        print("   This is optional - skipping SQLite tests")
        return True  # Not a failure, just skipped

    try:
        conn = sqlite3.connect(SQLITE_DB)
    except sqlite3.OperationalError as e:
        print(f"⚠ Cannot open SQLite database: {e}")
        print("   Skipping SQLite tests")
        return True  # Not a failure
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = ['receipts', 'inventory', 'market_valuations', 'asset_movements']

    print(f"✓ SQLite database exists")
    print(f"  Tables found: {', '.join(tables)}")

    # Count records
    for table in expected_tables:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")

    conn.close()
    return True


def test_postgresql_connection():
    """Test PostgreSQL connection"""
    print("\n" + "="*60)
    print("TEST 2: PostgreSQL Connection")
    print("="*60)

    config = {
        'host': PG_HOST,
        'port': int(PG_PORT),
        'database': PG_DATABASE,
        'user': PG_USER,
        'password': PG_PASSWORD
    }

    try:
        print(f"\nConnecting to {config['host']}:{config['port']}...")
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version[:50]}...")
        print(f"  Database: {PG_DATABASE}")
        conn.close()
        return config
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\n❌ Could not connect to PostgreSQL")
        print("   Make sure PostgreSQL is running:")
        print("   - Local: brew services start postgresql")
        print("   - Docker: docker-compose up -d")
        return None


def test_schema_creation(pg_config):
    """Test normalized schema creation"""
    print("\n" + "="*60)
    print("TEST 3: Creating Normalized Schema")
    print("="*60)

    try:
        conn = psycopg2.connect(**pg_config)
        cursor = conn.cursor()

        # Drop existing tables
        print("Dropping existing tables...")
        cursor.execute("""
            DROP TABLE IF EXISTS asset_movements CASCADE;
            DROP TABLE IF EXISTS market_valuations CASCADE;
            DROP TABLE IF EXISTS inventory CASCADE;
            DROP TABLE IF EXISTS receipts CASCADE;
            DROP TABLE IF EXISTS movement_types CASCADE;
            DROP TABLE IF EXISTS conditions CASCADE;
            DROP TABLE IF EXISTS categories CASCADE;
            DROP TABLE IF EXISTS vendors CASCADE;
            DROP VIEW IF EXISTS v_inventory_value CASCADE;
            DROP VIEW IF EXISTS v_receipt_summary CASCADE;
            DROP VIEW IF EXISTS v_inflation_gains CASCADE;
        """)
        conn.commit()
        print("✓ Dropped existing tables")

        # Read and execute schema file
        print(f"\nExecuting schema from {TEST_SCHEMA_FILE}...")
        with open(TEST_SCHEMA_FILE, 'r') as f:
            schema_sql = f.read()

        cursor.execute(schema_sql)
        conn.commit()
        print("✓ Schema created successfully")

        # Verify tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        expected = ['vendors', 'categories', 'conditions', 'movement_types',
                   'receipts', 'inventory', 'market_valuations', 'asset_movements']

        print(f"\n  Tables created ({len(tables)}):")
        for table in tables:
            status = "✓" if table in expected else "?"
            print(f"    {status} {table}")

        # Verify views
        cursor.execute("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        views = [row[0] for row in cursor.fetchall()]
        print(f"\n  Views created ({len(views)}):")
        for view in views:
            print(f"    ✓ {view}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        return False


def test_data_insertion(pg_config):
    """Test inserting data into normalized schema"""
    print("\n" + "="*60)
    print("TEST 4: Data Insertion")
    print("="*60)

    try:
        conn = psycopg2.connect(**pg_config)
        cursor = conn.cursor()

        # Dimensions should already be seeded
        cursor.execute("SELECT COUNT(*) FROM vendors")
        vendor_count = cursor.fetchone()[0]
        print(f"✓ Vendors seeded: {vendor_count} records")

        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        print(f"✓ Categories seeded: {category_count} records")

        cursor.execute("SELECT COUNT(*) FROM conditions")
        condition_count = cursor.fetchone()[0]
        print(f"✓ Conditions seeded: {condition_count} records")

        # Insert test receipt
        print("\nInserting test data...")
        cursor.execute("""
            INSERT INTO receipts (vendor_id, purchase_date, total_amount, notes)
            VALUES (1, '2024-01-15', 1250.50, 'Test receipt for lumber')
            RETURNING id
        """)
        receipt_id = cursor.fetchone()[0]
        print(f"✓ Inserted receipt (ID: {receipt_id})")

        # Insert test inventory
        cursor.execute("""
            INSERT INTO inventory
            (name, category_id, condition_id, quantity_on_hand, original_receipt_id, purchase_price, date_acquired)
            VALUES ('2x4 Lumber 8ft', 2, 1, 100, %s, 1250.50, '2024-01-15')
            RETURNING id
        """, (receipt_id,))
        inventory_id = cursor.fetchone()[0]
        print(f"✓ Inserted inventory (ID: {inventory_id})")

        # Insert market valuation
        cursor.execute("""
            INSERT INTO market_valuations (inventory_id, valuation_date, current_market_price, source)
            VALUES (%s, '2024-06-15', 1500.00, 'Lumber Market Index')
        """, (inventory_id,))
        print(f"✓ Inserted market valuation")

        conn.commit()

        # Test joins with views
        print("\nTesting views...")
        cursor.execute("SELECT * FROM v_inventory_value LIMIT 1")
        result = cursor.fetchone()
        if result:
            print(f"✓ v_inventory_value: {result}")

        cursor.execute("SELECT * FROM v_inflation_gains LIMIT 1")
        result = cursor.fetchone()
        if result:
            print(f"✓ v_inflation_gains: Price gain = ${result[4]:.2f} ({result[5]}%)")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Data insertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_date_dimension(pg_config):
    """Test date dimension creation"""
    print("\n" + "="*60)
    print("TEST 5: Date Dimension")
    print("="*60)

    try:
        conn = psycopg2.connect(**pg_config)
        cursor = conn.cursor()

        # Drop existing
        print("Dropping existing date dimension...")
        cursor.execute("DROP TABLE IF EXISTS dim_date CASCADE")
        cursor.execute("DROP FUNCTION IF EXISTS populate_date_dimension CASCADE")
        conn.commit()

        # Read and execute date dimension file
        print(f"\nExecuting date dimension from {TEST_DATE_DIM_FILE}...")
        with open(TEST_DATE_DIM_FILE, 'r') as f:
            date_sql = f.read()

        # Execute in chunks (some statements need separate execution)
        statements = date_sql.split(';')
        for stmt in statements:
            if stmt.strip():
                cursor.execute(stmt)

        conn.commit()
        print("✓ Date dimension created")

        # Verify data
        cursor.execute("SELECT COUNT(*) FROM dim_date")
        count = cursor.fetchone()[0]
        print(f"✓ Date records: {count}")

        # Test queries
        cursor.execute("""
            SELECT year, COUNT(*) as days
            FROM dim_date
            GROUP BY year
            ORDER BY year
            LIMIT 3
        """)
        print("\n  Sample data:")
        for row in cursor.fetchall():
            print(f"    Year {row[0]}: {row[1]} days")

        # Test holiday query
        cursor.execute("""
            SELECT full_date, holiday_name
            FROM dim_date
            WHERE is_holiday = TRUE
            AND year = 2024
            ORDER BY full_date
            LIMIT 5
        """)
        print("\n  2024 Holidays:")
        for row in cursor.fetchall():
            print(f"    {row[0]}: {row[1]}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Date dimension failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constraints(pg_config):
    """Test that constraints are working"""
    print("\n" + "="*60)
    print("TEST 6: Testing Constraints")
    print("="*60)

    try:
        conn = psycopg2.connect(**pg_config)
        cursor = conn.cursor()

        # Test 1: Negative amount should fail
        print("\nTest 1: Negative amount (should fail)...")
        try:
            cursor.execute("""
                INSERT INTO receipts (vendor_id, purchase_date, total_amount)
                VALUES (1, '2024-01-01', -100.00)
            """)
            conn.commit()
            print("❌ Constraint not working - negative amount allowed!")
            return False
        except psycopg2.Error:
            conn.rollback()
            print("✓ Negative amount rejected (constraint working)")

        # Test 2: Future date should fail
        print("\nTest 2: Future date (should fail)...")
        try:
            cursor.execute("""
                INSERT INTO receipts (vendor_id, purchase_date, total_amount)
                VALUES (1, '2030-01-01', 100.00)
            """)
            conn.commit()
            print("❌ Constraint not working - future date allowed!")
            return False
        except psycopg2.Error:
            conn.rollback()
            print("✓ Future date rejected (constraint working)")

        # Test 3: Negative quantity should fail
        print("\nTest 3: Negative quantity (should fail)...")
        try:
            cursor.execute("""
                INSERT INTO inventory (name, category_id, condition_id, quantity_on_hand, purchase_price)
                VALUES ('Test Item', 1, 1, -5, 100.00)
            """)
            conn.commit()
            print("❌ Constraint not working - negative quantity allowed!")
            return False
        except psycopg2.Error:
            conn.rollback()
            print("✓ Negative quantity rejected (constraint working)")

        # Test 4: Foreign key constraint
        print("\nTest 4: Invalid foreign key (should fail)...")
        try:
            cursor.execute("""
                INSERT INTO receipts (vendor_id, purchase_date, total_amount)
                VALUES (99999, '2024-01-01', 100.00)
            """)
            conn.commit()
            print("❌ Foreign key constraint not working!")
            return False
        except psycopg2.Error:
            conn.rollback()
            print("✓ Invalid foreign key rejected (constraint working)")

        conn.close()
        print("\n✓ All constraints working correctly!")
        return True

    except Exception as e:
        print(f"❌ Constraint test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MODULE 1: DATA MODELING - TEST SUITE")
    print("="*60)

    results = {}

    # Test 1: SQLite
    results['sqlite'] = test_sqlite_exists()

    # Test 2: PostgreSQL connection
    pg_config = test_postgresql_connection()
    if not pg_config:
        print("\n" + "="*60)
        print("TESTS INCOMPLETE - PostgreSQL not available")
        print("="*60)
        return

    # Test 3: Schema creation
    results['schema'] = test_schema_creation(pg_config)

    # Test 4: Data insertion
    if results['schema']:
        results['data'] = test_data_insertion(pg_config)

    # Test 5: Date dimension
    results['date_dim'] = test_date_dimension(pg_config)

    # Test 6: Constraints
    if results['schema']:
        results['constraints'] = test_constraints(pg_config)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20} {status}")

    total = len(results)
    passed = sum(results.values())

    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All Module 1 tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
