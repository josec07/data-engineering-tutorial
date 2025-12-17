-- SOLUTION: Date Dimension Table
-- Generates a complete date dimension for analytics

CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,              -- YYYYMMDD format: 20230512
    full_date DATE NOT NULL UNIQUE,

    -- Day attributes
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,              -- 0=Sunday, 6=Saturday
    day_of_week_name VARCHAR(10) NOT NULL, -- 'Monday', 'Tuesday', etc.
    day_of_week_abbr CHAR(3) NOT NULL,     -- 'Mon', 'Tue', etc.
    day_of_year INT NOT NULL,

    -- Week attributes
    week_of_year INT NOT NULL,
    iso_week INT NOT NULL,

    -- Month attributes
    month INT NOT NULL,
    month_name VARCHAR(10) NOT NULL,       -- 'January', 'February', etc.
    month_abbr CHAR(3) NOT NULL,           -- 'Jan', 'Feb', etc.

    -- Quarter attributes
    quarter INT NOT NULL,                   -- 1, 2, 3, 4
    quarter_name VARCHAR(2) NOT NULL,       -- 'Q1', 'Q2', etc.

    -- Year attributes
    year INT NOT NULL,

    -- Fiscal year (assuming April 1 start)
    fiscal_year INT NOT NULL,
    fiscal_quarter INT NOT NULL,
    fiscal_month INT NOT NULL,

    -- Boolean flags
    is_weekend BOOLEAN NOT NULL,
    is_weekday BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    is_business_day BOOLEAN NOT NULL,

    -- Holiday name (if applicable)
    holiday_name VARCHAR(50),

    -- Relative date descriptions
    relative_description VARCHAR(20)       -- 'Today', 'Yesterday', 'Last Week', etc.
);

-- Indexes for common queries
CREATE INDEX idx_dim_date_full ON dim_date(full_date);
CREATE INDEX idx_dim_date_year_month ON dim_date(year, month);
CREATE INDEX idx_dim_date_year_quarter ON dim_date(year, quarter);
CREATE INDEX idx_dim_date_fiscal ON dim_date(fiscal_year, fiscal_quarter);
CREATE INDEX idx_dim_date_weekend ON dim_date(is_weekend);

-- Function to populate date dimension
CREATE OR REPLACE FUNCTION populate_date_dimension(start_date DATE, end_date DATE)
RETURNS void AS $$
DECLARE
    current_date DATE := start_date;
    dow INT;
    is_wknd BOOLEAN;
    fiscal_yr INT;
BEGIN
    WHILE current_date <= end_date LOOP
        dow := EXTRACT(DOW FROM current_date);
        is_wknd := (dow = 0 OR dow = 6);

        -- Calculate fiscal year (April 1 start)
        IF EXTRACT(MONTH FROM current_date) >= 4 THEN
            fiscal_yr := EXTRACT(YEAR FROM current_date);
        ELSE
            fiscal_yr := EXTRACT(YEAR FROM current_date) - 1;
        END IF;

        INSERT INTO dim_date (
            date_key,
            full_date,
            day_of_month,
            day_of_week,
            day_of_week_name,
            day_of_week_abbr,
            day_of_year,
            week_of_year,
            iso_week,
            month,
            month_name,
            month_abbr,
            quarter,
            quarter_name,
            year,
            fiscal_year,
            fiscal_quarter,
            fiscal_month,
            is_weekend,
            is_weekday,
            is_business_day
        ) VALUES (
            TO_CHAR(current_date, 'YYYYMMDD')::INT,
            current_date,
            EXTRACT(DAY FROM current_date),
            dow,
            TO_CHAR(current_date, 'Day'),
            TO_CHAR(current_date, 'Dy'),
            EXTRACT(DOY FROM current_date),
            EXTRACT(WEEK FROM current_date),
            EXTRACT(WEEK FROM current_date),
            EXTRACT(MONTH FROM current_date),
            TO_CHAR(current_date, 'Month'),
            TO_CHAR(current_date, 'Mon'),
            EXTRACT(QUARTER FROM current_date),
            'Q' || EXTRACT(QUARTER FROM current_date),
            EXTRACT(YEAR FROM current_date),
            fiscal_yr,
            CASE
                WHEN EXTRACT(MONTH FROM current_date) BETWEEN 4 AND 6 THEN 1
                WHEN EXTRACT(MONTH FROM current_date) BETWEEN 7 AND 9 THEN 2
                WHEN EXTRACT(MONTH FROM current_date) BETWEEN 10 AND 12 THEN 3
                ELSE 4
            END,
            CASE
                WHEN EXTRACT(MONTH FROM current_date) >= 4
                THEN EXTRACT(MONTH FROM current_date) - 3
                ELSE EXTRACT(MONTH FROM current_date) + 9
            END,
            is_wknd,
            NOT is_wknd,
            NOT is_wknd  -- Can be enhanced with holiday logic
        );

        current_date := current_date + INTERVAL '1 day';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Populate with 10 years of data (2020-2030)
SELECT populate_date_dimension('2020-01-01'::DATE, '2030-12-31'::DATE);

-- Add US Federal Holidays
UPDATE dim_date SET is_holiday = TRUE, holiday_name = 'New Year''s Day'
WHERE month = 1 AND day_of_month = 1;

UPDATE dim_date SET is_holiday = TRUE, holiday_name = 'Independence Day'
WHERE month = 7 AND day_of_month = 4;

UPDATE dim_date SET is_holiday = TRUE, holiday_name = 'Christmas Day'
WHERE month = 12 AND day_of_month = 25;

-- Memorial Day (last Monday in May)
UPDATE dim_date SET is_holiday = TRUE, holiday_name = 'Memorial Day'
WHERE month = 5
  AND day_of_week = 1
  AND day_of_month >= 25;

-- Labor Day (first Monday in September)
UPDATE dim_date SET is_holiday = TRUE, holiday_name = 'Labor Day'
WHERE month = 9
  AND day_of_week = 1
  AND day_of_month <= 7;

-- Thanksgiving (fourth Thursday in November)
UPDATE dim_date SET is_holiday = TRUE, holiday_name = 'Thanksgiving'
WHERE month = 11
  AND day_of_week = 4
  AND day_of_month BETWEEN 22 AND 28;

-- Update business days (weekday AND not holiday)
UPDATE dim_date SET is_business_day = FALSE WHERE is_holiday = TRUE;

-- ============================================
-- EXAMPLE QUERIES USING DATE DIMENSION
-- ============================================

-- Total spending by quarter
-- SELECT
--     d.year,
--     d.quarter_name,
--     SUM(r.total_amount) as total_spent,
--     COUNT(r.id) as receipt_count
-- FROM receipts r
-- JOIN dim_date d ON r.purchase_date = d.full_date
-- GROUP BY d.year, d.quarter, d.quarter_name
-- ORDER BY d.year, d.quarter;

-- Weekday vs weekend spending
-- SELECT
--     CASE WHEN d.is_weekend THEN 'Weekend' ELSE 'Weekday' END as day_type,
--     COUNT(r.id) as purchases,
--     SUM(r.total_amount) as total_spent,
--     AVG(r.total_amount) as avg_purchase
-- FROM receipts r
-- JOIN dim_date d ON r.purchase_date = d.full_date
-- GROUP BY d.is_weekend;

-- Fiscal year summary
-- SELECT
--     d.fiscal_year,
--     d.fiscal_quarter,
--     SUM(r.total_amount) as total_spent
-- FROM receipts r
-- JOIN dim_date d ON r.purchase_date = d.full_date
-- GROUP BY d.fiscal_year, d.fiscal_quarter
-- ORDER BY d.fiscal_year, d.fiscal_quarter;

-- Year-over-year comparison
-- SELECT
--     d.month_name,
--     SUM(CASE WHEN d.year = 2023 THEN r.total_amount ELSE 0 END) as spend_2023,
--     SUM(CASE WHEN d.year = 2024 THEN r.total_amount ELSE 0 END) as spend_2024,
--     SUM(CASE WHEN d.year = 2024 THEN r.total_amount ELSE 0 END) -
--     SUM(CASE WHEN d.year = 2023 THEN r.total_amount ELSE 0 END) as yoy_change
-- FROM receipts r
-- JOIN dim_date d ON r.purchase_date = d.full_date
-- WHERE d.year IN (2023, 2024)
-- GROUP BY d.month, d.month_name
-- ORDER BY d.month;
