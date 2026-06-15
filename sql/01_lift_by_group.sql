-- Incremental lift: conversion by experiment group with absolute and
-- relative lift computed in SQL via a conditional-aggregation pivot.
WITH grp AS (
    SELECT
        test_group,
        COUNT(*)                       AS users,
        SUM(converted)                 AS conversions,
        ROUND(AVG(converted) * 100, 4) AS conv_rate_pct
    FROM experiment_users
    GROUP BY test_group
),
pivoted AS (
    SELECT
        MAX(CASE WHEN test_group = 'ad'  THEN conv_rate_pct END) AS ad_rate,
        MAX(CASE WHEN test_group = 'psa' THEN conv_rate_pct END) AS control_rate
    FROM grp
)
SELECT
    g.*,
    ROUND(p.ad_rate - p.control_rate, 4)                          AS abs_lift_pp,
    ROUND((p.ad_rate - p.control_rate) / p.control_rate * 100, 1) AS rel_lift_pct
FROM grp g CROSS JOIN pivoted p;
