# SYSEN5493_requirements-traceability-checker
Systems engineering projects often track requirements in spreadsheets. Mistakes like duplicate requirement IDs, missing verification methods, missing parent links, or incomplete statuses can break traceability. This tool reads a CSV file of requirements, checks for common traceability problems, and prints a clean summary report.
# Requirements Traceability Checker

A small Python command-line tool that checks a CSV file of systems engineering requirements for common traceability and data-quality problems.

This project was built for SYSEN 5493 as a final project demonstrating AI-assisted coding, Git/GitHub workflow, testing, CI/CD, and responsible use of AI-generated code.

## Project Purpose

Systems engineering projects often track requirements in spreadsheets. Small errors can weaken traceability, including:

- Duplicate requirement IDs
- Missing requirement text
- Invalid status values
- Missing verification methods
- Parent requirements that do not exist

This tool reads a requirements CSV file, validates each row, and prints a clear quality report.

## Features

- Loads requirements from a CSV file
- Checks for duplicate requirement IDs
- Checks for blank requirement IDs
- Checks for missing requirement text
- Validates allowed status values
- Validates allowed verification methods
- Checks whether parent requirements actually exist
- Prints a readable summary report
- Includes automated tests with pytest
- Runs in GitHub Actions CI

## Project Structure

```text
requirements-traceability-checker/
├── README.md
├── requirements_checker.py
├── sample_requirements.csv
├── tests/
│   └── test_requirements_checker.py
└── .github/
    └── workflows/
        └── ci.yml