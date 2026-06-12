import sqlite3

conn = sqlite3.connect("worldbank.db")
cur = conn.cursor()

print("--- Database Verification ---")
print("Total rows:      ", cur.execute("SELECT COUNT(*) FROM indicators").fetchone()[0])
print("Distinct countries:", cur.execute("SELECT COUNT(DISTINCT country) FROM indicators").fetchone()[0])
print("Year range:      ", cur.execute("SELECT MIN(date), MAX(date) FROM indicators").fetchone())
print("Metadata rows:   ", cur.execute("SELECT COUNT(*) FROM country_metadata").fetchone()[0])

conn.close()