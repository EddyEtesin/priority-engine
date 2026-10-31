SELECT
    agent_id,
    MIN(created_at) AS first_ticket_assigned_at,
    MAX(created_at) AS latest_ticket_assigned_at
FROM {{ ref('stg_support_tickets') }}
WHERE agent_id IS NOT NULL
GROUP BY agent_id