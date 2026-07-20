import os
import requests
import time

key     = os.environ.get("SPORTDB_API_KEY", "")
BASE    = "https://api.sportdb.dev/api"
headers = {"X-API-Key": key}


def get(endpoint):
    url = f"{BASE}{endpoint}"
    try:
        r = requests.get(
            url, headers=headers, timeout=15
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        return None


print("FINDING SPAIN GERMANY ITALY FRANCE BRAZIL IDs")
print("="*60)

countries = get("/flashscore/football")
if not countries:
    print("Failed to get countries")
    exit()

print(f"Total countries: {len(countries)}\n")

targets = [
    "spain", "germany", "italy", "france",
    "brazil", "argentina", "netherlands",
    "turkey", "belgium", "scotland",
    "mexico", "greece", "ukraine",
    "russia", "switzerland", "sweden",
    "denmark", "norway", "croatia",
    "serbia", "poland", "czechia",
    "czech-republic", "romania",
    "south-africa", "nigeria", "ghana",
    "egypt", "morocco", "japan",
    "south-korea", "china", "india",
    "saudi-arabia", "australia",
]

found = {}
for c in countries:
    slug = c.get("slug", "").lower()
    name = c.get("name", "").lower()
    cid  = c.get("id")

    for t in targets:
        if t in slug or t in name:
            found[t] = {
                "name": c.get("name"),
                "id":   cid,
                "slug": c.get("slug"),
            }
            break

print("FOUND COUNTRIES:")
for t, info in sorted(found.items()):
    print(
        f"  {t}: {info['name']} "
        f"(id:{info['id']}, slug:{info['slug']})"
    )

print("\nNOT FOUND:")
for t in targets:
    if t not in found:
        print(f"  {t}")

print("\nCHECKING COMPETITIONS FOR FOUND COUNTRIES:")
for t, info in sorted(found.items()):
    slug = info["slug"]
    cid  = info["id"]
    name = info["name"]

    comps = get(
        f"/flashscore/football/{slug}:{cid}"
    )
    if comps and isinstance(comps, list):
        print(f"\n  {name} ({slug}:{cid}):")
        for comp in comps[:5]:
            print(
                f"    {comp.get('name')} "
                f"id:{comp.get('id')}"
            )
    time.sleep(0.3)

print("\nDONE")
