
SELECT
    customer_id,

    MIN(customer_tier) AS customer_tier,

    MIN(created_at) AS first_ticket_at,

    MAX(created_at) AS latest_ticket_at,

    COUNT(*) AS total_tickets,

    COUNT(DISTINCT category) AS categories_used,

    SUM(
        CASE
            WHEN reopened_count > 0 THEN 1
            ELSE 0
        END
    ) AS reopened_tickets,

    COUNT(csat_score) AS tickets_with_csat,

    ROUND(
        AVG(CAST(csat_score AS DOUBLE)),
        2
    ) AS average_csat_score

FROM {{ ref('stg_support_tickets') }}

GROUP BY customer_id
