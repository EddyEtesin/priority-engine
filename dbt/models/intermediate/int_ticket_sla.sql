
WITH tickets AS (

    SELECT *
    FROM {{ ref('stg_support_tickets') }}

),

sla_targets AS (

    SELECT
        *,

        CASE severity
            WHEN 'critical' THEN 0.25
            WHEN 'high' THEN 1.0
            WHEN 'medium' THEN 4.0
            WHEN 'low' THEN 24.0
        END AS first_response_target_hours,

        CASE severity
            WHEN 'critical' THEN 4.0
            WHEN 'high' THEN 12.0
            WHEN 'medium' THEN 48.0
            WHEN 'low' THEN 120.0
        END AS resolution_target_hours

    FROM tickets

),

deadlines AS (

    SELECT
        *,

        created_at
            + first_response_target_hours * INTERVAL '1 hour'
            AS first_response_due_at,

        created_at
            + resolution_target_hours * INTERVAL '1 hour'
            AS resolution_due_at,

        DATE_DIFF(
            'second',
            created_at,
            COALESCE(first_response_at, snapshot_at)
        ) / 3600.0 AS first_response_elapsed_hours,

        DATE_DIFF(
            'second',
            created_at,
            COALESCE(resolved_at, snapshot_at)
        ) / 3600.0 AS resolution_elapsed_hours

    FROM sla_targets

),

sla_status AS (

    SELECT
        *,

        CASE
            WHEN first_response_at IS NOT NULL
                 AND first_response_at <= first_response_due_at
                THEN 'met'

            WHEN first_response_at IS NOT NULL
                 AND first_response_at > first_response_due_at
                THEN 'breached'

            WHEN snapshot_at > first_response_due_at
                THEN 'breached'

            WHEN first_response_elapsed_hours
                 >= first_response_target_hours * 0.80
                THEN 'at_risk'

            ELSE 'on_track'
        END AS first_response_sla_status,

        CASE
            WHEN resolved_at IS NOT NULL
                 AND resolved_at <= resolution_due_at
                THEN 'met'

            WHEN resolved_at IS NOT NULL
                 AND resolved_at > resolution_due_at
                THEN 'breached'

            WHEN snapshot_at > resolution_due_at
                THEN 'breached'

            WHEN resolution_elapsed_hours
                 >= resolution_target_hours * 0.80
                THEN 'at_risk'

            ELSE 'on_track'
        END AS resolution_sla_status

    FROM deadlines

)

SELECT
    ticket_id,
    severity,
    status,
    created_at,
    snapshot_at,
    first_response_at,
    resolved_at,

    first_response_target_hours,
    resolution_target_hours,

    first_response_due_at,
    resolution_due_at,

    ROUND(first_response_elapsed_hours, 2)
        AS first_response_elapsed_hours,

    ROUND(resolution_elapsed_hours, 2)
        AS resolution_elapsed_hours,

    ROUND(
        DATE_DIFF(
            'second',
            snapshot_at,
            first_response_due_at
        ) / 60.0,
        2
    ) AS first_response_minutes_remaining,

    ROUND(
        DATE_DIFF(
            'second',
            snapshot_at,
            resolution_due_at
        ) / 60.0,
        2
    ) AS resolution_minutes_remaining,

    first_response_sla_status,
    resolution_sla_status

FROM sla_status
