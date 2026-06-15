-- Fatigue: engagement as a function of how many prior communications the
-- customer has already received.
SELECT
    CAST(Total_Past_Communications / 10 AS INT) * 10 AS past_comm_bucket,
    COUNT(*)                                          AS emails,
    ROUND(AVG(engaged) * 100, 2)                      AS engagement_pct
FROM email_campaigns
GROUP BY past_comm_bucket
HAVING COUNT(*) >= 300
ORDER BY past_comm_bucket;
