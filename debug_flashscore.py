"""
Debug script to understand Flashscore API structure.
Run once to see what data we get.

print("\n[4b] GET /flashscore/football/matches")
data = get("/flashscore/football/matches")
if data:
    print(f"  Type: {type(data).__name__}")
    if isinstance(data, list):
        print(f"  Count: {len(data)}")
        if data:
            print(f"  ALL KEYS in first match:")
            print(f"  {list(data[0].keys())}")
            print(f"  Full first match:")
            print(json.dumps(data[0], indent=2)[:800])
    elif isinstance(data, dict):
        print(f"  Keys: {list(data.keys())}")
        # Try to find matches inside
        for k, v in data.items():
            if isinstance(v, list) and v:
                print(f"  Found list under '{k}': {len(v)} items")
                print(f"  First item keys: {list(v[0].keys()) if isinstance(v[0], dict) else v[0]}")

print("\n[4c] GET /flashscore/football/today")
data = get("/flashscore/football/today")
if data:
    print(f"  Type: {type(data).__name__}")
    if isinstance(data, list):
        print(f"  Count: {len(data)}")
        if data:
            print(f"  ALL KEYS in first match:")
            print(f"  {list(data[0].keys())}")
            print(f"  Full first match:")
            print(json.dumps(data[0], indent=2)[:800])
    elif isinstance(data, dict):
        print(f"  Keys: {list(data.keys())}")
        for k, v in data.items():
            if isinstance(v, list) and v:
                print(f"  Found list under '{k}': {len(v)} items")
                print(f"  First item keys: {list(v[0].keys()) if isinstance(v[0], dict) else v[0]}")

print("\n[4d] GET /flashscore/football/world:8")
data = get("/flashscore/football/world:8")
if data:
    print(f"  Type: {type(data).__name__}")
    if isinstance(data, list):
        print(f"  Count: {len(data)} competitions")
        for comp in data[:5]:
            print(f"  Comp: {json.dumps(comp)}")

        # Follow first competition link
        if data:
            first_link = data[0].get("link", "")
            if first_link:
                endpoint = first_link.replace("/api", "")
                print(f"\n  Following link: {first_link}")
                comp_data = get(endpoint)
                if comp_data:
                    print(f"  Comp data type: {type(comp_data).__name__}")
                    if isinstance(comp_data, list):
                        print(f"  Match count: {len(comp_data)}")
                        if comp_data:
                            print(f"  Match keys: {list(comp_data[0].keys())}")
                            print(f"  First match: {json.dumps(comp_data[0])[:500]}")
                    elif isinstance(comp_data, dict):
                        print(f"  Keys: {list(comp_data.keys())}")
                        
python debug_flashscore.py
"""

import os
import requests
import json
import time

key  = os.environ.get("SPORTDB_API_KEY", "")
BASE = "https://api.sportdb.dev/api"
headers = {"X-API-Key": key}


def get(endpoint):
    try:
        r = requests.get(
            f"{BASE}{endpoint}",
            headers=headers,
            timeout=15,
        )
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None


print("\n" + "="*60)
print("FLASHSCORE API STRUCTURE DEBUG")
print("="*60)

# STEP 1: Countries
print("\n[1] GET /flashscore/football")
countries = get("/flashscore/football")
if countries:
    print(f"  Type: {type(countries).__name__}")
    if isinstance(countries, list):
        print(f"  Count: {len(countries)}")
        print(f"  First item: {json.dumps(countries[0], indent=2)}")
        print(f"  Second item: {json.dumps(countries[1], indent=2)}")

        # Find England
        england = None
        for c in countries:
            name = c.get("name", "").lower()
            slug = c.get("slug", "").lower()
            if "england" in name or "england" in slug:
                england = c
                break

        # Find World
        world = None
        for c in countries:
            name = c.get("name", "").lower()
            slug = c.get("slug", "").lower()
            if "world" in name or "world" in slug or "international" in name:
                world = c
                break

        print(f"\n  England entry: {england}")
        print(f"  World/International entry: {world}")

    elif isinstance(countries, dict):
        print(f"  Keys: {list(countries.keys())}")
        print(f"  Content: {json.dumps(countries, indent=2)[:500]}")

time.sleep(1)

# STEP 2: Try England competitions
print("\n[2] GET /flashscore/football/england:1")
print("  (Testing England competitions)")
eng_comps = get("/flashscore/football/england:1")
if eng_comps:
    print(f"  Type: {type(eng_comps).__name__}")
    if isinstance(eng_comps, list):
        print(f"  Count: {len(eng_comps)}")
        if eng_comps:
            print(f"  First: {json.dumps(eng_comps[0], indent=2)}")
    elif isinstance(eng_comps, dict):
        print(f"  Keys: {list(eng_comps.keys())}")
        print(f"  Content: {json.dumps(eng_comps, indent=2)[:500]}")

time.sleep(1)

# STEP 3: Try the competitions URL from country object
if isinstance(countries, list) and countries:
    first = countries[0]
    comp_url = first.get("competitions", "")
    if comp_url:
        print(f"\n[3] GET {comp_url}")
        print(f"  (Using competitions URL from country object)")

        # Remove the /api prefix if present
        endpoint = comp_url.replace("/api", "")
        comp_data = get(endpoint)
        if comp_data:
            print(f"  Type: {type(comp_data).__name__}")
            if isinstance(comp_data, list):
                print(f"  Count: {len(comp_data)}")
                if comp_data:
                    print(
                        f"  First: "
                        f"{json.dumps(comp_data[0], indent=2)}"
                    )
            elif isinstance(comp_data, dict):
                print(f"  Keys: {list(comp_data.keys())}")
                print(
                    f"  Content: "
                    f"{json.dumps(comp_data, indent=2)[:500]}"
                )

time.sleep(1)

# STEP 4: Try matches endpoint
print("\n[4] Testing matches endpoints")
test_endpoints = [
    "/flashscore/football/england:1/matches",
    "/flashscore/football/matches",
    "/flashscore/football/today",
    "/flashscore/football/live",
    "/flashscore/matches",
    "/flashscore/football/events",
]

for ep in test_endpoints:
    print(f"\n  Testing: {ep}")
    data = get(ep)
    if data:
        print(f"    SUCCESS! Type: {type(data).__name__}")
        if isinstance(data, list):
            print(f"    Count: {len(data)}")
            if data:
                print(f"    First: {json.dumps(data[0])[:200]}")
        elif isinstance(data, dict):
            print(f"    Keys: {list(data.keys())}")
            print(f"    Content: {json.dumps(data)[:300]}")
    time.sleep(0.5)

# STEP 5: Check Transfermarkt too
print("\n[5] GET /transfermarkt/countries")
tm = get("/transfermarkt/countries")
if tm:
    print(f"  Type: {type(tm).__name__}")
    if isinstance(tm, list):
        print(f"  Count: {len(tm)}")
        print(f"  First 3: {tm[:3]}")

# STEP 6: Try different base paths
print("\n[6] Trying alternative base paths")
alt_endpoints = [
    "/flashscore",
    "/football",
    "/matches/today",
    "/events/today",
    "/fixtures",
    "/fixtures/today",
]

for ep in alt_endpoints:
    print(f"\n  Testing: {ep}")
    data = get(ep)
    if data:
        print(f"    SUCCESS! Type: {type(data).__name__}")
        if isinstance(data, list):
            print(f"    Count: {len(data)}")
        elif isinstance(data, dict):
            print(f"    Keys: {list(data.keys())[:5]}")

print("\n" + "="*60)
print("DEBUG COMPLETE")
print("="*60)
print("\nCopy this full output and send it.")
print("We will fix the integration based on results.")
