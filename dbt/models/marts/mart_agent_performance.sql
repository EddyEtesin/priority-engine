
SELECT
    agent_id,

    COUNT(*) AS assigned_tickets,

    SUM(
        CASE WHEN is_open_ticket THEN 1 ELSE 0 END
    ) AS open_tickets,

    SUM(
        CASE
            WHEN is_open_ticket
             AND priority_band IN ('P1', 'P2')
            THEN 1
            ELSE 0
        END
    ) AS urgent_open_tickets,

    SUM(
        CASE
            WHEN first_response_sla_status = 'met'
            THEN 1 ELSE 0
        END
    ) AS first_response_sla_met,

    SUM(
        CASE
            WHEN first_response_sla_status = 'breached'
            THEN 1 ELSE 0
        END
    ) AS first_response_sla_breached,

    SUM(
        CASE
            WHEN resolution_sla_status = 'met'
            THEN 1 ELSE 0
        END
    ) AS resolution_sla_met,

    SUM(
        CASE
            WHEN resolution_sla_status = 'breached'
            THEN 1 ELSE 0
        END
    ) AS resolution_sla_breached,

    ROUND(
        AVG(actual_resolution_hours),
        2
    ) AS average_resolution_hours,

    ROUND(
        AVG(CAST(csat_score AS DOUBLE)),
        2
    ) AS average_csat_score,

    SUM(
        CASE WHEN is_reopened THEN 1 ELSE 0 END
    ) AS reopened_tickets

FROM {{ ref('fct_support_tickets') }}

WHERE agent_id IS NOT NULL

GROUP BY agent_id
