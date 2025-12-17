-- EXERCISE: Current Schema (SQLite)
-- This is the starting point. Your task is to normalize this schema.

-- 1. THE PAPER TRUTH (Stream A)
CREATE TABLE receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_filename TEXT,
    vendor_name TEXT,                    -- ⚠️ PROBLEM: Not normalized!
    purchase_date TEXT,                  -- ⚠️ PROBLEM: Should be DATE type
    total_amount REAL,
    is_digitized INTEGER DEFAULT 0,
    notes TEXT
);

-- 2. THE PHYSICAL TRUTH (Stream B)
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,                       -- ⚠️ PROBLEM: Should be a dimension!
    condition TEXT,                      -- ⚠️ PROBLEM: Should be a dimension!
    quantity_on_hand INTEGER DEFAULT 1,
    original_receipt_id INTEGER,
    purchase_price REAL,
    date_acquired TEXT,                  -- ⚠️ PROBLEM: Should be DATE type
    FOREIGN KEY (original_receipt_id) REFERENCES receipts (id)
);

-- 3. THE INTELLIGENCE LAYER
CREATE TABLE market_valuations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id INTEGER,
    valuation_date TEXT,
    current_market_price REAL,
    source TEXT,
    FOREIGN KEY (inventory_id) REFERENCES inventory (id)
);

-- 4. THE AUDIT LOG
CREATE TABLE asset_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id INTEGER,
    movement_type TEXT,                  -- ⚠️ PROBLEM: Should be constrained!
    job_reference TEXT,
    movement_date TEXT,
    FOREIGN KEY (inventory_id) REFERENCES inventory (id)
);

-- YOUR TASKS:
-- 1. Create dimension tables for: vendors, categories, conditions
-- 2. Update fact tables to use foreign keys to dimensions
-- 3. Change TEXT dates to proper DATE/TIMESTAMP types
-- 4. Add appropriate indexes
-- 5. Add CHECK constraints for business rules
-- 6. Convert to PostgreSQL syntax (SERIAL instead of AUTOINCREMENT)
