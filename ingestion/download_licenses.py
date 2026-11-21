import json
from datetime import date
from pathlib import Path
import requests

URL = "https://data.cityofchicago.org/resource/r5kz-chrr.json"
WHERE = ("upper(license_description) like '%TAVERN%' "
         "OR upper(license_description) like '%LATE HOUR%' "
         "OR upper(license_description) like '%CONSUMPTION ON PREMISES%'")

out_dir = Path(r"C:\barscene-data\bronze\licenses") / f"snapshot_date={date.today()}"
out_dir.mkdir(parents=True, exist_ok=True)

rows, offset, limit = [], 0, 50000
while True:
    params = {"$where": WHERE, "$order": "id", "$limit": limit, "$offset": offset}
    resp = requests.get(URL, params=params, timeout=120)
    resp.raise_for_status()
    page = resp.json()
    rows.extend(page)
    print(f"Downloaded {len(rows)} rows")
    if len(page) < limit:
        break
    offset += limit

with open(out_dir / "licenses.json", "w", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")  # one row per line

print(f"Saved {len(rows)} rows to {out_dir / 'licenses.json'}")