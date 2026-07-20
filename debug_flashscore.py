"""
Debug script - Full version with match field analysis.
Run this to see exact API structure.

python debug_flashscore.py
"""

import os
import requests
import json
import time

key  = os.environ.get("SPORTDB_API_KEY", "")
BASE = "https://api.sportdb.dev/api"
headers = {"X-API-Key": key}


def get(endpoint, use_full_url=False):
    url = endpoint if use_full_url else f"{BASE}{endpoint}"
    try:
        r = requests.get(
            url, headers=headers, timeout=15
        )
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  Error body: {r.text[:100]}")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None


print("\n" + "="*60)
print("FLASHSCORE FULL DEBUG - MATCH FIELDS")
print("="*60)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION A: /matches endpoint - MOST IMPORTANT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*60)
print("SECTION A: /flashscore/football/matches")
print("="*60)
data = get("/flashscore/football/matches")
if data:
    print(f"Response type: {type(data).__name__}")

    if isinstance(data, list):
        print(f"Total matches: {len(data)}")
        if data:
            first = data[0]
            print("\nALL FIELD NAMES:")
            print(list(first.keys()))
            print("\nFULL FIRST MATCH:")
            print(json.dumps(first, indent=2))
            if len(data) > 1:
                print("\nFULL SECOND MATCH:")
                print(json.dumps(data[1], indent=2))

    elif isinstance(data, dict):
        print(f"Dict keys: {list(data.keys())}")
        for k, v in data.items():
            print(f"\nKey '{k}':")
            if isinstance(v, list):
                print(f"  List with {len(v)} items")
                if v and isinstance(v[0], dict):
                    print(f"  First item keys: {list(v[0].keys())}")
                    print(f"  First item: {json.dumps(v[0], indent=2)}")
            else:
                print(f"  Value: {str(v)[:100]}")
else:
    print("NO DATA RETURNED")

time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION B: /today endpoint
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*60)
print("SECTION B: /flashscore/football/today")
print("="*60)
data = get("/flashscore/football/today")
if data:
    print(f"Response type: {type(data).__name__}")

    if isinstance(data, list):
        print(f"Total: {len(data)}")
        if data:
            first = data[0]
            print("\nALL FIELD NAMES:")
            print(list(first.keys()))
            print("\nFULL FIRST ITEM:")
            print(json.dumps(first, indent=2))

    elif isinstance(data, dict):
        print(f"Dict keys: {list(data.keys())}")
        for k, v in data.items():
            print(f"\nKey '{k}':")
            if isinstance(v, list):
                print(f"  List with {len(v)} items")
                if v and isinstance(v[0], dict):
                    print(
                        f"  First item keys: "
                        f"{list(v[0].keys())}"
                    )
                    print(
                        f"  First item: "
                        f"{json.dumps(v[0], indent=2)}"
                    )
            else:
                print(f"  Value: {str(v)[:100]}")
else:
    print("NO DATA RETURNED")

time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION C: /live endpoint - already working
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*60)
print("SECTION C: /flashscore/football/live")
print("="*60)
data = get("/flashscore/football/live")
if data:
    if isinstance(data, list):
        print(f"Live matches: {len(data)}")
        if data:
            first = data[0]
            print("\nALL FIELD NAMES:")
            print(list(first.keys()))
            print("\nFULL FIRST LIVE MATCH:")
            print(json.dumps(first, indent=2))
else:
    print("NO DATA")

time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION D: World competitions and matches
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*60)
print("SECTION D: World competitions (World Cup)")
print("="*60)
world_data = get("/flashscore/football/world:8")
if world_data:
    comps = world_data if isinstance(world_data, list) else []
    print(f"World competitions: {len(comps)}")
    for i, comp in enumerate(comps[:10]):
        print(f"\n  Competition {i+1}:")
        print(f"  {json.dumps(comp)}")

    if comps:
        print("\n  Following first competition link...")
        first_comp = comps[0]
        link = first_comp.get("link", "")
        print(f"  Link: {link}")

        if link:
            # Remove /api prefix
            endpoint = link.replace("/api", "")
            comp_result = get(endpoint)

            if comp_result:
                print(
                    f"\n  Competition result type: "
                    f"{type(comp_result).__name__}"
                )
                if isinstance(comp_result, list):
                    print(
                        f"  Items: {len(comp_result)}"
                    )
                    if comp_result:
                        print(
                            "\n  First item keys: "
                            f"{list(comp_result[0].keys())}"
                        )
                        print(
                            "\n  First item full: "
                            f"{json.dumps(comp_result[0], indent=2)}"
                        )
                elif isinstance(comp_result, dict):
                    print(
                        f"  Dict keys: "
                        f"{list(comp_result.keys())}"
                    )
                    print(
                        f"  Content: "
                        f"{json.dumps(comp_result, indent=2)[:500]}"
                    )

        time.sleep(1)

        # Try the second competition too
        if len(comps) > 1:
            print("\n  Following second competition link...")
            second_comp = comps[1]
            link2 = second_comp.get("link", "")
            print(f"  Link: {link2}")
            if link2:
                endpoint2 = link2.replace("/api", "")
                result2 = get(endpoint2)
                if result2:
                    if isinstance(result2, list):
                        print(
                            f"  Items: {len(result2)}"
                        )
                        if result2:
                            print(
                                f"  Keys: "
                                f"{list(result2[0].keys())}"
                            )
                            print(
                                f"  First: "
                                f"{json.dumps(result2[0], indent=2)[:400]}"
                            )
                    elif isinstance(result2, dict):
                        print(
                            f"  Dict: "
                            f"{json.dumps(result2)[:400]}"
                        )

time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION E: England competitions and matches
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*60)
print("SECTION E: England competitions")
print("="*60)
eng_data = get("/flashscore/football/england:198")
if eng_data:
    comps = (
        eng_data if isinstance(eng_data, list)
        else []
    )
    print(f"England competitions: {len(comps)}")
    for comp in comps[:5]:
        print(f"  {json.dumps(comp)}")

    if comps:
        print("\n  Following first England comp link...")
        link = comps[0].get("link", "")
        if link:
            endpoint = link.replace("/api", "")
            result = get(endpoint)
            if result:
                if isinstance(result, list):
                    print(f"  Items: {len(result)}")
                    if result:
                        print(
                            f"  Keys: "
                            f"{list(result[0].keys())}"
                        )
                        print(
                            f"  First: "
                            f"{json.dumps(result[0], indent=2)[:500]}"
                        )
                elif isinstance(result, dict):
                    print(
                        f"  Dict keys: "
                        f"{list(result.keys())}"
                    )
                    print(
                        f"  Content: "
                        f"{json.dumps(result)[:400]}"
                    )


print("\n" + "="*60)
print("DEBUG COMPLETE - Send this full output")
print("="*60)
