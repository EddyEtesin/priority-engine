
from __future__ import annotations

import sys
from pathlib import Path

import duckdb


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_FILE = PROJECT_ROOT / "data" / "raw" / "support_tickets.csv"

DATABASE_DIR = PROJECT_ROOT / "data" / "warehouse"
DATABASE_FILE = DATABASE_DIR / "priority_engine.duckdb"


REQUIRED_COLUMNS = {
    "ticket_id",
    "customer_id",
    "customer_tier",
    "category",
    "severity",
    "impact_scope",
    "channel",
    "status",
    "description",
    "created_at",
    "updated_at",
    "first_response_at",
    "resolved_at",
    "agent_id",
    "reopened_count",
    "csat_score",
    "snapshot_at",
}


# ---------------------------------------------------------
# VALIDATE SOURCE
# ---------------------------------------------------------

def validate_source(connection: duckdb.DuckDBPyConnection) -> int:

    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw.support_tickets
        """
    ).fetchone()

    row_count = int(result[0])

    if row_count == 0:
        raise ValueError("The source CSV contains no ticket records.")

    distinct_count = connection.execute(
        """
        SELECT COUNT(DISTINCT ticket_id)
        FROM raw.support_tickets
        """
    ).fetchone()[0]

    if distinct_count != row_count:
        raise ValueError(
            f"Duplicate ticket IDs detected. "
            f"Rows: {row_count}, distinct IDs: {distinct_count}"
        )

    null_ids = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw.support_tickets
        WHERE ticket_id IS NULL
        """
    ).fetchone()[0]

    if null_ids:
        raise ValueError(
            f"{null_ids} tickets have missing ticket IDs."
        )

    invalid_severity = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw.support_tickets
        WHERE severity NOT IN ('critical', 'high', 'medium', 'low')
        """
    ).fetchone()[0]

    if invalid_severity:
        raise ValueError(
            f"{invalid_severity} tickets have invalid severity values."
        )

    return row_count


# ---------------------------------------------------------
# INGESTION
# ---------------------------------------------------------

def ingest_tickets() -> None:

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Ticket CSV not found: {CSV_FILE}\n"
            "Run generate_tickets.py first."
        )

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Starting Priority Engine ingestion...")
    print(f"Source: {CSV_FILE}")
    print(f"Database: {DATABASE_FILE}")

    connection = duckdb.connect(
        str(DATABASE_FILE)
    )

    try:
        connection.execute(
            "CREATE SCHEMA IF NOT EXISTS raw"
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.ingestion_log (
                ingestion_id VARCHAR,
                ingested_at TIMESTAMPTZ,
                source_file VARCHAR,
                row_count BIGINT,
                dataset_as_of TIMESTAMPTZ
            )
            """
        )

        # Read the CSV and replace the raw table.
        # Re-running the script is safe and does not duplicate tickets.

        connection.execute(
            """
            CREATE OR REPLACE TABLE raw.support_tickets AS
            SELECT *
            FROM read_csv_auto(
                ?,
                header = true,
                sample_size = -1,
                nullstr = ''
            )
            """,
            [str(CSV_FILE)],
        )

        # Check that all expected columns are present.
        actual_columns = {
            row[0]
            for row in connection.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'raw'
                  AND table_name = 'support_tickets'
                """
            ).fetchall()
        }

        missing_columns = REQUIRED_COLUMNS - actual_columns

        if missing_columns:
            raise ValueError(
                f"Missing columns in source data: "
                f"{sorted(missing_columns)}"
            )

        row_count = validate_source(connection)

        # Record this ingestion run.
        connection.execute(
            """
            INSERT INTO raw.ingestion_log
            SELECT
                CAST(uuid() AS VARCHAR),
                current_timestamp,
                ?,
                COUNT(*),
                MAX(snapshot_at)
            FROM raw.support_tickets
            """,
            [CSV_FILE.name],
        )

        # Display a brief ingestion summary.
        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total_tickets,
                COUNT(DISTINCT customer_id) AS customers,
                COUNT(DISTINCT agent_id) AS assigned_agents,
                MIN(created_at) AS earliest_ticket,
                MAX(created_at) AS latest_ticket,
                MAX(snapshot_at) AS snapshot_at
            FROM raw.support_tickets
            """
        ).fetchdf()

        print("\nINGESTION COMPLETED")
        print("=" * 45)
        print(f"Rows loaded: {row_count:,}")
        print(f"Database: {DATABASE_FILE}")
        print("\nDataset summary:")
        print(summary.to_string(index=False))

        print("\nStatus distribution:")

        status_summary = connection.execute(
            """
            SELECT
                status,
                COUNT(*) AS ticket_count,
                ROUND(
                    100.0 * COUNT(*) /
                    SUM(COUNT(*)) OVER (),
                    2
                ) AS percentage
            FROM raw.support_tickets
            GROUP BY status
            ORDER BY ticket_count DESC
            """
        ).fetchdf()

        print(status_summary.to_string(index=False))

        print("\nIngestion history:")

        history = connection.execute(
            """
            SELECT *
            FROM raw.ingestion_log
            ORDER BY ingested_at DESC
            LIMIT 5
            """
        ).fetchdf()

        print(history.to_string(index=False))

    finally:
        connection.close()


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":

    try:
        ingest_tickets()

    except Exception as exc:
        print(f"\nINGESTION FAILED: {exc}", file=sys.stderr)
        raise
