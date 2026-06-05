# PyArrow Test Result

Date: 2026-06-05

Environment:
- Python 3.15.0b1
- macOS ARM64
- uv-managed venv

Result:
FAIL

Reason:
No cp315 wheel available.

Source build attempted.

Build stopped during CMake configuration:

ArrowConfig.cmake not found

Conclusion:
PyArrow remains incompatible with Python 3.15 as of this test.

Status:
Known ecosystem blocker.
