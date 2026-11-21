import duckdb
from pathlib import Path

src = "C:/barscene-data/bronze/licenses/snapshot_date=*/licenses.json"
out = "C:/barscene-data/silver/bars.parquet"

con = duckdb.connect()
Path(out).parent.mkdir(parents=True, exist_ok=True)  # create the silver folder if missing
con.sql(f"""
CREATE OR REPLACE TABLE lic AS
SELECT
  account_number || '-' || site_number               AS bar_id,
  trim(doing_business_as_name)                       AS bar_name,
  trim(address)                                      AS address,
  zip_code, community_area_name, neighborhood,
  license_description, license_status,
  CAST(try_cast(license_start_date AS TIMESTAMP) AS DATE) AS start_date,
  CAST(try_cast(expiration_date   AS TIMESTAMP) AS DATE) AS end_date,
  try_cast(latitude  AS DOUBLE) AS lat,
  try_cast(longitude AS DOUBLE) AS lng
FROM read_json_auto('{src}')
WHERE snapshot_date = (SELECT max(snapshot_date) FROM read_json_auto('{src}'))
  AND license_description <> 'Laundry, Late Hour'
""")

con.sql("""
CREATE OR REPLACE TABLE bars AS
SELECT
  bar_id,
  arg_max(bar_name, end_date)            AS bar_name,
  arg_max(address, end_date)             AS address,
  arg_max(zip_code, end_date)            AS zip_code,
  arg_max(community_area_name, end_date) AS community_area,
  arg_max(neighborhood, end_date)        AS neighborhood,
  arg_max(lat, end_date)                 AS lat,
  arg_max(lng, end_date)                 AS lng,
  CASE WHEN bool_or(license_description = 'Tavern') THEN 'Bar / Tavern'
       ELSE 'Restaurant with alcohol' END AS venue_type,
  bool_or(license_description = 'Late Hour' AND end_date >= current_date) AS open_late,
  min(start_date)                        AS first_licensed,
  max(end_date)                          AS license_expires,
  bool_or(license_status = 'REV')        AS ever_revoked,
  (max(end_date) >= current_date
   AND arg_max(license_status, end_date) = 'AAI') AS is_open
FROM lic
GROUP BY bar_id
""")

con.sql(f"COPY bars TO '{out}' (FORMAT parquet)")

print("Bars per status and type:")
con.sql("""SELECT venue_type, is_open, COUNT(*) AS bars
FROM bars GROUP BY ALL ORDER BY venue_type, is_open DESC""").show()

print("Top 10 neighborhoods by open bars and taverns:")
con.sql("""SELECT community_area, COUNT(*) AS open_bars,
       SUM(CASE WHEN open_late THEN 1 ELSE 0 END) AS open_late
FROM bars WHERE is_open AND venue_type = 'Bar / Tavern'
GROUP BY 1 ORDER BY open_bars DESC LIMIT 10""").show()

print(f"Saved clean table to {out}")
