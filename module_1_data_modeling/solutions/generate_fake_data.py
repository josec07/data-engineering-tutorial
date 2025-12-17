"""
Generate Fake Data for Type43 Analytics
Creates realistic construction business data at scale
"""

import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker()

# PostgreSQL configuration
PG_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'database': os.getenv('PGDATABASE', 'type43_db'),
    'user': os.getenv('PGUSER', 'type43_user'),
    'password': os.getenv('PGPASSWORD', 'type43_pass')
}

# Realistic vendor names for construction
VENDORS = [
    'Home Depot', 'Lowes', 'Menards', 'Ace Hardware',
    'Harbor Freight Tools', 'Northern Tool',
    'Lumber Liquidators', 'Buildmart', '84 Lumber',
    'Fastenal', 'Grainger', 'McMaster-Carr',
    'Tractor Supply Co', 'True Value Hardware'
]

# Product categories with typical items
PRODUCTS = {
    'Tool': [
        ('DeWalt 20V Drill', 150, 200),
        ('Milwaukee Impact Driver', 180, 250),
        ('Makita Circular Saw', 200, 300),
        ('Bosch Jigsaw', 100, 150),
        ('Ryobi Angle Grinder', 60, 100),
        ('Craftsman Tool Set', 200, 400),
        ('Stanley Tape Measure', 15, 30),
        ('Klein Wire Stripper', 25, 40),
        ('Estwing Hammer', 30, 50),
        ('Irwin Pliers Set', 40, 70),
    ],
    'Material': [
        ('2x4 Lumber 8ft', 5, 12),
        ('2x6 Lumber 10ft', 10, 20),
        ('Plywood Sheet 4x8', 40, 80),
        ('Drywall Sheet', 12, 25),
        ('Concrete Mix 80lb', 8, 15),
        ('PVC Pipe 10ft', 15, 30),
        ('Copper Wire 100ft', 50, 100),
        ('Insulation Roll', 30, 60),
        ('Roofing Shingles', 80, 150),
        ('Vinyl Siding', 200, 400),
    ],
    'Consumable': [
        ('Paint Gallon', 25, 50),
        ('Wood Stain Quart', 15, 30),
        ('Primer Gallon', 20, 40),
        ('Caulk Tube', 5, 10),
        ('Wood Glue', 8, 15),
        ('Sandpaper Pack', 10, 20),
        ('Paint Brushes Set', 15, 30),
        ('Drop Cloth', 10, 20),
        ('Painter Tape', 8, 15),
        ('Paint Roller Set', 12, 25),
    ],
}

CONDITIONS = ['New', 'Good', 'Fair', 'Poor']
CONDITION_DEPRECIATION = {'New': 1.0, 'Good': 0.8, 'Fair': 0.5, 'Poor': 0.25}

# Job site references for asset movements
JOB_SITES = [
    'Smith Residence Remodel',
    'Johnson Office Building',
    'Downtown Apartment Complex',
    'Miller House Addition',
    'Wilson Commercial Renovation',
    'Brown Retail Store Fit-out',
    'Davis Warehouse Construction',
    'Garcia Restaurant Build',
    'Martinez School Expansion',
    'Rodriguez Medical Center',
]


def generate_receipts(conn, count=1000, start_date=None, end_date=None):
    """Generate fake receipt data"""
    cursor = conn.cursor()

    if not start_date:
        start_date = datetime.now() - timedelta(days=730)  # 2 years ago
    if not end_date:
        end_date = datetime.now()

    print(f"\n📄 Generating {count:,} receipts...")

    receipts_data = []
    for i in range(count):
        # Random vendor
        vendor_name = random.choice(VENDORS)

        # Random date in range
        time_delta = end_date - start_date
        random_days = random.randint(0, time_delta.days)
        purchase_date = start_date + timedelta(days=random_days)

        # Random total amount (typically $50-$5000 for construction supplies)
        total_amount = round(random.uniform(50, 5000), 2)

        # Sometimes add notes
        notes = fake.sentence() if random.random() > 0.7 else None

        receipts_data.append((vendor_name, purchase_date, total_amount, notes))

        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1:,} receipts...")

    # Bulk insert
    print(f"  Inserting {len(receipts_data):,} receipts into database...")
    cursor.executemany("""
        INSERT INTO receipts (vendor_id, purchase_date, total_amount, notes)
        SELECT v.id, %s, %s, %s
        FROM vendors v
        WHERE v.name = %s
    """, [(date, amt, note, vendor) for vendor, date, amt, note in receipts_data])

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM receipts")
    total = cursor.fetchone()[0]
    print(f"  ✓ Total receipts in database: {total:,}")


def generate_inventory(conn, count=5000):
    """Generate fake inventory data"""
    cursor = conn.cursor()

    print(f"\n📦 Generating {count:,} inventory items...")

    # Get receipt IDs to link some inventory to receipts
    cursor.execute("SELECT id FROM receipts ORDER BY RANDOM() LIMIT %s", (count,))
    receipt_ids = [row[0] for row in cursor.fetchall()]

    inventory_data = []
    for i in range(count):
        # Random category and product
        category = random.choice(list(PRODUCTS.keys()))
        product_name, min_price, max_price = random.choice(PRODUCTS[category])

        # Add variation to product name
        if random.random() > 0.5:
            product_name = f"{fake.company()} {product_name}"

        # Random condition
        condition = random.choice(CONDITIONS)

        # Quantity (most items 1-10, some bulk 10-100)
        if random.random() > 0.8:
            quantity = random.randint(10, 100)  # Bulk purchase
        else:
            quantity = random.randint(1, 10)

        # Purchase price
        purchase_price = round(random.uniform(min_price, max_price), 2)

        # Link to receipt (50% of the time)
        receipt_id = random.choice(receipt_ids) if random.random() > 0.5 else None

        # Acquisition date
        date_acquired = fake.date_between(start_date='-2y', end_date='today')

        inventory_data.append((
            product_name,
            category,
            condition,
            quantity,
            receipt_id,
            purchase_price,
            date_acquired
        ))

        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1:,} items...")

    # Bulk insert
    print(f"  Inserting {len(inventory_data):,} items into database...")
    cursor.executemany("""
        INSERT INTO inventory (
            name, category_id, condition_id, quantity_on_hand,
            original_receipt_id, purchase_price, date_acquired
        )
        SELECT
            %s,
            c.id,
            co.id,
            %s,
            %s,
            %s,
            %s
        FROM categories c, conditions co
        WHERE c.name = %s AND co.name = %s
    """, [(name, qty, receipt_id, price, date, cat, cond)
          for name, cat, cond, qty, receipt_id, price, date in inventory_data])

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM inventory")
    total = cursor.fetchone()[0]
    print(f"  ✓ Total inventory items: {total:,}")


def generate_market_valuations(conn, percentage=30):
    """Generate market valuations for a percentage of inventory"""
    cursor = conn.cursor()

    print(f"\n💰 Generating market valuations for {percentage}% of inventory...")

    # Get inventory items
    cursor.execute(f"""
        SELECT id, purchase_price
        FROM inventory
        ORDER BY RANDOM()
        LIMIT (SELECT COUNT(*) * {percentage} / 100 FROM inventory)
    """)

    items = cursor.fetchall()

    valuations_data = []
    for inventory_id, purchase_price in items:
        # Current market price (could be higher or lower than purchase)
        # Simulate inflation/deflation: -20% to +50%
        price_change = random.uniform(0.8, 1.5)
        current_market_price = round(float(purchase_price) * price_change, 2)

        # Valuation date (recent)
        valuation_date = fake.date_between(start_date='-30d', end_date='today')

        # Data source
        source = random.choice([
            'Home Depot Website',
            'Lowes Online',
            'eBay Marketplace',
            'Amazon',
            'Commodities Index',
            'Manual Appraisal',
        ])

        valuations_data.append((
            inventory_id,
            valuation_date,
            current_market_price,
            source
        ))

    # Bulk insert
    print(f"  Inserting {len(valuations_data):,} valuations...")
    cursor.executemany("""
        INSERT INTO market_valuations (
            inventory_id, valuation_date, current_market_price, source
        ) VALUES (%s, %s, %s, %s)
    """, valuations_data)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM market_valuations")
    total = cursor.fetchone()[0]
    print(f"  ✓ Total market valuations: {total:,}")


def generate_asset_movements(conn, percentage=20):
    """Generate asset movement records"""
    cursor = conn.cursor()

    print(f"\n🚚 Generating asset movements for {percentage}% of inventory...")

    # Get inventory items
    cursor.execute(f"""
        SELECT id
        FROM inventory
        WHERE quantity_on_hand > 0
        ORDER BY RANDOM()
        LIMIT (SELECT COUNT(*) * {percentage} / 100 FROM inventory WHERE quantity_on_hand > 0)
    """)

    items = [row[0] for row in cursor.fetchall()]

    # Get movement type IDs
    cursor.execute("SELECT id, name FROM movement_types")
    movement_types = cursor.fetchall()

    movements_data = []
    for inventory_id in items:
        # Random number of movements per item (1-3)
        num_movements = random.randint(1, 3)

        for _ in range(num_movements):
            movement_type_id = random.choice(movement_types)[0]
            job_reference = random.choice(JOB_SITES) if random.random() > 0.3 else None
            movement_date = fake.date_between(start_date='-1y', end_date='today')
            quantity = random.randint(1, 5)
            notes = fake.sentence() if random.random() > 0.8 else None

            movements_data.append((
                inventory_id,
                movement_type_id,
                job_reference,
                movement_date,
                quantity,
                notes
            ))

    # Bulk insert
    print(f"  Inserting {len(movements_data):,} movements...")
    cursor.executemany("""
        INSERT INTO asset_movements (
            inventory_id, movement_type_id, job_reference,
            movement_date, quantity, notes
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, movements_data)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM asset_movements")
    total = cursor.fetchone()[0]
    print(f"  ✓ Total asset movements: {total:,}")


def show_statistics(conn):
    """Display data statistics"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)

    # Table counts
    tables = ['receipts', 'inventory', 'market_valuations', 'asset_movements', 'vendors', 'categories']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:25} {count:>10,} records")

    # Total spending
    cursor.execute("SELECT SUM(total_amount) FROM receipts")
    total_spent = cursor.fetchone()[0] or 0
    print(f"\n{'Total Spent:':<25} ${float(total_spent):>12,.2f}")

    # Total inventory value
    cursor.execute("SELECT SUM(purchase_price * quantity_on_hand) FROM inventory")
    total_value = cursor.fetchone()[0] or 0
    print(f"{'Inventory Value:':<25} ${float(total_value):>12,.2f}")

    # Inflation gains
    cursor.execute("""
        SELECT SUM(current_market_price - i.purchase_price)
        FROM market_valuations mv
        JOIN inventory i ON mv.inventory_id = i.id
    """)
    inflation_gain = cursor.fetchone()[0] or 0
    print(f"{'Inflation Gains:':<25} ${float(inflation_gain):>12,.2f}")

    # Date range
    cursor.execute("SELECT MIN(purchase_date), MAX(purchase_date) FROM receipts")
    min_date, max_date = cursor.fetchone()
    if min_date and max_date:
        print(f"\n{'Date Range:':<25} {min_date} to {max_date}")

    # Top vendors
    print(f"\n{'Top 5 Vendors by Spending:':}")
    cursor.execute("""
        SELECT v.name, COUNT(r.id) as receipt_count, SUM(r.total_amount) as total
        FROM receipts r
        JOIN vendors v ON r.vendor_id = v.id
        GROUP BY v.name
        ORDER BY total DESC
        LIMIT 5
    """)
    for i, (vendor, count, total) in enumerate(cursor.fetchall(), 1):
        print(f"  {i}. {vendor:30} {count:>5} receipts  ${float(total):>10,.2f}")


def main():
    """Generate comprehensive fake data"""
    print("="*60)
    print("TYPE43 ANALYTICS - FAKE DATA GENERATOR")
    print("="*60)

    # Configuration
    RECEIPT_COUNT = 100_000   # 100k receipts
    INVENTORY_COUNT = 50_000  # 50k inventory items

    print("\nConfiguration:")
    print(f"  Receipts to generate: {RECEIPT_COUNT:,}")
    print(f"  Inventory items: {INVENTORY_COUNT:,}")
    print(f"  Market valuations: 30% of inventory")
    print(f"  Asset movements: 20% of inventory")

    try:
        # Connect
        print("\n📡 Connecting to database...")
        conn = psycopg2.connect(**PG_CONFIG)
        print("  ✓ Connected")

        # Generate data
        generate_receipts(conn, count=RECEIPT_COUNT)
        generate_inventory(conn, count=INVENTORY_COUNT)
        generate_market_valuations(conn, percentage=30)
        generate_asset_movements(conn, percentage=20)

        # Show stats
        show_statistics(conn)

        print("\n" + "="*60)
        print("✅ DATA GENERATION COMPLETE")
        print("="*60)

        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
