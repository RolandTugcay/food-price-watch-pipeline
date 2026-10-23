-- Import the csv file using PL SQL
-- \COPY staging_food_prices FROM 'C:\Users\Roland\Documents\Workspace\Python\FoodPriceWatchPipeline\wfp_food_prices_phl.csv'  DELIMITER e',' CSV HEADER

-- Populate markets table
INSERT INTO markets
SELECT DISTINCT market_id, market as market_name, admin1, admin2, latitude, longitude from staging_food_prices
ORDER BY market_id

-- Populate categories table
INSERT INTO categories (category_name)
SELECT DISTINCT TRIM(category) FROM staging_food_prices
ON CONFLICT (category_name) DO NOTHING;

-- Populate commodities table
INSERT INTO commodities
SELECT DISTINCT
    s.commodity_id,
    TRIM(s.commodity),
    c.category_id
FROM staging_food_prices s
INNER JOIN categories c
    ON c.category_name = TRIM(s.category)
WHERE s.commodity_id IS NOT NULL
  AND s.commodity IS NOT NULL
  AND TRIM(s.commodity) <> ''
ON CONFLICT (commodity_id) DO NOTHING;

-- Populate price_observations
INSERT INTO price_observations (
    observation_date,
    market_id,
    commodity_id,
    unit,
    price_flag,
    price_type,
    currency,
    price,
    usd_price
)
SELECT
    s.date,
    s.market_id,
    s.commodity_id,
    s.unit,
    s.priceflag,
    s.pricetype,
    s.currency,
    s.price,
    s.usdprice
FROM staging_food_prices s
WHERE s.date IS NOT NULL
  AND s.market_id IS NOT NULL
  AND s.commodity_id IS NOT NULL
  AND s.unit IS NOT NULL
  AND s.pricetype IS NOT NULL
  AND s.currency IS NOT NULL
ON CONFLICT (
    observation_date,
    market_id,
    commodity_id,
    unit,
    price_type,
    currency
)
DO UPDATE SET
    price_flag = EXCLUDED.price_flag,
    price = EXCLUDED.price,
    usd_price = EXCLUDED.usd_price;
