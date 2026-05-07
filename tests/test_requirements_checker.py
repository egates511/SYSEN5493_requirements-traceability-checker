from __future__ import annotations

import csv
from pathlib import Path

import pytest

from requirements_checker import (
    RequirementsCheckerError,
    check_requirements,
    read_requirements,
)


HEADER = [
    "id",
    "parent_id",
    "text",
    "status",
    "verification_method",
    "priority",
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


def test_valid_requirements_have_no_issues(tmp_path: Path) -> None:
    csv_path = tmp_path / "valid.csv"
    write_csv(
        csv_path,
        [
            {
                "id": "REQ-001",
                "parent_id": "",
                "text": "System shall authenticate users.",
                "status": "approved",
                "verification_method": "test",
                "priority": "high",
            },
            {
                "id": "REQ-002",
                "parent_id": "REQ-001",
                "text": "System shall reject invalid passwords.",
                "status": "review",
                "verification_method": "inspection",
                "priority": "medium",
            },
        ],
    )

    requirements = read_requirements(csv_path)
    report = check_requirements(requirements)

    assert len(report.requirements) == 2
    assert report.status_counts["approved"] == 1
    assert report.status_counts["review"] == 1
    assert report.issues == []


def test_detects_blank_id_and_blank_text(tmp_path: Path) -> None:
    csv_path = tmp_path / "blank_fields.csv"
    write_csv(
        csv_path,
        [
            {
                "id": "",
                "parent_id": "",
                "text": "",
                "status": "draft",
                "verification_method": "test",
                "priority": "low",
            }
        ],
    )

    report = check_requirements(read_requirements(csv_path))

    assert any("id cannot be blank" in issue for issue in report.issues)
    assert any("text cannot be blank" in issue for issue in report.issues)


def test_detects_duplicate_ids(tmp_path: Path) -> None:
    csv_path = tmp_path / "duplicates.csv"
    write_csv(
        csv_path,
        [
            {
                "id": "REQ-001",
                "parent_id": "",
                "text": "First requirement.",
                "status": "draft",
                "verification_method": "test",
                "priority": "low",
            },
            {
                "id": "REQ-001",
                "parent_id": "",
                "text": "Duplicate requirement.",
                "status": "review",
                "verification_method": "inspection",
                "priority": "medium",
            },
        ],
    )

    report = check_requirements(read_requirements(csv_path))

    duplicate_issues = [issue for issue in report.issues if "id must be unique" in issue]
    assert len(duplicate_issues) == 2


def test_detects_invalid_status_and_verification_method(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid_values.csv"
    write_csv(
        csv_path,
        [
            {
                "id": "REQ-001",
                "parent_id": "",
                "text": "Bad enumerated values.",
                "status": "released",
                "verification_method": "simulation",
                "priority": "medium",
            }
        ],
    )

    report = check_requirements(read_requirements(csv_path))

    assert any("status must be one of" in issue for issue in report.issues)
    assert any("verification_method must be one of" in issue for issue in report.issues)


def test_detects_missing_parent_reference(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing_parent.csv"
    write_csv(
        csv_path,
        [
            {
                "id": "REQ-001",
                "parent_id": "REQ-999",
                "text": "Child requirement with missing parent.",
                "status": "approved",
                "verification_method": "analysis",
                "priority": "high",
            }
        ],
    )

    report = check_requirements(read_requirements(csv_path))

    assert any("does not reference an existing id" in issue for issue in report.issues)


def test_empty_file_raises_clear_error(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    with pytest.raises(RequirementsCheckerError, match="empty|no header"):
        read_requirements(csv_path)


def test_header_only_csv_raises_clear_error(tmp_path: Path) -> None:
    csv_path = tmp_path / "header_only.csv"
    csv_path.write_text(",".join(HEADER) + "\n", encoding="utf-8")

    with pytest.raises(RequirementsCheckerError, match="no requirement rows"):
        read_requirements(csv_path)


def test_missing_required_column_raises_clear_error(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing_column.csv"
    csv_path.write_text("id,text,status\nREQ-001,Some text,draft\n", encoding="utf-8")

    with pytest.raises(RequirementsCheckerError, match="missing required column"):
        read_requirements(csv_path)

"""Additional tests recommended by AI"""
def test_missing_file_raises_clear_error(tmp_path: Path) -> None:
    csv_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(RequirementsCheckerError, match="File not found"):
        read_requirements(csv_path)

def test_strips_whitespace_and_normalizes_allowed_values(tmp_path: Path) -> None:
    csv_path = tmp_path / "normalized.csv"
    write_csv(
        csv_path,
        [
            {
                "id": " REQ-001 ",
                "parent_id": "",
                "text": " Requirement text. ",
                "status": " Approved ",
                "verification_method": " TEST ",
                "priority": " high ",
            }
        ],
    )

    report = check_requirements(read_requirements(csv_path))

    assert report.issues == []
    assert report.requirements[0].req_id == "REQ-001"
    assert report.requirements[0].status == "approved"
    assert report.requirements[0].verification_method == "test"

"""End additional AI recommended tests"""
