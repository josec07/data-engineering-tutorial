# Module 1: Knowledge Check Answers

## Question 1: What's the difference between a fact and dimension table?

**Answer:**

**Fact Tables** contain quantitative, measurable data (metrics):
- Store business events and measurements
- Have foreign keys to dimension tables
- Contain numeric values (amounts, quantities, counts)
- Grow rapidly over time
- Examples: receipts (total_amount), asset_movements (quantity), sales transactions

**Dimension Tables** contain descriptive, contextual attributes:
- Describe the "who, what, where, when, why" of facts
- Have a primary key referenced by facts
- Contain text descriptions and categories
- Grow slowly over time
- Examples: vendors (name, type), categories (name, description), customers

**In Type43 Analytics:**
- **Fact**: `receipts` table (records purchase transactions)
- **Dimension**: `vendors` table (describes who we bought from)

---

## Question 2: When should you denormalize data?

**Answer:**

Denormalize when:

1. **Query Performance** is critical
   - Joining 10+ tables is too slow
   - Read-heavy workloads benefit from fewer joins
   - Example: Pre-join vendor name into receipts for dashboard queries

2. **Historical Tracking** is required
   - Need to preserve data as it was at a point in time
   - Example: Store product price at time of purchase, even if current price changes

3. **Simplicity** outweighs normalization benefits
   - Small lookup tables (<100 rows) don't need separate tables
   - Example: Receipt status ('pending', 'approved', 'rejected') can be VARCHAR

4. **Reporting and Analytics**
   - Data warehouses often denormalize for OLAP queries
   - Materialized views for dashboard performance
   - Example: `v_receipt_summary` view in our schema

**When NOT to denormalize:**
- OLTP systems (transactional workloads)
- Data changes frequently
- Data integrity is critical
- Storage costs are high

---

## Question 3: Why use a date dimension instead of just a DATE column?

**Answer:**

A date dimension provides:

1. **Pre-computed Calendar Attributes**
   - Day of week, month name, quarter
   - Fiscal year calculations
   - Holiday flags
   - No need to calculate these in every query

2. **Consistent Business Logic**
   - Fiscal year defined once (April 1 start)
   - Holiday definitions centralized
   - Weekend/weekday logic standardized

3. **Query Performance**
   - Pre-indexed attributes
   - Avoid date functions in WHERE clauses
   - Faster aggregations by quarter, fiscal year

4. **Better Reporting**
   ```sql
   -- Without date dimension (complex)
   SELECT
       EXTRACT(YEAR FROM purchase_date) as year,
       EXTRACT(QUARTER FROM purchase_date) as quarter,
       SUM(total_amount)
   FROM receipts
   GROUP BY EXTRACT(YEAR FROM purchase_date), EXTRACT(QUARTER FROM purchase_date);

   -- With date dimension (simple)
   SELECT
       d.year,
       d.quarter_name,
       SUM(r.total_amount)
   FROM receipts r
   JOIN dim_date d ON r.purchase_date = d.full_date
   GROUP BY d.year, d.quarter_name;
   ```

5. **Fiscal Period Support**
   - Many businesses don't follow calendar year
   - Easy year-over-year comparisons

---

## Question 4: What are the trade-offs of normalization?

**Answer:**

**Benefits of Normalization:**
- ✅ Reduces data redundancy (no duplicate vendor names)
- ✅ Ensures data integrity (vendor change updates once)
- ✅ Saves storage space
- ✅ Easier to update data consistently
- ✅ Prevents anomalies (update, insert, delete)

**Costs of Normalization:**
- ❌ More complex queries (requires JOINs)
- ❌ Slower query performance (join overhead)
- ❌ More tables to manage
- ❌ Harder to understand for non-technical users
- ❌ More complex application code

**The Decision:**

| Scenario | Normalized | Denormalized |
|----------|-----------|--------------|
| OLTP (transactional) | ✓ Preferred | ✗ |
| OLAP (analytics) | Sometimes | ✓ Preferred |
| Small datasets | Either | ✓ Simpler |
| Large datasets | ✓ Space savings | ❌ Wasteful |
| Frequent updates | ✓ Single point | ❌ Update many rows |
| Frequent reads | ❌ Join overhead | ✓ Fast queries |

**Best Practice:** Normalize your operational database (3NF), denormalize your data warehouse (star schema).

---

## Question 5: How do you decide on indexing strategy?

**Answer:**

**Index these columns:**

1. **Primary Keys** (automatic in most databases)
   ```sql
   CREATE TABLE receipts (
       id SERIAL PRIMARY KEY  -- Automatically indexed
   );
   ```

2. **Foreign Keys** (for JOIN performance)
   ```sql
   CREATE INDEX idx_inventory_receipt ON inventory(original_receipt_id);
   ```

3. **Columns in WHERE clauses**
   ```sql
   -- Query: SELECT * FROM receipts WHERE purchase_date > '2024-01-01'
   CREATE INDEX idx_receipts_date ON receipts(purchase_date);
   ```

4. **Columns in ORDER BY**
   ```sql
   -- Query: SELECT * FROM receipts ORDER BY total_amount DESC
   CREATE INDEX idx_receipts_amount ON receipts(total_amount);
   ```

5. **Columns in GROUP BY** (sometimes)
   ```sql
   CREATE INDEX idx_inventory_category ON inventory(category_id);
   ```

6. **Composite indexes for common filter combinations**
   ```sql
   -- Query: WHERE category_id = 1 AND condition_id = 2
   CREATE INDEX idx_inventory_cat_cond ON inventory(category_id, condition_id);
   ```

**Don't index:**
- Small tables (<1000 rows) - table scans are faster
- Columns with low cardinality (few distinct values)
  - ❌ `is_digitized` (only TRUE/FALSE)
  - ✓ `vendor_id` (many distinct vendors)
- Columns that are frequently updated (index maintenance overhead)
- Columns never used in queries

**Monitoring:**
```sql
-- PostgreSQL: Find unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%pkey%';
```

**Rule of Thumb:**
- Index columns in WHERE, JOIN, ORDER BY clauses
- Composite indexes: put most selective column first
- Don't over-index: Each index slows INSERT/UPDATE
- Monitor and remove unused indexes

---

## Bonus: Common Mistakes to Avoid

1. **Natural Keys as Primary Keys**
   - ❌ `PRIMARY KEY (vendor_name)` - what if vendor renames?
   - ✓ `PRIMARY KEY (id)` - use surrogate keys

2. **Missing Constraints**
   - Add CHECK constraints for business rules
   - Use NOT NULL where appropriate
   - Add UNIQUE constraints

3. **Wrong Data Types**
   - ❌ VARCHAR(255) for everything
   - ✓ Use INT, DECIMAL, DATE appropriately

4. **No Indexes on Foreign Keys**
   - Always index FK columns for JOIN performance

5. **Over-normalization**
   - Sometimes 3NF is too much
   - Star schema (denormalized) is fine for analytics
