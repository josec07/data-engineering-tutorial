-- SOLUTION: Normalized Schema for Type43 Analytics
-- PostgreSQL syntax with proper normalization and referential integrity

-- ============================================
-- DIMENSION TABLES
-- ============================================

-- Vendors dimension
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    vendor_type VARCHAR(50),  -- 'Hardware', 'Lumber', 'Equipment', etc.
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for lookups
CREATE INDEX idx_vendors_name ON vendors(name);

-- Categories dimension
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 'Tool', 'Material', 'Vehicle', 'Consumable'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conditions dimension
CREATE TABLE conditions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 'New', 'Good', 'Fair', 'Poor', 'Scrap'
    depreciation_factor DECIMAL(3,2),  -- 1.00 for New, 0.75 for Good, etc.
    description TEXT
);

-- Movement types dimension
CREATE TABLE movement_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 'Checked Out', 'Lost', 'Sold', 'Scrapped'
    affects_inventory BOOLEAN DEFAULT TRUE,
    description TEXT
);

-- ============================================
-- FACT TABLES
-- ============================================

-- Receipts fact table
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    scan_filename VARCHAR(255),
    vendor_id INT NOT NULL REFERENCES vendors(id),
    purchase_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    is_digitized BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Business constraints
    CONSTRAINT positive_amount CHECK (total_amount > 0),
    CONSTRAINT valid_date CHECK (purchase_date <= CURRENT_DATE)
);

-- Indexes for common queries
CREATE INDEX idx_receipts_vendor ON receipts(vendor_id);
CREATE INDEX idx_receipts_date ON receipts(purchase_date);
CREATE INDEX idx_receipts_amount ON receipts(total_amount);

-- Inventory fact/dimension hybrid
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category_id INT NOT NULL REFERENCES categories(id),
    condition_id INT NOT NULL REFERENCES conditions(id),
    quantity_on_hand INT DEFAULT 1,
    original_receipt_id INT REFERENCES receipts(id),
    purchase_price DECIMAL(10, 2),
    date_acquired DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Business constraints
    CONSTRAINT valid_quantity CHECK (quantity_on_hand >= 0),
    CONSTRAINT positive_price CHECK (purchase_price >= 0)
);

-- Indexes
CREATE INDEX idx_inventory_category ON inventory(category_id);
CREATE INDEX idx_inventory_condition ON inventory(condition_id);
CREATE INDEX idx_inventory_receipt ON inventory(original_receipt_id);
CREATE INDEX idx_inventory_date ON inventory(date_acquired);

-- Composite index for common filter combinations
CREATE INDEX idx_inventory_cat_cond ON inventory(category_id, condition_id);

-- Market valuations fact table
CREATE TABLE market_valuations (
    id SERIAL PRIMARY KEY,
    inventory_id INT NOT NULL REFERENCES inventory(id),
    valuation_date DATE DEFAULT CURRENT_DATE,
    current_market_price DECIMAL(10, 2) NOT NULL,
    source VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Business constraints
    CONSTRAINT positive_market_price CHECK (current_market_price >= 0),

    -- Prevent duplicate valuations on same date
    UNIQUE(inventory_id, valuation_date)
);

-- Indexes
CREATE INDEX idx_market_inventory ON market_valuations(inventory_id);
CREATE INDEX idx_market_date ON market_valuations(valuation_date);

-- Asset movements fact table
CREATE TABLE asset_movements (
    id SERIAL PRIMARY KEY,
    inventory_id INT NOT NULL REFERENCES inventory(id),
    movement_type_id INT NOT NULL REFERENCES movement_types(id),
    job_reference VARCHAR(100),
    movement_date DATE DEFAULT CURRENT_DATE,
    quantity INT DEFAULT 1,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Business constraints
    CONSTRAINT valid_movement_date CHECK (movement_date <= CURRENT_DATE),
    CONSTRAINT positive_quantity CHECK (quantity > 0)
);

-- Indexes
CREATE INDEX idx_movements_inventory ON asset_movements(inventory_id);
CREATE INDEX idx_movements_date ON asset_movements(movement_date);
CREATE INDEX idx_movements_type ON asset_movements(movement_type_id);

-- ============================================
-- SEED DIMENSION DATA
-- ============================================

-- Seed vendors
INSERT INTO vendors (name, vendor_type) VALUES
    ('Home Depot', 'Hardware'),
    ('Lowes', 'Hardware'),
    ('Lumber Liquidators', 'Lumber'),
    ('Harbor Freight', 'Tools'),
    ('Menards', 'Hardware');

-- Seed categories
INSERT INTO categories (name, description) VALUES
    ('Tool', 'Hand tools, power tools, equipment'),
    ('Material', 'Lumber, concrete, fasteners'),
    ('Vehicle', 'Trucks, trailers, machinery'),
    ('Consumable', 'Paint, fuel, cleaning supplies');

-- Seed conditions
INSERT INTO conditions (name, depreciation_factor, description) VALUES
    ('New', 1.00, 'Brand new, unused'),
    ('Good', 0.80, 'Used but fully functional'),
    ('Fair', 0.50, 'Shows wear, still usable'),
    ('Poor', 0.25, 'Heavily worn, limited use'),
    ('Scrap', 0.00, 'Not usable, salvage only');

-- Seed movement types
INSERT INTO movement_types (name, affects_inventory, description) VALUES
    ('Checked Out', TRUE, 'Item checked out to job site'),
    ('Returned', FALSE, 'Item returned from job site'),
    ('Lost', TRUE, 'Item lost or stolen'),
    ('Sold', TRUE, 'Item sold'),
    ('Scrapped', TRUE, 'Item disposed of');

-- ============================================
-- USEFUL VIEWS
-- ============================================

-- Current inventory value view
CREATE VIEW v_inventory_value AS
SELECT
    i.id,
    i.name,
    c.name as category,
    co.name as condition,
    i.quantity_on_hand,
    i.purchase_price,
    (i.purchase_price * i.quantity_on_hand) as total_value,
    i.date_acquired
FROM inventory i
JOIN categories c ON i.category_id = c.id
JOIN conditions co ON i.condition_id = co.id
WHERE i.quantity_on_hand > 0;

-- Receipt summary view
CREATE VIEW v_receipt_summary AS
SELECT
    r.id,
    r.purchase_date,
    v.name as vendor_name,
    r.total_amount,
    COUNT(i.id) as item_count,
    SUM(i.quantity_on_hand) as total_items
FROM receipts r
JOIN vendors v ON r.vendor_id = v.id
LEFT JOIN inventory i ON i.original_receipt_id = r.id
GROUP BY r.id, r.purchase_date, v.name, r.total_amount;

-- Inflation gains view
CREATE VIEW v_inflation_gains AS
SELECT
    i.id as inventory_id,
    i.name as item_name,
    i.purchase_price,
    mv.current_market_price,
    (mv.current_market_price - i.purchase_price) as price_gain,
    ROUND(((mv.current_market_price - i.purchase_price) / NULLIF(i.purchase_price, 0) * 100), 2) as price_gain_pct,
    mv.valuation_date
FROM inventory i
JOIN market_valuations mv ON mv.inventory_id = i.id
WHERE mv.valuation_date = (
    SELECT MAX(valuation_date)
    FROM market_valuations mv2
    WHERE mv2.inventory_id = i.id
);

COMMENT ON VIEW v_inflation_gains IS 'Shows current market value vs purchase price for all items with recent valuations';
