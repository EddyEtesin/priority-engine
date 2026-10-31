
SELECT
    customer_id

FROM {{ ref('stg_support_tickets') }}

GROUP BY customer_id

HAVING COUNT(DISTINCT customer_tier) > 1
