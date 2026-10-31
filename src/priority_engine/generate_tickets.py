
from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------
# PROJECT CONFIGURATION
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "support_tickets.csv"

RANDOM_SEED = 20261030
DEFAULT_AS_OF = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)

NUMBER_OF_TICKETS = 800
NUMBER_OF_CUSTOMERS = 250
NUMBER_OF_AGENTS = 12


# ---------------------------------------------------------
# REFERENCE DATA
# ---------------------------------------------------------

CATEGORIES = {
    "payments": [
        "Payment failed during checkout",
        "Customer charged twice",
        "Refund has not been received",
        "Card payment rejected",
        "Transaction pending for too long",
    ],
    "account_access": [
        "Customer cannot log in",
        "Password reset not working",
        "Account temporarily locked",
        "Two-factor authentication failure",
        "Customer unable to verify account",
    ],
    "delivery": [
        "Delivery has been delayed",
        "Order marked delivered but not received",
        "Wrong item delivered",
        "Missing item in order",
        "Delivery address needs correction",
    ],
    "technical_issue": [
        "Application crashes during use",
        "Website page fails to load",
        "Checkout page is not responding",
        "Mobile application displays an error",
        "Customer cannot upload a document",
    ],
    "billing": [
        "Incorrect charge on customer account",
        "Invoice contains an error",
        "Subscription charged incorrectly",
        "Customer requests billing clarification",
        "Unexpected account deduction",
    ],
    "product_information": [
        "Customer requests product information",
        "Question about product availability",
        "Customer needs help choosing a product",
        "Request for product specifications",
        "Question about product features",
    ],
}

SEVERITIES = ["critical", "high", "medium", "low"]

SEVERITY_WEIGHTS = [5, 20, 45, 30]

CUSTOMER_TIERS = ["standard", "premium", "enterprise"]
CUSTOMER_TIER_WEIGHTS = [72, 20, 8]

CHANNELS = ["email", "chat", "phone", "web_form"]
CHANNEL_WEIGHTS = [35, 30, 20, 15]

STATUSES = [
    "open",
    "in_progress",
    "pending_customer",
    "resolved",
    "closed",
]

STATUS_WEIGHTS = [18, 28, 12, 25, 17]

AGENT_IDS = [
    f"AGT-{number:03d}"
    for number in range(1, NUMBER_OF_AGENTS + 1)
]

CUSTOMER_IDS = [
    f"CUST-{number:04d}"
    for number in range(1, NUMBER_OF_CUSTOMERS + 1)
]


# ---------------------------------------------------------
# SLA REFERENCE VALUES
# These are elapsed-clock-hour targets.
# Business-hour calendars are not applied in V1.
# ---------------------------------------------------------

SLA_TARGETS = {
    "critical": {
        "first_response_hours": 0.25,
        "resolution_hours": 4,
    },
    "high": {
        "first_response_hours": 1,
        "resolution_hours": 12,
    },
    "medium": {
        "first_response_hours": 4,
        "resolution_hours": 48,
    },
    "low": {
        "first_response_hours": 24,
        "resolution_hours": 120,
    },
}


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def utc_iso(value: datetime | None) -> str:
    """Return a consistent ISO-8601 UTC timestamp."""

    if value is None:
        return ""

    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def choose_impact_scope(
    rng: random.Random,
    severity: str,
) -> str:
    """Generate an impact scope influenced by severity."""

    distributions = {
        "critical": (
            ["widespread", "multiple_customers", "individual"],
            [55, 35, 10],
        ),
        "high": (
            ["widespread", "multiple_customers", "individual"],
            [15, 55, 30],
        ),
        "medium": (
            ["widespread", "multiple_customers", "individual"],
            [5, 30, 65],
        ),
        "low": (
            ["widespread", "multiple_customers", "individual"],
            [1, 9, 90],
        ),
    }

    options, weights = distributions[severity]

    return rng.choices(options, weights=weights, k=1)[0]


def choose_status(
    rng: random.Random,
    ticket_age_hours: float,
) -> str:
    """Select a status while avoiding impossible recent resolutions."""

    options = STATUSES.copy()
    weights = STATUS_WEIGHTS.copy()

    # Very recent tickets are less likely to be resolved or closed.
    if ticket_age_hours < 12:
        weights[3] = 8
        weights[4] = 4
        weights[0] = 30
        weights[1] = 40

    elif ticket_age_hours < 48:
        weights[3] = 18
        weights[4] = 10

    return rng.choices(options, weights=weights, k=1)[0]


def make_response_timestamp(
    rng: random.Random,
    created_at: datetime,
    snapshot_at: datetime,
    severity: str,
) -> datetime | None:
    """Generate a first-response timestamp."""

    response_probability = 0.88

    if rng.random() > response_probability:
        return None

    target_hours = SLA_TARGETS[severity]["first_response_hours"]

    # Some responses meet SLA, while others breach it.
    if rng.random() < 0.78:
        response_hours = target_hours * rng.uniform(0.20, 0.95)
    else:
        response_hours = target_hours * rng.uniform(1.05, 3.50)

    available_hours = (
        snapshot_at - created_at
    ).total_seconds() / 3600

    response_hours = min(
        response_hours,
        available_hours * 0.75,
    )

    return created_at + timedelta(hours=max(response_hours, 0.001))


def make_resolution_timestamp(
    rng: random.Random,
    created_at: datetime,
    first_response_at: datetime | None,
    snapshot_at: datetime,
    severity: str,
) -> datetime | None:
    """Generate a resolution timestamp for resolved tickets."""

    target_hours = SLA_TARGETS[severity]["resolution_hours"]

    if rng.random() < 0.78:
        resolution_hours = target_hours * rng.uniform(0.20, 0.95)
    else:
        resolution_hours = target_hours * rng.uniform(1.05, 2.80)

    available_hours = (
        snapshot_at - created_at
    ).total_seconds() / 3600

    # Resolution must occur after first response.
    if first_response_at is not None:
        response_hours = (
            first_response_at - created_at
        ).total_seconds() / 3600

        minimum_resolution_hours = response_hours + 0.10
    else:
        minimum_resolution_hours = 0.10

    resolution_hours = min(
        max(resolution_hours, minimum_resolution_hours),
        available_hours * 0.95,
    )

    if resolution_hours <= 0:
        return None

    return created_at + timedelta(hours=resolution_hours)


def generate_description(
    rng: random.Random,
    category: str,
) -> str:
    """Choose a short synthetic ticket description."""

    return rng.choice(CATEGORIES[category])


# ---------------------------------------------------------
# TICKET GENERATION
# ---------------------------------------------------------

def generate_tickets(
    number_of_tickets: int = NUMBER_OF_TICKETS,
    seed: int = RANDOM_SEED,
    as_of: datetime = DEFAULT_AS_OF,
) -> list[dict[str, Any]]:

    rng = random.Random(seed)

    customer_tier_by_id = {
    customer_id: rng.choices(
        CUSTOMER_TIERS,
        weights=CUSTOMER_TIER_WEIGHTS,
        k=1,
    )[0]
    for customer_id in CUSTOMER_IDS
}

    tickets: list[dict[str, Any]] = []

    snapshot_at = as_of.astimezone(timezone.utc)

    for number in range(1, number_of_tickets + 1):

        ticket_id = f"TKT-{number:06d}"

        customer_id = rng.choice(CUSTOMER_IDS)

        category = rng.choice(list(CATEGORIES.keys()))

        severity = rng.choices(
            SEVERITIES,
            weights=SEVERITY_WEIGHTS,
            k=1,
        )[0]

        customer_tier = customer_tier_by_id[customer_id]

        impact_scope = choose_impact_scope(
            rng,
            severity,
        )

        channel = rng.choices(
            CHANNELS,
            weights=CHANNEL_WEIGHTS,
            k=1,
        )[0]

        # Ticket age ranges from 1 to 120 days.
        age_days = rng.uniform(1, 120)

        created_at = snapshot_at - timedelta(days=age_days)

        ticket_age_hours = (
            snapshot_at - created_at
        ).total_seconds() / 3600

        status = choose_status(
            rng,
            ticket_age_hours,
        )

        # Some active tickets have not yet been assigned.
        if status == "open" and rng.random() < 0.35:
            agent_id = None
        else:
            agent_id = rng.choice(AGENT_IDS)

        first_response_at = make_response_timestamp(
            rng,
            created_at,
            snapshot_at,
            severity,
        )

        resolved_at = None

        if status in {"resolved", "closed"}:
            resolved_at = make_resolution_timestamp(
                rng,
                created_at,
                first_response_at,
                snapshot_at,
                severity,
            )

            # A ticket cannot be resolved before it exists.
            if resolved_at is None:
                status = "in_progress"

        reopened_count = rng.choices(
            [0, 1, 2, 3, 4],
            weights=[72, 17, 7, 3, 1],
            k=1,
        )[0]

        # CSAT is collected only after resolution.
        if resolved_at is not None:
            csat_score = rng.choices(
                [1, 2, 3, 4, 5],
                weights=[5, 8, 17, 35, 35],
                k=1,
            )[0]

        else:
            csat_score = None

        relevant_timestamps = [
            created_at,
            first_response_at,
            resolved_at,
        ]

        updated_at = max(
            timestamp
            for timestamp in relevant_timestamps
            if timestamp is not None
        )

        ticket = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "customer_tier": customer_tier,
            "category": category,
            "severity": severity,
            "impact_scope": impact_scope,
            "channel": channel,
            "status": status,
            "description": generate_description(
                rng,
                category,
            ),
            "created_at": utc_iso(created_at),
            "updated_at": utc_iso(updated_at),
            "first_response_at": utc_iso(first_response_at),
            "resolved_at": utc_iso(resolved_at),
            "agent_id": agent_id or "",
            "reopened_count": reopened_count,
            "csat_score": csat_score if csat_score is not None else "",
            "snapshot_at": utc_iso(snapshot_at),
        }

        tickets.append(ticket)

    return tickets


# ---------------------------------------------------------
# CSV OUTPUT
# ---------------------------------------------------------

def save_tickets(
    tickets: list[dict[str, Any]],
    output_file: Path = OUTPUT_FILE,
) -> None:

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not tickets:
        raise ValueError("No tickets were generated.")

    columns = list(tickets[0].keys())

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=columns,
        )

        writer.writeheader()
        writer.writerows(tickets)

    print(f"\nGenerated {len(tickets):,} support tickets.")
    print(f"Output: {output_file}")

    status_counts: dict[str, int] = {}

    for ticket in tickets:
        status = ticket["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print("\nTicket status distribution:")

    for status, count in sorted(status_counts.items()):
        percentage = count / len(tickets) * 100

        print(
            f"  {status:<20} {count:>4,} "
            f"({percentage:.1f}%)"
        )


# ---------------------------------------------------------
# COMMAND LINE
# ---------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser(
        description="Generate synthetic support tickets."
    )

    parser.add_argument(
        "--count",
        type=int,
        default=NUMBER_OF_TICKETS,
        help="Number of tickets to generate.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Random seed for reproducibility.",
    )

    parser.add_argument(
        "--as-of",
        type=str,
        default=DEFAULT_AS_OF.isoformat(),
        help="Dataset snapshot timestamp in ISO-8601 format.",
    )

    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be greater than zero.")

    try:
        as_of = datetime.fromisoformat(
            args.as_of.replace("Z", "+00:00")
        )

        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)

    except ValueError as exc:
        parser.error(f"Invalid --as-of timestamp: {exc}")

    tickets = generate_tickets(
        number_of_tickets=args.count,
        seed=args.seed,
        as_of=as_of,
    )

    save_tickets(tickets)


if __name__ == "__main__":
    main()
