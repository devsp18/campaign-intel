-- Frequency analysis: does conversion rise (or fatigue) with ad exposure?
-- Exposure banded with CASE; window function gives each band's share.
WITH banded AS (
    SELECT
        CASE
            WHEN total_ads BETWEEN 1  AND 5   THEN '01-05'
            WHEN total_ads BETWEEN 6  AND 15  THEN '06-15'
            WHEN total_ads BETWEEN 16 AND 30  THEN '16-30'
            WHEN total_ads BETWEEN 31 AND 60  THEN '31-60'
            WHEN total_ads BETWEEN 61 AND 120 THEN '61-120'
            ELSE '121+'
        END AS exposure_band,
        converted
    FROM experiment_users
    WHERE test_group = 'ad'
)
SELECT
    exposure_band,
    COUNT(*)                                           AS users,
    ROUND(AVG(converted) * 100, 3)                     AS conv_rate_pct,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_users
FROM banded
GROUP BY exposure_band
ORDER BY exposure_band;
