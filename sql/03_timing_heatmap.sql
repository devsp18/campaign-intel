-- Send/exposure timing: conversion by day-of-week x hour for the treated
-- group, only where the cell has enough users to be meaningful.
SELECT
    most_ads_day                    AS day,
    most_ads_hour                   AS hour,
    COUNT(*)                        AS users,
    ROUND(AVG(converted) * 100, 3)  AS conv_rate_pct
FROM experiment_users
WHERE test_group = 'ad'
GROUP BY most_ads_day, most_ads_hour
HAVING COUNT(*) >= 500
ORDER BY
    CASE most_ads_day
        WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
        WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
        ELSE 7
    END, most_ads_hour;
