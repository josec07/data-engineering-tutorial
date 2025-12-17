"""
Performance Benchmark: Normalized vs Denormalized Schema
Demonstrates performance impact of schema design at scale
"""

import psycopg2
import time
import os
from contextlib import contextmanager

# PostgreSQL configuration
PG_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'database': os.getenv('PGDATABASE', 'type43_db'),
    'user': os.getenv('PGUSER', 'type43_user'),
    'password': os.getenv('PGPASSWORD', 'type43_pass')
}


@contextmanager
def timer(description):
    """Context manager to time operations"""
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"  ⏱️  {description}: {elapsed:.3f}s")
    return elapsed


def benchmark_query_performance(conn):
    """Compare query performance: normalized vs denormalized"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("BENCHMARK 1: Query Performance")
    print("="*60)

    # Get record count
    cursor.execute("SELECT COUNT(*) FROM receipts")
    receipt_count = cursor.fetchone()[0]
    print(f"\nDataset: {receipt_count:,} receipts\n")

    # Query 1: Simple aggregation (normalized)
    print("Query 1: Total spending by vendor (Normalized)")
    with timer("  Normalized query"):
        cursor.execute("""
            SELECT v.name, SUM(r.total_amount) as total
            FROM receipts r
            JOIN vendors v ON r.vendor_id = v.id
            GROUP BY v.name
            ORDER BY total DESC
            LIMIT 10
        """)
        results_normalized = cursor.fetchall()

    # Show results
    print("\n  Top 3 vendors:")
    for vendor, total in results_normalized[:3]:
        print(f"    {vendor:25} ${float(total):>12,.2f}")

    # Query 2: Complex join with multiple tables
    print("\nQuery 2: Inventory with current market value (Multiple JOINs)")
    with timer("  Complex join query"):
        cursor.execute("""
            SELECT
                i.name,
                c.name as category,
                co.name as condition,
                i.purchase_price,
                mv.current_market_price,
                (mv.current_market_price - i.purchase_price) as gain
            FROM inventory i
            JOIN categories c ON i.category_id = c.id
            JOIN conditions co ON i.condition_id = co.id
            LEFT JOIN market_valuations mv ON mv.inventory_id = i.id
            WHERE mv.current_market_price IS NOT NULL
            ORDER BY gain DESC
            LIMIT 10
        """)
        results = cursor.fetchall()

    print(f"\n  Retrieved {len(results)} items with market data")

    # Query 3: Aggregation with date dimension
    print("\nQuery 3: Monthly spending trends (Date JOIN)")
    with timer("  Date dimension query"):
        cursor.execute("""
            SELECT
                d.year,
                d.month_name,
                COUNT(r.id) as receipt_count,
                SUM(r.total_amount) as total_spent
            FROM receipts r
            JOIN dim_date d ON r.purchase_date = d.full_date
            WHERE d.year >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year, d.month
            LIMIT 12
        """)
        results = cursor.fetchall()

    print(f"\n  Analyzed {len(results)} months of data")


def benchmark_insert_performance(conn):
    """Compare insert performance: normalized vs single table"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("BENCHMARK 2: Insert Performance")
    print("="*60)

    BATCH_SIZE = 10_000

    # Test 1: Normalized insert (with FK lookup)
    print(f"\nInserting {BATCH_SIZE:,} receipts (Normalized schema)")

    receipts_data = []
    for i in range(BATCH_SIZE):
        receipts_data.append((
            1,  # vendor_id (Home Depot)
            '2024-01-15',
            100.00 + i * 0.01,
            f'Test receipt {i}'
        ))

    with timer(f"  Insert {BATCH_SIZE:,} receipts"):
        cursor.executemany("""
            INSERT INTO receipts (vendor_id, purchase_date, total_amount, notes)
            VALUES (%s, %s, %s, %s)
        """, receipts_data)
        conn.commit()

    # Cleanup
    cursor.execute("DELETE FROM receipts WHERE notes LIKE 'Test receipt%'")
    conn.commit()

    # Test 2: Bulk insert with COPY (fastest method)
    print(f"\nBulk insert using COPY command")

    import io
    buffer = io.StringIO()
    for i in range(BATCH_SIZE):
        buffer.write(f"1\t2024-01-15\t{100.00 + i * 0.01}\tTest bulk {i}\n")
    buffer.seek(0)

    with timer(f"  COPY {BATCH_SIZE:,} receipts"):
        cursor.copy_from(
            buffer,
            'receipts',
            columns=('vendor_id', 'purchase_date', 'total_amount', 'notes')
        )
        conn.commit()

    # Cleanup
    cursor.execute("DELETE FROM receipts WHERE notes LIKE 'Test bulk%'")
    conn.commit()

    print("\n  💡 Tip: COPY is 5-10x faster than INSERT for bulk loads")


def benchmark_index_impact(conn):
    """Demonstrate index performance impact"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("BENCHMARK 3: Index Performance Impact")
    print("="*60)

    # Get current indexes
    cursor.execute("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'receipts'
    """)
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"\nCurrent indexes on receipts: {', '.join(indexes)}")

    # Query without specific date index
    print("\nQuery: Find receipts from last 30 days")

    with timer("  With existing indexes"):
        cursor.execute("""
            EXPLAIN ANALYZE
            SELECT COUNT(*), SUM(total_amount)
            FROM receipts
            WHERE purchase_date >= CURRENT_DATE - INTERVAL '30 days'
        """)
        plan = cursor.fetchall()

    # Show if index was used
    plan_text = '\n'.join([row[0] for row in plan])
    if 'Index Scan' in plan_text:
        print("  ✓ Index scan used")
    else:
        print("  ⚠️  Sequential scan (slower)")

    # Test aggregate performance
    print("\nAggregate query: Total by vendor")

    with timer("  GROUP BY with index"):
        cursor.execute("""
            SELECT vendor_id, COUNT(*), SUM(total_amount)
            FROM receipts
            GROUP BY vendor_id
        """)
        results = cursor.fetchall()

    print(f"  Grouped {len(results)} vendors")


def benchmark_migration_performance(conn):
    """Benchmark large-scale schema migration"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("BENCHMARK 4: Schema Migration at Scale")
    print("="*60)

    # Get current receipt count
    cursor.execute("SELECT COUNT(*) FROM receipts")
    receipt_count = cursor.fetchone()[0]

    print(f"\nSimulating migration on {receipt_count:,} receipts")

    # Simulation: Add new column
    print("\nTest 1: Adding a new column")

    # Drop if exists
    cursor.execute("""
        ALTER TABLE receipts DROP COLUMN IF EXISTS tax_amount CASCADE
    """)
    conn.commit()

    with timer("  ADD COLUMN (nullable)"):
        cursor.execute("""
            ALTER TABLE receipts
            ADD COLUMN tax_amount DECIMAL(10,2)
        """)
        conn.commit()

    print("  ✓ Column added (instant - no data rewrite)")

    # Backfill data
    print("\nTest 2: Backfilling data")

    with timer(f"  UPDATE {receipt_count:,} rows"):
        cursor.execute("""
            UPDATE receipts
            SET tax_amount = total_amount * 0.08
            WHERE tax_amount IS NULL
        """)
        conn.commit()

    # Add NOT NULL constraint
    print("\nTest 3: Adding NOT NULL constraint")

    with timer("  ALTER COLUMN SET NOT NULL"):
        cursor.execute("""
            ALTER TABLE receipts
            ALTER COLUMN tax_amount SET NOT NULL
        """)
        conn.commit()

    print("  ✓ Constraint added (validates all rows)")

    # Cleanup
    cursor.execute("ALTER TABLE receipts DROP COLUMN tax_amount")
    conn.commit()


def benchmark_denormalized_alternative(conn):
    """Compare performance: normalized vs denormalized views"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("BENCHMARK 5: Materialized View Performance")
    print("="*60)

    # Create materialized view (denormalized)
    print("\nCreating materialized view (denormalized data)...")

    cursor.execute("DROP MATERIALIZED VIEW IF EXISTS receipts_denorm CASCADE")

    with timer("  CREATE MATERIALIZED VIEW"):
        cursor.execute("""
            CREATE MATERIALIZED VIEW receipts_denorm AS
            SELECT
                r.id,
                r.purchase_date,
                v.name as vendor_name,
                r.total_amount,
                r.notes
            FROM receipts r
            JOIN vendors v ON r.vendor_id = v.id
        """)
        conn.commit()

    # Get row count
    cursor.execute("SELECT COUNT(*) FROM receipts_denorm")
    count = cursor.fetchone()[0]
    print(f"  ✓ Materialized view created with {count:,} rows")

    # Query performance comparison
    print("\nQuery: Total spending by vendor")

    print("\n  Option 1: Normalized (with JOIN)")
    with timer("    Normalized query"):
        cursor.execute("""
            SELECT v.name, SUM(r.total_amount)
            FROM receipts r
            JOIN vendors v ON r.vendor_id = v.id
            GROUP BY v.name
        """)
        cursor.fetchall()

    print("\n  Option 2: Materialized View (pre-joined)")
    with timer("    Materialized view query"):
        cursor.execute("""
            SELECT vendor_name, SUM(total_amount)
            FROM receipts_denorm
            GROUP BY vendor_name
        """)
        cursor.fetchall()

    print("\n  💡 Materialized views are faster but require refresh")

    # Show refresh cost
    print("\nRefreshing materialized view...")
    with timer("  REFRESH MATERIALIZED VIEW"):
        cursor.execute("REFRESH MATERIALIZED VIEW receipts_denorm")
        conn.commit()

    # Cleanup
    cursor.execute("DROP MATERIALIZED VIEW receipts_denorm")
    conn.commit()


def show_table_sizes(conn):
    """Show storage space used by each table"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("STORAGE ANALYSIS")
    print("="*60 + "\n")

    cursor.execute("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            pg_total_relation_size(schemaname||'.'||tablename) as bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY bytes DESC
    """)

    print(f"{'Table':<30} {'Size':>15}")
    print("-" * 50)
    for schema, table, size, bytes in cursor.fetchall():
        print(f"{table:<30} {size:>15}")


def main():
    """Run all benchmarks"""
    print("="*60)
    print("SCHEMA PERFORMANCE BENCHMARKS")
    print("="*60)

    try:
        conn = psycopg2.connect(**PG_CONFIG)

        # Run benchmarks
        benchmark_query_performance(conn)
        benchmark_insert_performance(conn)
        benchmark_index_impact(conn)
        benchmark_migration_performance(conn)
        benchmark_denormalized_alternative(conn)
        show_table_sizes(conn)

        print("\n" + "="*60)
        print("✅ BENCHMARKS COMPLETE")
        print("="*60)

        print("\n📊 Key Takeaways:")
        print("  1. Indexes dramatically improve query performance")
        print("  2. COPY is fastest for bulk inserts")
        print("  3. Materialized views trade refresh cost for query speed")
        print("  4. Schema migrations can be slow on large tables")
        print("  5. Normalized schemas are smaller but require joins")

        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
