-- Content vs engagement: subject-line strength and body length against
-- engagement, with NTILE quartiles for word count.
WITH scored AS (
    SELECT
        CASE
            WHEN Subject_Hotness_Score < 1 THEN 'Low (0-1)'
            WHEN Subject_Hotness_Score < 2 THEN 'Mid (1-2)'
            WHEN Subject_Hotness_Score < 3 THEN 'High (2-3)'
            ELSE 'Very High (3+)'
        END AS subject_strength,
        NTILE(4) OVER (ORDER BY Word_Count) AS wordcount_quartile,
        engaged, acknowledged
    FROM email_campaigns
)
SELECT
    subject_strength,
    wordcount_quartile,
    COUNT(*)                          AS emails,
    ROUND(AVG(engaged) * 100, 2)      AS engagement_pct,
    ROUND(AVG(acknowledged) * 100, 2) AS acknowledged_pct
FROM scored
GROUP BY subject_strength, wordcount_quartile
ORDER BY subject_strength, wordcount_quartile;
