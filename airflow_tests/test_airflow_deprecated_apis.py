"""
test_airflow_deprecated_apis.py
Documents Airflow 3.x API changes relevant to Python 3.15 migration.
These are Airflow version changes, not Python 3.15 incompatibilities.
"""
import sys
import warnings

print("=" * 60)
print("AIRFLOW DEPRECATED API DOCUMENTATION")
print("=" * 60)
print(f"Python  : {sys.version.split()[0]}")

import airflow
print(f"Airflow : {airflow.__version__}")
print()

changes = []

# 1. Operator paths moved to providers.standard
try:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from airflow.operators.python import PythonOperator
        from airflow.operators.bash import BashOperator
        warned = any("DeprecatedImportWarning" in str(x.category) for x in w)
    if warned:
        changes.append(("PythonOperator/BashOperator path",
                        "DEPRECATED",
                        "Use airflow.providers.standard.operators.* instead"))
    else:
        changes.append(("PythonOperator/BashOperator path", "OK", "No warning"))
except ImportError as e:
    changes.append(("PythonOperator/BashOperator path", "REMOVED", str(e)))

# 2. days_ago removed in Airflow 3.x
try:
    from airflow.utils.dates import days_ago
    changes.append(("airflow.utils.dates.days_ago", "OK", "Still present"))
except ImportError:
    changes.append(("airflow.utils.dates.days_ago",
                    "REMOVED",
                    "Use datetime.now() - timedelta(days=N) instead"))

# 3. New recommended operator path
try:
    from airflow.providers.standard.operators.python import PythonOperator
    from airflow.providers.standard.operators.bash import BashOperator
    changes.append(("providers.standard operators", "PASS", "Available"))
except ImportError as e:
    changes.append(("providers.standard operators", "FAIL", str(e)))

print("API Change Summary:")
for item, status, note in changes:
    print(f"  [{status:10}] {item}")
    print(f"              {note}")

print()
print("Migration guidance:")
print("  Old: from airflow.operators.python import PythonOperator")
print("  New: from airflow.providers.standard.operators.python import PythonOperator")
print()
print("  Old: from airflow.utils.dates import days_ago")
print("  New: from datetime import datetime, timedelta")
print("       start = datetime.now() - timedelta(days=1)")
print()
print("DEPRECATED API DOCUMENTATION: COMPLETE")
