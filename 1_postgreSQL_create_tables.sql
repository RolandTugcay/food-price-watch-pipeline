-- Create Database and Tables for Food Price Watch Pipeline

-- Create the database
CREATE DATABASE hdx_ph_food_prices;


-- 1. Markets
CREATE TABLE markets (
    market_id INTEGER PRIMARY KEY,
    market_name TEXT NOT NULL,
    admin1 TEXT NOT NULL,
    admin2 TEXT NOT NULL,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6)
);

-- 2. Food categories
CREATE TABLE categories (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

-- 3. Food commodities
CREATE TABLE commodities (
    commodity_id INTEGER PRIMARY KEY,
    commodity_name TEXT NOT NULL,
    category_id INTEGER NOT NULL
        REFERENCES categories(category_id),
    UNIQUE (commodity_name, category_id)
);

-- 4. Historical food prices
CREATE TABLE price_observations (
    price_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    observation_date DATE NOT NULL,
    market_id INTEGER NOT NULL
        REFERENCES markets(market_id),
    commodity_id INTEGER NOT NULL
        REFERENCES commodities(commodity_id),
    unit TEXT NOT NULL,
    price_flag TEXT NOT NULL,
    price_type TEXT NOT NULL,
    currency CHAR(3) NOT NULL,
    price NUMERIC(14, 4) NOT NULL,
    usd_price NUMERIC(14, 4) NOT NULL,

    CONSTRAINT uq_price_observation UNIQUE (
        observation_date,
        market_id,
        commodity_id,
        unit,
        price_type,
        currency
    )
);

-- 5. Temporary import/staging table
CREATE TABLE staging_food_prices (
    date DATE,
    admin1 TEXT,
    admin2 TEXT,
    market TEXT,
    market_id INTEGER,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    category TEXT,
    commodity TEXT,
    commodity_id INTEGER,
    unit TEXT,
    priceflag TEXT,
    pricetype TEXT,
    currency CHAR(3),
    price NUMERIC(14, 4),
    usdprice NUMERIC(14, 4)
);

-- Indexes for common queries
CREATE INDEX idx_prices_date
    ON price_observations (observation_date);

CREATE INDEX idx_prices_market_date
    ON price_observations (market_id, observation_date);

CREATE INDEX idx_prices_commodity_date
    ON price_observations (commodity_id, observation_date);

CREATE INDEX idx_prices_type
    ON price_observations (price_type);
