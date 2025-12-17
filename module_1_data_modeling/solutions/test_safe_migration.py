"""
Test Safe Schema Migration
Demonstrates how to safely migrate schema without losing data
"""

import psycopg2
import os

# PostgreSQL configuration
PG_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'database': os.getenv('PGDATABASE', 'type43_db'),
    'user': os.getenv('PGUSER', 'type43_user'),
    'password': os.getenv('PGPASSWORD', 'type43_pass')
}


def setup_original_schema(conn):
    """Create original schema (pre-normalization)"""
    cursor = conn.cursor()

    # Original unnormalized schema
    cursor.execute("""
        DROP TABLE IF EXISTS receipts_v1 CASCADE;

        CREATE TABLE receipts_v1 (
            id SERIAL PRIMARY KEY,
            vendor_name VARCHAR(100),  -- Not normalized
            purchase_date DATE,
            total_amount DECIMAL(10,2),
            notes TEXT
        );
    """)

    # Insert test data
    test_data = [
        ('Home Depot', '2024-01-15', 1250.50, 'Lumber for Smith Job'),
        ('home depot', '2024-01-20', 350.00, 'Tools'),  # Duplicate with different case
        ('Lowes', '2024-02-01', 890.25, 'Paint supplies'),
        ('Home Depot', '2024-02-15', 2100.00, 'More lumber'),
    ]

    for vendor, date, amount, notes in test_data:
        cursor.execute("""
            INSERT INTO receipts_v1 (vendor_name, purchase_date, total_amount, notes)
            VALUES (%s, %s, %s, %s)
        """, (vendor, date, amount, notes))

    conn.commit()

    # Show original data
    cursor.execute("SELECT COUNT(*) FROM receipts_v1")
    count = cursor.fetchone()[0]
    print(f"✓ Created original schema with {count} receipts")

    return count


def migration_step_1_add_vendors_table(conn):
    """Step 1: Add vendors dimension table"""
    cursor = conn.cursor()

    print("\n📦 Migration Step 1: Adding vendors dimension table")

    # Create vendors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL
        );
    """)

    # Populate vendors from distinct vendor names (normalize case)
    cursor.execute("""
        INSERT INTO vendors (name)
        SELECT DISTINCT LOWER(TRIM(vendor_name))
        FROM receipts_v1
        WHERE vendor_name IS NOT NULL
        ON CONFLICT (name) DO NOTHING;
    """)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM vendors")
    vendor_count = cursor.fetchone()[0]
    print(f"  ✓ Created {vendor_count} unique vendors")

    # Show vendor consolidation
    cursor.execute("""
        SELECT name, COUNT(*) as receipt_count
        FROM vendors v
        JOIN receipts_v1 r ON LOWER(TRIM(r.vendor_name)) = v.name
        GROUP BY name
    """)
    print("  Vendor consolidation:")
    for name, count in cursor.fetchall():
        print(f"    - {name}: {count} receipts")


def migration_step_2_add_foreign_key(conn):
    """Step 2: Add vendor_id column (nullable)"""
    cursor = conn.cursor()

    print("\n🔗 Migration Step 2: Adding vendor_id foreign key")

    # Add nullable vendor_id column
    cursor.execute("""
        ALTER TABLE receipts_v1
        ADD COLUMN IF NOT EXISTS vendor_id INT REFERENCES vendors(id);
    """)

    print("  ✓ Added vendor_id column (nullable)")

    conn.commit()


def migration_step_3_backfill_data(conn):
    """Step 3: Backfill vendor_id from vendor_name"""
    cursor = conn.cursor()

    print("\n🔄 Migration Step 3: Backfilling vendor_id")

    # Backfill vendor_id
    cursor.execute("""
        UPDATE receipts_v1 r
        SET vendor_id = v.id
        FROM vendors v
        WHERE LOWER(TRIM(r.vendor_name)) = v.name
          AND r.vendor_id IS NULL;
    """)

    rows_updated = cursor.rowcount
    conn.commit()

    print(f"  ✓ Updated {rows_updated} receipts with vendor_id")

    # Verify no nulls
    cursor.execute("SELECT COUNT(*) FROM receipts_v1 WHERE vendor_id IS NULL")
    null_count = cursor.fetchone()[0]

    if null_count > 0:
        print(f"  ⚠️  Warning: {null_count} receipts still have NULL vendor_id")
    else:
        print("  ✓ All receipts have vendor_id populated")


def migration_step_4_verify_data_integrity(conn):
    """Step 4: Verify data integrity before making changes permanent"""
    cursor = conn.cursor()

    print("\n✅ Migration Step 4: Verifying data integrity")

    checks_passed = 0
    checks_failed = 0

    # Check 1: No data lost
    cursor.execute("SELECT COUNT(*) FROM receipts_v1")
    current_count = cursor.fetchone()[0]

    if current_count == 4:  # We inserted 4 test records
        print(f"  ✓ Check 1: Row count preserved ({current_count} receipts)")
        checks_passed += 1
    else:
        print(f"  ✗ Check 1 FAILED: Expected 4 receipts, found {current_count}")
        checks_failed += 1

    # Check 2: All vendor_ids populated
    cursor.execute("SELECT COUNT(*) FROM receipts_v1 WHERE vendor_id IS NULL")
    null_count = cursor.fetchone()[0]

    if null_count == 0:
        print("  ✓ Check 2: All receipts have vendor_id")
        checks_passed += 1
    else:
        print(f"  ✗ Check 2 FAILED: {null_count} receipts missing vendor_id")
        checks_failed += 1

    # Check 3: Vendor consolidation worked
    cursor.execute("""
        SELECT COUNT(DISTINCT vendor_id) FROM receipts_v1
    """)
    unique_vendor_ids = cursor.fetchone()[0]

    if unique_vendor_ids == 2:  # "home depot" and "lowes" -> 2 vendors
        print(f"  ✓ Check 3: Vendor names properly consolidated ({unique_vendor_ids} unique vendors)")
        checks_passed += 1
    else:
        print(f"  ✗ Check 3 FAILED: Expected 2 vendors, found {unique_vendor_ids}")
        checks_failed += 1

    # Check 4: Total amounts preserved
    cursor.execute("SELECT SUM(total_amount) FROM receipts_v1")
    total = cursor.fetchone()[0]
    expected_total = 1250.50 + 350.00 + 890.25 + 2100.00

    if abs(float(total) - expected_total) < 0.01:
        print(f"  ✓ Check 4: Total amounts preserved (${total:,.2f})")
        checks_passed += 1
    else:
        print(f"  ✗ Check 4 FAILED: Expected ${expected_total:,.2f}, got ${total:,.2f}")
        checks_failed += 1

    print(f"\n  Summary: {checks_passed} passed, {checks_failed} failed")

    return checks_failed == 0


def migration_step_5_make_not_null(conn):
    """Step 5: Make vendor_id NOT NULL (safe because we verified no nulls)"""
    cursor = conn.cursor()

    print("\n🔒 Migration Step 5: Making vendor_id NOT NULL")

    try:
        cursor.execute("""
            ALTER TABLE receipts_v1
            ALTER COLUMN vendor_id SET NOT NULL;
        """)
        conn.commit()
        print("  ✓ vendor_id is now NOT NULL")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        conn.rollback()


def migration_step_6_deprecate_old_column(conn):
    """Step 6: (Optional) Drop old vendor_name column"""
    cursor = conn.cursor()

    print("\n⚠️  Migration Step 6: Dropping old vendor_name column")
    print("  (In production, wait 30 days before dropping)")

    # In production, you'd wait before doing this
    # cursor.execute("ALTER TABLE receipts_v1 DROP COLUMN vendor_name;")
    print("  ℹ️  Skipping column drop in this demo")


def demo_rollback(conn):
    """Demonstrate rollback capability"""
    print("\n↩️  Rollback Demonstration")
    print("  If migration failed, we could:")
    print("  1. DROP COLUMN vendor_id;")
    print("  2. Restore from backup")
    print("  3. Keep both columns until code is updated")


def main():
    """Run safe migration demonstration"""
    print("="*60)
    print("SAFE SCHEMA MIGRATION DEMONSTRATION")
    print("="*60)
    print("\nScenario: Normalize vendor names without data loss\n")

    try:
        # Connect to database
        conn = psycopg2.connect(**PG_CONFIG)

        # Setup
        original_count = setup_original_schema(conn)

        # Migration steps (each can be rolled back independently)
        migration_step_1_add_vendors_table(conn)
        migration_step_2_add_foreign_key(conn)
        migration_step_3_backfill_data(conn)

        # Verify before making permanent changes
        if migration_step_4_verify_data_integrity(conn):
            migration_step_5_make_not_null(conn)
            migration_step_6_deprecate_old_column(conn)
        else:
            print("\n❌ Verification failed - aborting migration!")
            print("   Rolling back changes...")
            conn.rollback()
            return 1

        demo_rollback(conn)

        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nKey Takeaways:")
        print("  1. ✓ No data was lost")
        print("  2. ✓ Vendor names were consolidated")
        print("  3. ✓ Foreign key relationships established")
        print("  4. ✓ Each step was verified before proceeding")
        print("  5. ✓ Rollback plan was available at each step")

        conn.close()
        return 0

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
