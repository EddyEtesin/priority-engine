
WITH source AS (

    SELECT *
    FROM {{ source('raw', 'support_tickets') }}

),

cleaned AS (

    SELECT
        TRIM(CAST(ticket_id AS VARCHAR)) AS ticket_id,
        TRIM(CAST(customer_id AS VARCHAR)) AS customer_id,

        LOWER(TRIM(CAST(customer_tier AS VARCHAR))) AS customer_tier,
        LOWER(TRIM(CAST(category AS VARCHAR))) AS category,
        LOWER(TRIM(CAST(severity AS VARCHAR))) AS severity,
        LOWER(TRIM(CAST(impact_scope AS VARCHAR))) AS impact_scope,
        LOWER(TRIM(CAST(channel AS VARCHAR))) AS channel,
        LOWER(TRIM(CAST(status AS VARCHAR))) AS status,

        NULLIF(TRIM(CAST(description AS VARCHAR)), '') AS description,

        TRY_CAST(created_at AS TIMESTAMPTZ) AS created_at,
        TRY_CAST(updated_at AS TIMESTAMPTZ) AS updated_at,

        TRY_CAST(first_response_at AS TIMESTAMPTZ)
            AS first_response_at,

        TRY_CAST(resolved_at AS TIMESTAMPTZ)
            AS resolved_at,

        NULLIF(TRIM(CAST(agent_id AS VARCHAR)), '') AS agent_id,

        TRY_CAST(reopened_count AS INTEGER) AS reopened_count,
        TRY_CAST(csat_score AS INTEGER) AS csat_score,
        TRY_CAST(snapshot_at AS TIMESTAMPTZ) AS snapshot_at

    FROM source

)

SELECT *
FROM cleaned
