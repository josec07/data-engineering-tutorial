# Module 1: Data Modeling - Quick Start

## One-Command Test (For Recruiters)

```bash
# Run all Module 1 tests in Docker
docker-compose up --build

# View results (tests run automatically)
```

That's it! The tests will:
1. ✓ Start PostgreSQL database
2. ✓ Create normalized schema
3. ✓ Populate date dimension
4. ✓ Insert test data
5. ✓ Validate constraints
6. ✓ Show test results

---

## What Gets Tested

### 1. Schema Normalization
- Creates dimension tables (vendors, categories, conditions)
- Creates fact tables (receipts, inventory, valuations)
- Establishes foreign key relationships
- Adds business rule constraints

### 2. Date Dimension
- Generates 10 years of calendar data (2020-2030)
- Calculates fiscal year periods
- Marks weekends and holidays
- Enables time-based analytics

### 3. Data Integrity
- Tests CHECK constraints (no negative amounts)
- Tests foreign key constraints
- Tests date validation (no future dates)
- Tests unique constraints

### 4. Views & Queries
- `v_inventory_value` - Current inventory valuation
- `v_receipt_summary` - Receipt aggregations
- `v_inflation_gains` - Price appreciation tracking

---

## Expected Output

```
============================================================
MODULE 1: DATA MODELING - TEST SUITE
============================================================

============================================================
TEST 1: Checking SQLite Database
============================================================
✓ SQLite database exists
  Tables found: receipts, inventory, market_valuations, asset_movements
  receipts: 1 records
  inventory: 1 records
  market_valuations: 1 records
  asset_movements: 0 records

============================================================
TEST 2: PostgreSQL Connection
============================================================
✓ Connected to PostgreSQL
  Version: PostgreSQL 15.x...
  Database: type43_db

============================================================
TEST 3: Creating Normalized Schema
============================================================
✓ Dropped existing tables
✓ Schema created successfully

  Tables created (8):
    ✓ asset_movements
    ✓ categories
    ✓ conditions
    ✓ inventory
    ✓ market_valuations
    ✓ movement_types
    ✓ receipts
    ✓ vendors

  Views created (3):
    ✓ v_inflation_gains
    ✓ v_inventory_value
    ✓ v_receipt_summary

============================================================
TEST 4: Data Insertion
============================================================
✓ Vendors seeded: 5 records
✓ Categories seeded: 4 records
✓ Conditions seeded: 5 records

Inserting test data...
✓ Inserted receipt (ID: 1)
✓ Inserted inventory (ID: 1)
✓ Inserted market valuation

Testing views...
✓ v_inventory_value: (1, '2x4 Lumber 8ft', 'Material', 'New', 100, 1250.50, 125050.00, ...)
✓ v_inflation_gains: Price gain = $249.50 (19.96%)

============================================================
TEST 5: Date Dimension
============================================================
✓ Date dimension created
✓ Date records: 4018

  Sample data:
    Year 2020: 366 days
    Year 2021: 365 days
    Year 2022: 365 days

  2024 Holidays:
    2024-01-01: New Year's Day
    2024-05-27: Memorial Day
    2024-07-04: Independence Day
    2024-09-02: Labor Day
    2024-11-28: Thanksgiving

============================================================
TEST 6: Testing Constraints
============================================================
✓ Negative amount rejected (constraint working)
✓ Future date rejected (constraint working)
✓ Negative quantity rejected (constraint working)
✓ Invalid foreign key rejected (constraint working)

✓ All constraints working correctly!

============================================================
TEST SUMMARY
============================================================
sqlite               ✓ PASSED
schema               ✓ PASSED
data                 ✓ PASSED
date_dim             ✓ PASSED
constraints          ✓ PASSED

============================================================
RESULTS: 5/5 tests passed
============================================================

🎉 All Module 1 tests passed!
```

---

## Manual Testing (Optional)

If you want to explore the database manually:

```bash
# Start just the database
docker-compose up -d postgres

# Connect with psql
docker-compose exec postgres psql -U type43_user -d type43_db

# Run queries
type43_db=# SELECT * FROM vendors;
type43_db=# SELECT * FROM v_inflation_gains;
type43_db=# \dt  -- List all tables
type43_db=# \dv  -- List all views
```

---

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove database volume (start fresh)
docker-compose down -v
```

---

## Learning Objectives Demonstrated

✅ **Normalization**: Separated vendors, categories, conditions into dimension tables
✅ **Referential Integrity**: Foreign keys enforce relationships
✅ **Data Types**: Appropriate types (DECIMAL for money, DATE for dates)
✅ **Constraints**: Business rules enforced at database level
✅ **Indexing**: Strategic indexes on FK columns and filters
✅ **Views**: Simplified complex queries for end users
✅ **Date Dimensions**: Pre-computed calendar attributes for analytics
✅ **Star Schema**: Fact tables surrounded by dimension tables

---

## Files Tested

- `solutions/schema_v2_normalized.sql` - Normalized PostgreSQL schema
- `solutions/date_dimension.sql` - Date dimension with 10 years of data
- `solutions/migrate.py` - SQLite to PostgreSQL migration script
- `solutions/knowledge_check.md` - Concept explanations

---

## Troubleshooting

**Port conflict:**
```bash
# Change port in docker-compose.yml
ports:
  - "5434:5432"  # Use different external port
```

**See logs:**
```bash
docker-compose logs -f test-runner
docker-compose logs -f postgres
```

**Rebuild:**
```bash
docker-compose build --no-cache
docker-compose up
```

---

## Next Steps

After Module 1 passes:
- Explore the schema in PostgreSQL
- Read the knowledge check answers
- Move to [Module 2: ETL Pipeline](../module_2_etl_pipeline/)
