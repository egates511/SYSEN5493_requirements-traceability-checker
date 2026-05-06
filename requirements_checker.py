"""Command-line tool for checking basic requirement traceability quality.

Usage:
    python requirements_checker.py sample_requirements.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Final


REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "id",
    "parent_id",
    "text",
    "status",
    "verification_method",
    "priority",
)

VALID_STATUSES: Final[set[str]] = {"draft", "review", "approved"}
VALID_VERIFICATION_METHODS: Final[set[str]] = {
    "test",
    "inspection",
    "analysis",
    "demonstration",
}


@dataclass(frozen=True)
class Requirement:
    """One requirement row from the input CSV."""

    row_number: int
    req_id: str
    parent_id: str
    text: str
    status: str
    verification_method: str
    priority: str


@dataclass(frozen=True)
class CheckReport:
    """Validation results for a requirements CSV file."""

    requirements: list[Requirement]
    status_counts: Counter[str]
    issues: list[str]


class RequirementsCheckerError(Exception):
    """Raised when the CSV cannot be checked."""


def normalize(value: str | None) -> str:
    """Return a stripped string for a possibly missing CSV value."""

    return "" if value is None else value.strip()


def read_requirements(csv_path: Path) -> list[Requirement]:
    """Read requirements from a CSV file and validate basic file structure."""

    if not csv_path.exists():
        raise RequirementsCheckerError(f"File not found: {csv_path}")

    try:
        with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise RequirementsCheckerError("CSV file is empty or has no header row.")

            missing_columns = [
                column for column in REQUIRED_COLUMNS if column not in reader.fieldnames
            ]
            if missing_columns:
                joined_columns = ", ".join(missing_columns)
                raise RequirementsCheckerError(
                    f"CSV file is missing required column(s): {joined_columns}"
                )

            requirements = [
                row_to_requirement(row_number, row)
                for row_number, row in enumerate(reader, start=2)
            ]
    except OSError as exc:
        raise RequirementsCheckerError(f"Could not read CSV file: {exc}") from exc
    except csv.Error as exc:
        raise RequirementsCheckerError(f"Invalid CSV file: {exc}") from exc

    if not requirements:
        raise RequirementsCheckerError("CSV file contains no requirement rows.")

    return requirements


def row_to_requirement(row_number: int, row: dict[str, str]) -> Requirement:
    """Convert one CSV dictionary row into a Requirement."""

    return Requirement(
        row_number=row_number,
        req_id=normalize(row.get("id")),
        parent_id=normalize(row.get("parent_id")),
        text=normalize(row.get("text")),
        status=normalize(row.get("status")).lower(),
        verification_method=normalize(row.get("verification_method")).lower(),
        priority=normalize(row.get("priority")),
    )


def check_requirements(requirements: list[Requirement]) -> CheckReport:
    """Run all quality checks against parsed requirements."""

    issues: list[str] = []
    ids = [requirement.req_id for requirement in requirements if requirement.req_id]
    id_counts = Counter(ids)
    existing_ids = set(ids)

    for requirement in requirements:
        issues.extend(check_required_fields(requirement))
        issues.extend(check_allowed_values(requirement))
        issues.extend(check_duplicate_id(requirement, id_counts))
        issues.extend(check_parent_reference(requirement, existing_ids))

    return CheckReport(
        requirements=requirements,
        status_counts=Counter(requirement.status for requirement in requirements),
        issues=issues,
    )


def check_required_fields(requirement: Requirement) -> list[str]:
    """Check fields that must not be blank."""

    issues: list[str] = []

    if not requirement.req_id:
        issues.append(f"Row {requirement.row_number}: id cannot be blank.")

    if not requirement.text:
        label = requirement.req_id or "<blank id>"
        issues.append(f"Row {requirement.row_number} ({label}): text cannot be blank.")

    return issues


def check_allowed_values(requirement: Requirement) -> list[str]:
    """Check fields constrained to known allowed values."""

    issues: list[str] = []
    label = requirement.req_id or "<blank id>"

    if requirement.status not in VALID_STATUSES:
        allowed = ", ".join(sorted(VALID_STATUSES))
        issues.append(
            f"Row {requirement.row_number} ({label}): "
            f"status must be one of: {allowed}. Found: {requirement.status!r}."
        )

    if requirement.verification_method not in VALID_VERIFICATION_METHODS:
        allowed = ", ".join(sorted(VALID_VERIFICATION_METHODS))
        issues.append(
            f"Row {requirement.row_number} ({label}): "
            f"verification_method must be one of: {allowed}. "
            f"Found: {requirement.verification_method!r}."
        )

    return issues


def check_duplicate_id(
    requirement: Requirement,
    id_counts: Counter[str],
) -> list[str]:
    """Check whether the requirement id appears more than once."""

    if requirement.req_id and id_counts[requirement.req_id] > 1:
        return [
            f"Row {requirement.row_number} ({requirement.req_id}): "
            "id must be unique."
        ]

    return []


def check_parent_reference(
    requirement: Requirement,
    existing_ids: set[str],
) -> list[str]:
    """Check that parent_id points to an existing requirement id when supplied."""

    if requirement.parent_id and requirement.parent_id not in existing_ids:
        label = requirement.req_id or "<blank id>"
        return [
            f"Row {requirement.row_number} ({label}): "
            f"parent_id {requirement.parent_id!r} does not reference an existing id."
        ]

    return []


def print_report(report: CheckReport) -> None:
    """Print a readable validation report to stdout."""

    total_requirements = len(report.requirements)

    print("Requirements Traceability Validation Report")
    print("=" * 44)
    print(f"Total requirements: {total_requirements}")
    print()

    print("Status counts:")
    for status in sorted(VALID_STATUSES):
        print(f"  {status}: {report.status_counts.get(status, 0)}")

    invalid_status_count = sum(
        count
        for status, count in report.status_counts.items()
        if status not in VALID_STATUSES
    )
    if invalid_status_count:
        print(f"  invalid/unknown: {invalid_status_count}")

    print()
    print("Issues found:")
    if not report.issues:
        print("  None. All checks passed.")
        return

    for index, issue in enumerate(report.issues, start=1):
        print(f"  {index}. {issue}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Check basic traceability quality for engineering requirements."
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to a requirements CSV file.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the requirements checker command-line interface."""

    args = parse_args()

    try:
        requirements = read_requirements(args.csv_file)
        report = check_requirements(requirements)
    except RequirementsCheckerError as exc:
        print(f"Error: {exc}")
        return 1

    print_report(report)
    return 1 if report.issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
