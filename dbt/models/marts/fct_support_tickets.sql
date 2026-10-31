
WITH tickets AS (

    SELECT *
    FROM {{ ref('stg_support_tickets') }}

),

priority AS (

    SELECT *
    FROM {{ ref('int_ticket_priority_scores') }}

),

sla AS (

    SELECT *
    FROM {{ ref('int_ticket_sla') }}

)

SELECT
    t.ticket_id,
    t.customer_id,
    t.agent_id,

    t.customer_tier,
    t.category,
    t.severity,
    t.impact_scope,
    t.channel,
    t.status,

    t.created_at,
    t.updated_at,
    t.first_response_at,
    t.resolved_at,
    t.snapshot_at,

    t.reopened_count,
    t.csat_score,

    p.severity_points,
    p.impact_points,
    p.customer_tier_points,
    p.reopened_points,
    p.priority_score,
    p.priority_band,
    p.priority_reason,

    s.first_response_target_hours,
    s.resolution_target_hours,

    s.first_response_due_at,
    s.resolution_due_at,

    s.first_response_elapsed_hours,
    s.resolution_elapsed_hours,

    s.first_response_minutes_remaining,
    s.resolution_minutes_remaining,

    s.first_response_sla_status,
    s.resolution_sla_status,

    ROUND(
        DATE_DIFF(
            'second',
            t.created_at,
            t.snapshot_at
        ) / 3600.0,
        2
    ) AS ticket_age_hours,

    CASE
        WHEN t.first_response_at IS NOT NULL
        THEN ROUND(
            DATE_DIFF(
                'second',
                t.created_at,
                t.first_response_at
            ) / 3600.0,
            2
        )
        ELSE NULL
    END AS actual_first_response_hours,

    CASE
        WHEN t.resolved_at IS NOT NULL
        THEN ROUND(
            DATE_DIFF(
                'second',
                t.created_at,
                t.resolved_at
            ) / 3600.0,
            2
        )
        ELSE NULL
    END AS actual_resolution_hours,

    CASE
        WHEN t.status IN (
            'open',
            'in_progress',
            'pending_customer'
        )
        THEN TRUE
        ELSE FALSE
    END AS is_open_ticket,

    CASE
        WHEN t.status IN ('resolved', 'closed')
        THEN TRUE
        ELSE FALSE
    END AS is_resolved,

    t.agent_id IS NOT NULL AS is_assigned,

    COALESCE(t.reopened_count, 0) > 0 AS is_reopened

FROM tickets t

LEFT JOIN priority p
    ON t.ticket_id = p.ticket_id

LEFT JOIN sla s
    ON t.ticket_id = s.ticket_id
