import sqlite3

print("=" * 60)
print("SQLITE VALIDATION")
print("=" * 60)

print("SQLite engine version      :", sqlite3.sqlite_version)
print("SQLite version tuple       :", sqlite3.sqlite_version_info)

conn = sqlite3.connect(":memory:")

print("Connection established     : PASS")

conn.close()

print("Connection closed          : PASS")
