import os
import requests
import json
import time

key     = os.environ.get("SPORTDB_API_KEY", "")
BASE    = "https://api.sportdb.dev/api"
headers = {"X-API-Key": key}


def get(endpoint):
    url = f"{BASE}{endpoint}"
    if endpoint.startswith("/api/"):
        url = f"{BASE}{endpoint[4:]}"
    try:
        r = requests.get(
            url, headers=headers, timeout=15
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


print("FINDING COMPETITION IDS FOR ALL LEAGUES\n")

targets = [
    ("world",       8),
    ("england",     198),
    ("spain",       45),
    ("germany",     78),
    ("italy",       102),
    ("france",      74),
    ("netherlands", 130),
    ("portugal",    155),
    ("brazil",      32),
    ("argentina",   11),
    ("turkey",      186),
    ("belgium",     24),
    ("scotland",    166),
    ("usa",         200),
    ("mexico",      119),
]

for slug, cid in targets:
    print(f"\n{'='*50}")
    print(f"COUNTRY: {slug} (id:{cid})")
    print(f"{'='*50}")

    comps = get(f"/flashscore/football/{slug}:{cid}")
    if comps and isinstance(comps, list):
        for comp in comps[:15]:
            cname = comp.get("name", "?")
            cslug = comp.get("slug", "?")
            cid2  = comp.get("id", "?")
            link  = comp.get("link", "?")
            print(f"  NAME: {cname}")
            print(f"  SLUG: {cslug}")
            print(f"  ID:   {cid2}")
            print(f"  LINK: {link}")
            print()
    else:
        print(f"  No competitions found")
    time.sleep(0.5)

print("\nDONE")
