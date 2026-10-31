
WITH tickets AS (

    SELECT *
    FROM {{ ref('stg_support_tickets') }}

),

score_components AS (

    SELECT
        *,

        CASE severity
            WHEN 'critical' THEN 100
            WHEN 'high' THEN 70
            WHEN 'medium' THEN 40
            WHEN 'low' THEN 10
            ELSE 0
        END AS severity_points,

        CASE impact_scope
            WHEN 'widespread' THEN 30
            WHEN 'multiple_customers' THEN 20
            WHEN 'individual' THEN 5
            ELSE 0
        END AS impact_points,

        CASE customer_tier
            WHEN 'enterprise' THEN 15
            WHEN 'premium' THEN 8
            WHEN 'standard' THEN 0
            ELSE 0
        END AS customer_tier_points,

        LEAST(
            GREATEST(COALESCE(reopened_count, 0), 0) * 5,
            15
        ) AS reopened_points

    FROM tickets

),

scored AS (

    SELECT
        *,

        severity_points
        + impact_points
        + customer_tier_points
        + reopened_points AS priority_score

    FROM score_components

),

classified AS (

    SELECT
        *,

        CASE
            WHEN severity = 'critical'
                OR priority_score >= 120
                THEN 'P1'

            WHEN priority_score >= 85
                THEN 'P2'

            WHEN priority_score >= 45
                THEN 'P3'

            ELSE 'P4'
        END AS priority_band

    FROM scored

)

SELECT
    ticket_id,
    customer_id,
    customer_tier,
    category,
    severity,
    impact_scope,
    status,
    agent_id,
    created_at,
    snapshot_at,

    severity_points,
    impact_points,
    customer_tier_points,
    reopened_points,

    priority_score,
    priority_band,

    CASE
        WHEN severity = 'critical'
            THEN 'Critical severity override'
        WHEN priority_score >= 120
            THEN 'High combined risk score'
        WHEN priority_score >= 85
            THEN 'Elevated combined risk score'
        WHEN priority_score >= 45
            THEN 'Moderate combined risk score'
        ELSE 'Low combined risk score'
    END AS priority_reason

FROM classified
