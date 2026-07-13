#!/usr/bin/env python3
"""
validate_dataeng_stack.py

Validate the production Data Engineering reference stack and display
package versions with colorized output.


Compatibility Markers:
    Author: Dr. Ceasar Jackson Jr.
    Purpose: Validate the Python 3.15 data-engineering package stack and report compatibility results.
    Validation: python -m py_compile scripts/validate_dataeng_stack.py; python scripts/validate_dataeng_stack.py --help
"""

from importlib.metadata import PackageNotFoundError, version

GREEN = "\033[0;32m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
RESET = "\033[0m"

PACKAGES = [
    "polars",
    "duckdb",
    "pyarrow",
    "pandas",
    "numpy",
    "orjson",
    "msgspec",
    "rapidfuzz",
    "sqlglot",
    "great_expectations",
    "pydantic",
    "pydantic_settings",
    "structlog",
    "rich",
    "typer",
    "watchfiles",
    "pendulum",
]

print(f"{CYAN}=== Data Engineering Stack Validation ==={RESET}")

for package in PACKAGES:
    try:
        __import__(package)
        try:
            pkg_version = version(package.replace("_", "-"))
        except PackageNotFoundError:
            pkg_version = "installed"

        print(f"{GREEN}✅ {package:<20} {pkg_version}{RESET}")

    except Exception as exc:
        print(f"{RED}❌ {package:<20} {exc}{RESET}")
