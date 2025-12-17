-- 1. THE PAPER TRUTH (Stream A)
-- Raw data from the scans. Proof of Purchase.
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    scan_filename VARCHAR(255),       -- Link to the image file (e.g., "REC_001.jpg")
    vendor_name VARCHAR(100),         -- Home Depot, Lowes, etc.
    purchase_date DATE,
    total_amount DECIMAL(10, 2),      -- The final number on the receipt
    is_digitized BOOLEAN DEFAULT FALSE, -- Have we extracted line items yet?
    notes TEXT
);

-- 2. THE PHYSICAL TRUTH (Stream B)
-- The actual items sitting in the shop.
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,       -- "DeWalt 20V Drill" or "Plywood Sheet"
    category VARCHAR(50),             -- Tool, Material, Vehicle, Consumable
    condition VARCHAR(50),            -- New, Good, Fair, Scrap
    quantity_on_hand INT DEFAULT 1,
    
    -- The "Loose Link" to Receipts
    -- If we find the receipt, we link it here. If not, it stays NULL.
    original_receipt_id INT REFERENCES receipts(id),
    
    purchase_price DECIMAL(10, 2),    -- What he paid (from Receipt or Estimate)
    date_acquired DATE                -- Best guess if receipt is missing
);

-- 3. THE INTELLIGENCE LAYER (The "Type43 Value")
-- This is where we store the "Market Price" to show inflation/equity.
CREATE TABLE market_valuations (
    id SERIAL PRIMARY KEY,
    inventory_id INT REFERENCES inventory(id),
    valuation_date DATE DEFAULT CURRENT_DATE,
    
    current_market_price DECIMAL(10, 2), -- What it costs to buy TODAY
    source VARCHAR(100),                 -- "Home Depot Website", "Commodity Futures", "eBay"
    
    -- Calculated Field: The "Hidden Equity"
    -- (Current Price - Purchase Price) = Value Created via Inflation
    inflation_delta DECIMAL(10, 2) GENERATED ALWAYS AS (current_market_price) STORED 
    -- Note: Simple DBs might not support GENERATED columns easily, 
    -- usually we calculate this in Python/Pandas.
);

-- 4. THE AUDIT LOG (The "Leak" Detector)
-- Tracking when items go missing or get assigned to a job.
CREATE TABLE asset_movements (
    id SERIAL PRIMARY KEY,
    inventory_id INT REFERENCES inventory(id),
    movement_type VARCHAR(50),        -- "Checked Out", "Lost", "Sold", "Scrapped"
    job_reference VARCHAR(100),       -- "Smith House Project"
    movement_date DATE DEFAULT CURRENT_DATE
);