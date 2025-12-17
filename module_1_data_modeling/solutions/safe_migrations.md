# Safe Schema Migrations - Protecting Historical Data

## The Problem

When modifying database schemas in production:
- **Risk**: Data loss, downtime, broken applications
- **Challenge**: Ensure zero data loss while evolving schema
- **Goal**: Backwards-compatible, reversible changes

---

## Best Practices for Safe Migrations

### 1. Database Migration Tools

Use versioned migration tools to track schema changes:

**Flyway** (Java-based):
```
migrations/
  V1__initial_schema.sql
  V2__add_vendor_email.sql
  V3__normalize_categories.sql
```

**Alembic** (Python-based):
```python
# alembic/versions/001_add_vendor_email.py
def upgrade():
    op.add_column('vendors',
        sa.Column('email', sa.String(100), nullable=True))

def downgrade():
    op.drop_column('vendors', 'email')
```

**Benefits**:
- Version control for schema
- Automatic rollback capability
- Audit trail of changes
- Team coordination

---

### 2. Backwards-Compatible Migrations

**Bad** (Breaking Change):
```sql
-- This BREAKS existing applications!
ALTER TABLE receipts DROP COLUMN vendor_name;
ALTER TABLE receipts ADD COLUMN vendor_id INT REFERENCES vendors(id);
```

**Good** (Backwards-Compatible):
```sql
-- Step 1: Add new column (nullable)
ALTER TABLE receipts ADD COLUMN vendor_id INT REFERENCES vendors(id);

-- Step 2: Backfill data
UPDATE receipts r
SET vendor_id = v.id
FROM vendors v
WHERE r.vendor_name = v.name;

-- Step 3: (Later deployment) Make non-nullable
ALTER TABLE receipts ALTER COLUMN vendor_id SET NOT NULL;

-- Step 4: (Even later) Drop old column
-- ALTER TABLE receipts DROP COLUMN vendor_name;
```

**Why This Works**:
1. Old code continues using `vendor_name`
2. New code uses `vendor_id`
3. Both columns exist during transition
4. Remove old column only after all code is updated

---

### 3. Zero-Downtime Column Additions

**Example**: Add `tax_amount` to receipts

```sql
-- Migration V5__add_tax_amount.sql

-- Step 1: Add column (nullable with default)
ALTER TABLE receipts
ADD COLUMN tax_amount DECIMAL(10,2) DEFAULT 0.00;

-- Step 2: Backfill historical data
UPDATE receipts
SET tax_amount = total_amount * 0.08  -- 8% tax rate
WHERE tax_amount IS NULL;

-- Step 3: Add NOT NULL constraint
ALTER TABLE receipts
ALTER COLUMN tax_amount SET NOT NULL;

-- Step 4: Remove default (for new inserts)
ALTER TABLE receipts
ALTER COLUMN tax_amount DROP DEFAULT;
```

**Result**:
- No data loss
- Historical data gets calculated tax
- New inserts require explicit tax_amount

---

### 4. Preserving Historical Data with Temporal Tables

**Problem**: Vendor changes address, but we need historical address for old receipts.

**Solution**: Temporal/History Tables

```sql
-- Current vendors table
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    address VARCHAR(200),
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT '9999-12-31'
);

-- History table (automatically populated)
CREATE TABLE vendors_history (
    id INT,
    name VARCHAR(100),
    address VARCHAR(200),
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    PRIMARY KEY (id, valid_from)
);

-- Trigger to maintain history
CREATE OR REPLACE FUNCTION maintain_vendor_history()
RETURNS TRIGGER AS $$
BEGIN
    -- Close out old record
    UPDATE vendors
    SET valid_to = CURRENT_TIMESTAMP
    WHERE id = NEW.id;

    -- Archive to history
    INSERT INTO vendors_history
    SELECT id, name, address, valid_from, valid_to
    FROM vendors
    WHERE id = NEW.id AND valid_to != '9999-12-31';

    -- Insert new current record
    INSERT INTO vendors (id, name, address)
    VALUES (NEW.id, NEW.name, NEW.address);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER vendor_history_trigger
BEFORE UPDATE ON vendors
FOR EACH ROW EXECUTE FUNCTION maintain_vendor_history();
```

**Query Historical State**:
```sql
-- What was vendor's address on 2023-05-15?
SELECT * FROM vendors_history
WHERE id = 5
  AND '2023-05-15' BETWEEN valid_from AND valid_to;
```

---

### 5. Slowly Changing Dimensions (SCD)

For data warehouse scenarios, use SCD patterns:

**Type 1** (Overwrite - No History):
```sql
UPDATE vendors SET address = 'New Address' WHERE id = 5;
-- Old address is lost
```

**Type 2** (Add New Row - Full History):
```sql
-- Close old record
UPDATE vendors SET is_current = FALSE, end_date = CURRENT_DATE
WHERE id = 5 AND is_current = TRUE;

-- Insert new record
INSERT INTO vendors (id, name, address, is_current, start_date)
VALUES (5, 'Home Depot', 'New Address', TRUE, CURRENT_DATE);
```

**Type 3** (Add Column for Previous Value):
```sql
ALTER TABLE vendors ADD COLUMN previous_address VARCHAR(200);

UPDATE vendors
SET previous_address = address,
    address = 'New Address'
WHERE id = 5;
```

---

### 6. Testing Migrations

**Always test migrations on production-like data**:

```python
# test_migration_v5.py
def test_add_tax_amount():
    # Setup: Create test data
    insert_receipts(count=1000)

    # Execute migration
    run_migration('V5__add_tax_amount.sql')

    # Verify
    conn = get_db()
    cursor = conn.cursor()

    # Check all rows have tax_amount
    cursor.execute("SELECT COUNT(*) FROM receipts WHERE tax_amount IS NULL")
    assert cursor.fetchone()[0] == 0

    # Check calculation is correct
    cursor.execute("""
        SELECT COUNT(*) FROM receipts
        WHERE ABS(tax_amount - (total_amount * 0.08)) > 0.01
    """)
    assert cursor.fetchone()[0] == 0
```

---

### 7. Backup Before Migration

**Always backup before schema changes**:

```bash
# Backup before migration
pg_dump type43_db > backup_before_v5_$(date +%Y%m%d_%H%M%S).sql

# Run migration
psql type43_db < migrations/V5__add_tax_amount.sql

# If failure, restore
# psql type43_db < backup_before_v5_20240115_143022.sql
```

---

### 8. Blue-Green Deployment

For critical changes, use blue-green deployment:

```
┌─────────────┐
│  Blue DB    │ ← Current production (old schema)
│  (v1.0)     │
└─────────────┘

┌─────────────┐
│  Green DB   │ ← New version (new schema)
│  (v2.0)     │
└─────────────┘

Steps:
1. Clone production to Green
2. Apply migrations to Green
3. Test thoroughly on Green
4. Switch traffic to Green
5. Keep Blue as rollback option
```

---

### 9. Migration Checklist

Before running any schema migration:

- [ ] Tested on development database
- [ ] Tested on staging with production-like data
- [ ] Backup created
- [ ] Rollback script prepared
- [ ] Downtime window communicated (if needed)
- [ ] Monitoring alerts configured
- [ ] Team on standby for rollback
- [ ] Migration is backwards-compatible
- [ ] Application code updated to handle both old and new schema

---

### 10. Example Migration Workflow

**Scenario**: Normalize vendor names

```sql
-- Migration 1: Add vendors table and vendor_id column
-- File: V10__add_vendors_table.sql

-- Create vendors dimension
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Add new column (nullable for now)
ALTER TABLE receipts ADD COLUMN vendor_id INT REFERENCES vendors(id);

-- Populate vendors from existing data
INSERT INTO vendors (name)
SELECT DISTINCT vendor_name FROM receipts WHERE vendor_name IS NOT NULL;

-- Backfill vendor_id
UPDATE receipts r
SET vendor_id = v.id
FROM vendors v
WHERE r.vendor_name = v.name;

-- Verification query
SELECT
    COUNT(*) as total_receipts,
    COUNT(vendor_id) as receipts_with_vendor_id,
    COUNT(vendor_name) as receipts_with_vendor_name
FROM receipts;
-- Should show: all receipts have both vendor_id and vendor_name
```

```sql
-- Migration 2 (1 week later): Make vendor_id required
-- File: V11__vendor_id_not_null.sql

-- Verify no nulls
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM receipts WHERE vendor_id IS NULL) THEN
        RAISE EXCEPTION 'Cannot make vendor_id NOT NULL: found % null values',
            (SELECT COUNT(*) FROM receipts WHERE vendor_id IS NULL);
    END IF;
END $$;

-- Make NOT NULL
ALTER TABLE receipts ALTER COLUMN vendor_id SET NOT NULL;
```

```sql
-- Migration 3 (1 month later): Remove old column
-- File: V12__drop_vendor_name.sql

-- Only after ALL application code is updated
ALTER TABLE receipts DROP COLUMN vendor_name;
```

---

## Summary

**Key Principles**:
1. **Never delete data** without backup
2. **Always add before removing** (additive changes)
3. **Test on production-like data** before deploying
4. **Use migration tools** for version control
5. **Keep rollback plan** ready
6. **Communicate** with team about schema changes

**For Type43 Analytics**:
- Use Alembic for Python-based migrations
- Maintain `vendors_history` table for address changes
- Test all migrations on copy of production data
- Never drop columns without 30-day deprecation period
