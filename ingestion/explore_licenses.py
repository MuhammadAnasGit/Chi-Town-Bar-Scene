import duckdb

path = "C:/barscene-data/bronze/licenses/snapshot_date=2026-11-21/licenses.json"
con = duckdb.connect()
con.sql(f"CREATE VIEW lic AS SELECT * FROM read_json_auto('{path}')")

print("1. Columns")
con.sql("DESCRIBE lic").show(max_rows=50)

print("2. License types")
con.sql("SELECT license_description, COUNT(*) n FROM lic GROUP BY 1 ORDER BY n DESC").show()

print("3. License status")
con.sql("SELECT license_status, COUNT(*) n FROM lic GROUP BY 1 ORDER BY n DESC").show()

print("4. Application types")
con.sql("SELECT application_type, COUNT(*) n FROM lic GROUP BY 1 ORDER BY n DESC").show()

print("5. Rows vs. unique bar locations")
con.sql("""SELECT COUNT(*) AS rows,
       COUNT(DISTINCT account_number || '-' || site_number) AS unique_locations
FROM lic""").show()

print("6. New licenses issued per year")
con.sql("""SELECT year(try_cast(license_start_date AS TIMESTAMP)) AS yr, COUNT(*) AS new_licenses
FROM lic WHERE application_type = 'ISSUE'
GROUP BY 1 ORDER BY 1 DESC LIMIT 15""").show()

print("7. Sample rows")
con.sql("""SELECT doing_business_as_name, address, license_description, license_status,
       license_start_date, expiration_date
FROM lic LIMIT 5""").show()