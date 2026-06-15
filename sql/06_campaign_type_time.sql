-- Campaign type x send-time bucket performance matrix.
SELECT
    Email_Campaign_Type             AS campaign_type,
    Time_Email_sent_Category        AS send_time_bucket,
    COUNT(*)                        AS emails,
    ROUND(AVG(engaged) * 100, 2)    AS engagement_pct
FROM email_campaigns
GROUP BY campaign_type, send_time_bucket
ORDER BY campaign_type, send_time_bucket;
