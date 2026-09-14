-- =========================================================================
-- Week 8: SQL Fundamentals for Data Projects
-- Project: MassKara Festival Google Trends & Travel Price Tracker
-- Database: data/masskara.db (SQLite)
-- =========================================================================

-- -------------------------------------------------------------------------
-- Business Question 1: What is the "Festival Price Premium"?
-- Does traveling during the MassKara festival (Oct 9-13) cost more than
-- typical rolling baseline travel dates?
-- -------------------------------------------------------------------------

-- 1A: Flights comparison (Festival Target vs Rolling Baseline)
SELECT 
    collection_mode,
    COUNT(*) AS total_flight_quotes,
    ROUND(MIN(price_php), 2) AS min_price_php,
    ROUND(AVG(price_php), 2) AS avg_price_php,
    ROUND(MAX(price_php), 2) AS max_price_php
FROM flights
WHERE status = 'success' AND price_php IS NOT NULL
GROUP BY collection_mode;

-- 1B: Hotels comparison (Festival Target 4-night stay vs Rolling 1-night stay)
SELECT 
    collection_mode,
    COUNT(*) AS total_hotel_quotes,
    ROUND(MIN(price_php), 2) AS min_price_php,
    ROUND(AVG(price_php), 2) AS avg_price_php,
    ROUND(MAX(price_php), 2) AS max_price_php
FROM hotels
WHERE status = 'success' AND price_php IS NOT NULL
GROUP BY collection_mode;


-- -------------------------------------------------------------------------
-- Business Question 2: How are Festival Prices Escalating Over Time?
-- As booking lead time shrinks leading up to the festival, how do opening-day
-- flight prices shift across collection dates?
-- -------------------------------------------------------------------------
SELECT 
    date_collected,
    COUNT(*) AS flight_options_scraped,
    ROUND(MIN(price_php), 2) AS cheapest_flight_php,
    ROUND(AVG(price_php), 2) AS avg_flight_php,
    ROUND(MAX(price_php), 2) AS max_flight_php
FROM flights
WHERE collection_mode = 'festival_target' 
  AND status = 'success' 
  AND price_php IS NOT NULL
GROUP BY date_collected
ORDER BY date_collected ASC;


-- -------------------------------------------------------------------------
-- Business Question 3: How Does Public Search Interest Align with Prices?
-- Joining Google Trends search index with festival flight prices on each 
-- collection date to prepare for correlation and lead-time analysis.
-- -------------------------------------------------------------------------
WITH daily_trends AS (
    SELECT 
        date_collected,
        MAX(interest_value) AS peak_search_interest,
        ROUND(AVG(interest_value), 1) AS avg_search_interest
    FROM trends
    WHERE status = 'success'
    GROUP BY date_collected
),
daily_festival_flights AS (
    SELECT 
        date_collected,
        MIN(price_php) AS cheapest_festival_fare,
        ROUND(AVG(price_php), 2) AS avg_festival_fare
    FROM flights
    WHERE collection_mode = 'festival_target' AND status = 'success'
    GROUP BY date_collected
)
SELECT 
    f.date_collected,
    t.peak_search_interest,
    t.avg_search_interest AS trend_window_avg,
    f.cheapest_festival_fare,
    f.avg_festival_fare
FROM daily_festival_flights f
LEFT JOIN daily_trends t ON f.date_collected = t.date_collected
ORDER BY f.date_collected ASC;


-- -------------------------------------------------------------------------
-- Bonus Question 4: Airline Price Comparison for Festival Flights
-- Which carrier offers the most competitive rates for MassKara arrival?
-- -------------------------------------------------------------------------
SELECT 
    airline,
    COUNT(*) AS total_flight_options,
    ROUND(MIN(price_php), 2) AS lowest_fare_php,
    ROUND(AVG(price_php), 2) AS avg_fare_php,
    ROUND(MAX(price_php), 2) AS highest_fare_php
FROM flights
WHERE collection_mode = 'festival_target' 
  AND status = 'success' 
  AND airline IS NOT NULL
GROUP BY airline
ORDER BY avg_fare_php ASC;
