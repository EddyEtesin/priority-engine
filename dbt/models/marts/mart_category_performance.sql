
SELECT
    category,

    COUNT(*) AS total_tickets,

    SUM(
        CASE WHEN is_open_ticket THEN 1 ELSE 0 END
    ) AS open_tickets,

    SUM(
        CASE WHEN priority_band = 'P1' THEN 1 ELSE 0 END
    ) AS p1_tickets,

    SUM(
        CASE WHEN priority_band = 'P2' THEN 1 ELSE 0 END
    ) AS p2_tickets,

    SUM(
        CASE
            WHEN first_response_sla_status = 'breached'
            THEN 1 ELSE 0
        END
    ) AS first_response_breaches,

    SUM(
        CASE
            WHEN resolution_sla_status = 'breached'
            THEN 1 ELSE 0
        END
    ) AS resolution_breaches,

    ROUND(
        AVG(actual_resolution_hours),
        2
    ) AS average_resolution_hours,

    ROUND(
        AVG(CAST(csat_score AS DOUBLE)),
        2
    ) AS average_csat_score

FROM {{ ref('fct_support_tickets') }}

GROUP BY category
