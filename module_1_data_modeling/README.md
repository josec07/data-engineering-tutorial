# Module 1: Data Modeling Fundamentals

**Duration**: 2-3 hours
**Difficulty**: Beginner
**Prerequisites**: Basic SQL knowledge

## Learning Objectives

By the end of this module, you will:
- Understand dimensional modeling (star schema vs snowflake)
- Design fact and dimension tables
- Implement referential integrity
- Choose appropriate data types
- Normalize vs denormalize trade-offs
- Migrate from SQLite to PostgreSQL

---

## The Business Problem

A construction contractor needs to track:
1. **Receipts** - Paper proof of purchases from vendors
2. **Inventory** - Physical tools and materials on hand
3. **Market Valuations** - Current prices to track inflation gains
4. **Asset Movements** - Audit trail for lost/sold items

**Challenge**: How do we model this data efficiently for both transactional operations (OLTP) and analytics (OLAP)?

---

## Core Concepts

### 1. Fact vs Dimension Tables

**Fact Tables** (Measures/Metrics):
- Store quantitative data (amounts, quantities, counts)
- Foreign keys to dimension tables
- Examples: `receipts`, `asset_movements`

**Dimension Tables** (Context):
- Store descriptive attributes
- Primary keys referenced by facts
- Examples: `vendors`, `categories`, `conditions`

### 2. Schema Design Patterns

**Star Schema** (Our Approach):
```
         receipts (FACT)
              |
    +---------+---------+
    |         |         |
  vendors  inventory  dates
  (DIM)     (DIM)     (DIM)
```

**Benefits**:
- Simple to understand
- Fast query performance
- Easy to maintain

### 3. Normalization Levels

- **1NF**: No repeating groups (each cell has one value)
- **2NF**: No partial dependencies
- **3NF**: No transitive dependencies
- **Denormalization**: Intentionally adding redundancy for performance

---

## The Type43 Schema

### Current Schema (SQLite)

```sql
-- Fact Table: Receipts
receipts (
    id,
    vendor_name,           -- Should be normalized!
    purchase_date,
    total_amount,
    notes
)

-- Dimension/Fact Hybrid: Inventory
inventory (
    id,
    name,
    category,              -- Should be dimension!
    condition,             -- Should be dimension!
    quantity_on_hand,
    purchase_price,
    original_receipt_id    -- Foreign key (good!)
)

-- Fact Table: Market Valuations
market_valuations (
    id,
    inventory_id,          -- Foreign key (good!)
    valuation_date,
    current_market_price,
    source
)

-- Fact Table: Asset Movements
asset_movements (
    id,
    inventory_id,          -- Foreign key (good!)
    movement_type,
    job_reference,
    movement_date
)
```

### Problems with Current Design

1. **Vendor names not normalized** - "Home Depot" vs "home depot" vs "HomeDepot"
2. **Categories are strings** - Can't enforce valid values
3. **No date dimension** - Hard to do time-based analytics
4. **Missing indexes** - Slow queries on large datasets
5. **SQLite limitations** - No SERIAL, limited concurrency

---

## Exercise 1: Normalize the Schema

### Task

Refactor the schema to:
1. Create a `vendors` dimension table
2. Create a `categories` dimension table
3. Create a `conditions` dimension table
4. Add appropriate indexes
5. Convert to PostgreSQL syntax

### Starting Point

See [exercises/schema_v1.sql](./exercises/schema_v1.sql) for the current schema.

### Your Goal

Create `exercises/schema_v2_normalized.sql` with:
- Properly normalized dimensions
- Referential integrity constraints
- Appropriate indexes
- PostgreSQL data types

### Hints

```sql
-- Example: Vendors dimension
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    vendor_type VARCHAR(50),  -- Hardware, Lumber, Equipment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update receipts to reference vendors
ALTER TABLE receipts
    ADD COLUMN vendor_id INT REFERENCES vendors(id);
```

**Check your work**: [solutions/schema_v2_normalized.sql](./solutions/schema_v2_normalized.sql)

---

## Exercise 2: Add a Date Dimension

### Why Date Dimensions?

Date dimensions enable powerful time-based analytics:
- Fiscal year vs calendar year
- Weekday vs weekend analysis
- Holiday tracking
- Quarter-over-quarter comparisons

### Task

Create a `dim_date` table with:
- `date_key` (YYYYMMDD format, e.g., 20230512)
- `full_date` (actual date)
- `day_of_week`, `month`, `quarter`, `year`
- `is_weekend`, `is_holiday`
- Fiscal year fields

### Example Use Case

```sql
-- Total spending by quarter
SELECT
    d.fiscal_year,
    d.quarter,
    SUM(r.total_amount) as total_spent
FROM receipts r
JOIN dim_date d ON r.purchase_date = d.full_date
GROUP BY d.fiscal_year, d.quarter
ORDER BY d.fiscal_year, d.quarter;
```

**Check your work**: [solutions/date_dimension.sql](./solutions/date_dimension.sql)

---

## Exercise 3: Denormalization for Performance

### The Trade-off

Sometimes we intentionally denormalize for:
- Query performance (avoid joins)
- Simplicity
- Historical tracking

### Task

Create a `receipts_summary` materialized view:
```sql
CREATE MATERIALIZED VIEW receipts_summary AS
SELECT
    r.id,
    r.purchase_date,
    v.name as vendor_name,
    r.total_amount,
    COUNT(i.id) as items_count,
    SUM(i.quantity_on_hand) as total_items
FROM receipts r
LEFT JOIN vendors v ON r.vendor_id = v.id
LEFT JOIN inventory i ON i.original_receipt_id = r.id
GROUP BY r.id, r.purchase_date, v.name, r.total_amount;
```

**Question**: When would you refresh this materialized view?

**Check your work**: [solutions/materialized_views.sql](./solutions/materialized_views.sql)

---

## Exercise 4: Add Data Constraints

### Task

Add business logic constraints:
- Receipt amounts must be positive
- Quantities cannot be negative
- Purchase price cannot be negative
- Dates cannot be in the future

### Example

```sql
ALTER TABLE receipts
    ADD CONSTRAINT positive_amount
    CHECK (total_amount > 0);

ALTER TABLE inventory
    ADD CONSTRAINT valid_quantity
    CHECK (quantity_on_hand >= 0);
```

**Check your work**: [solutions/constraints.sql](./solutions/constraints.sql)

---

## Exercise 5: Migration Script

### Task

Write a Python script to migrate data from SQLite to PostgreSQL:

1. Export existing SQLite data
2. Transform vendor names to vendor dimension
3. Transform categories to category dimension
4. Insert into PostgreSQL with proper foreign keys

**Starter code**: [exercises/migrate.py](./exercises/migrate.py)
**Solution**: [solutions/migrate.py](./solutions/migrate.py)

---

## Performance Considerations

### Indexing Strategy

```sql
-- Index foreign keys
CREATE INDEX idx_inventory_receipt ON inventory(original_receipt_id);
CREATE INDEX idx_market_inventory ON market_valuations(inventory_id);

-- Index date columns for time-based queries
CREATE INDEX idx_receipts_date ON receipts(purchase_date);

-- Composite index for common queries
CREATE INDEX idx_inventory_category_condition
    ON inventory(category_id, condition_id);
```

### Query Optimization

**Before** (slow):
```sql
SELECT * FROM inventory WHERE category = 'Tool';
```

**After** (fast):
```sql
-- With proper indexing and normalized categories
SELECT i.*
FROM inventory i
JOIN categories c ON i.category_id = c.id
WHERE c.name = 'Tool';
```

---

## Real-World Examples

### E-commerce Schema
- Orders (fact) → Customers, Products, Dates (dimensions)

### Financial Transactions
- Transactions (fact) → Accounts, Merchants, Time (dimensions)

### IoT Sensor Data
- Readings (fact) → Sensors, Locations, Time (dimensions)

---

## Knowledge Check

1. **What's the difference between a fact and dimension table?**
2. **When should you denormalize data?**
3. **Why use a date dimension instead of just a DATE column?**
4. **What are the trade-offs of normalization?**
5. **How do you decide on indexing strategy?**

**Answers**: [solutions/knowledge_check.md](./solutions/knowledge_check.md)

---

## Going Further

### Advanced Topics
- Slowly Changing Dimensions (SCD Type 1, 2, 3)
- Bridge tables for many-to-many relationships
- Surrogate keys vs natural keys
- Temporal tables for historical tracking

### Recommended Reading
- "The Data Warehouse Toolkit" by Ralph Kimball
- [PostgreSQL Documentation: Data Modeling](https://www.postgresql.org/docs/current/ddl.html)

---

## Next Steps

Once you've completed the exercises:
1. Review the solutions
2. Test your schema with sample data
3. Run performance benchmarks
4. Proceed to [Module 2: ETL Pipeline →](../module_2_etl_pipeline/)

---

**Questions?** Open an issue or discussion on GitHub!
