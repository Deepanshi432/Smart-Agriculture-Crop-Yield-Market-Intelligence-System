-- Business questions for the Smart Agriculture project (SQLite)

-- Q1. Top 5 crops by TOTAL PRODUCTION in each state (Coconut excluded: counted in nuts, not tonnes)
SELECT * FROM (
  SELECT state, crop, ROUND(SUM(production)) AS total_production,
         ROW_NUMBER() OVER (PARTITION BY state ORDER BY SUM(production) DESC) AS rnk
  FROM crop_yield
  WHERE crop <> 'Coconut'
  GROUP BY state, crop
) WHERE rnk <= 5
ORDER BY state, rnk;

-- Q2. Year-over-year production growth for Rice (all India)
WITH yearly AS (
  SELECT year, SUM(production) AS prod
  FROM crop_yield WHERE crop = 'Rice' GROUP BY year
)
SELECT year, ROUND(prod) AS production,
       ROUND(100.0 * (prod - LAG(prod) OVER (ORDER BY year)) / LAG(prod) OVER (ORDER BY year), 2) AS yoy_growth_pct
FROM yearly ORDER BY year;

-- Q3. Season-wise performance for Wheat and Rice
SELECT crop, season, COUNT(*) AS records, ROUND(AVG("yield"), 2) AS avg_yield,
       ROUND(SUM(area)) AS total_area
FROM crop_yield WHERE crop IN ('Wheat', 'Rice')
GROUP BY crop, season ORDER BY crop, avg_yield DESC;

-- Q4. Top 5 districts by average Wheat yield in the last 5 years
SELECT state, district, ROUND(AVG("yield"), 2) AS avg_yield
FROM crop_yield
WHERE crop = 'Wheat' AND year >= (SELECT MAX(year) - 4 FROM crop_yield)
GROUP BY state, district ORDER BY avg_yield DESC LIMIT 5;

-- Q5. Do wetter monsoons give better Kharif rice yield? (rainfall bands)
SELECT CASE WHEN season_rainfall < 500 THEN '1. <500 mm'
            WHEN season_rainfall < 900 THEN '2. 500-900 mm'
            WHEN season_rainfall < 1400 THEN '3. 900-1400 mm'
            ELSE '4. >1400 mm' END AS rainfall_band,
       COUNT(*) AS records, ROUND(AVG("yield"), 2) AS avg_yield
FROM merged_yield WHERE crop = 'Rice' AND season = 'Kharif'
GROUP BY rainfall_band ORDER BY rainfall_band;

-- Q6. Most expensive commodities today (modal price, Rs/quintal)
SELECT commodity, ROUND(AVG(modal_price)) AS avg_modal_price, COUNT(*) AS markets
FROM mandi_prices GROUP BY commodity HAVING markets >= 20
ORDER BY avg_modal_price DESC LIMIT 10;
