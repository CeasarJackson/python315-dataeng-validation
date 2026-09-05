# Python 3.15.0rc2 Validation Runbook

**Project:** Python 3.15 Data Engineering Validation Suite  
**Purpose:** Execute a clean, reproducible Python 3.15.0rc2 compatibility cycle without contaminating the validated RC1 baseline.

---

## 1. Preconditions

Do not begin RC2 validation until Python 3.15.0rc2 is actually available.

Check:

```bash
uv python list | grep '3\.15\.0rc2'
