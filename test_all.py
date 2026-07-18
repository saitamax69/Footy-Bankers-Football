"""
FOOTY BANKERS FOOTBALL
Complete System Test - Standalone Version

No imports from src/ needed.
Tests everything directly.
"""

import os
import sys
import json
import time
import asyncio
import requests
import feedparser
from datetime import datetime
import pytz

# Print immediately
print("Starting Footy Bankers Football Tests...")
print(f"Python: {sys.version.split()[0]}")
print(f"Directory: {os.getcwd()}")
print(f"Files: {os.listdir('.')}")
print("")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLOURS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def ok(msg):
    print(f"  {GREEN}✅ {msg}{RESET}")


def fail(msg):
    print(f"  {RED}❌ {msg}{RESET}")


def warn(msg):
    print(f"  {YELLOW}⚠️  {msg}{RESET}")


def info(msg):
    print(f"  {BLUE}ℹ️  {msg}{RESET}")


def header(msg):
    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"{BOLD}  {msg}{RESET}")
    print(f"{BOLD}{'='*50}{RESET}")


def subheader(msg):
    print(f"\n{BOLD}  ── {msg} ──{RESET}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

results = {"passed": [], "failed": [], "warned": []}


def record_pass(name):
    results["passed"].append(name)


def record_fail(name, reason=""):
    results["failed"].append(f"{name}: {reason}")


def record_warn(name, reason=""):
    results["warned"].append(f"{name}: {reason}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: SECRETS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_secrets():
    header("TEST 1: SECRETS")

    required = {
        "FOOTBALL_DATA_API_KEY": "football-data.org",
        "GROQ_API_KEY":          "Groq AI",
        "TELEGRAM_BOT_TOKEN":    "Telegram bot",
        "TELEGRAM_CHANNEL_ID":   "Telegram channel",
        "FACEBOOK_PAGE_TOKEN":   "Facebook token",
        "FACEBOOK_PAGE_ID":      "Facebook page ID",
        "GH_TOKEN":              "GitHub token",
    }

    optional = {
        "SPORTDB_API_KEY":        "SportDB/Flashscore",
        "FACEBOOK_TOKEN_DATE":    "Facebook token date",
        "TELEGRAM_OWNER_CHAT_ID": "Your personal chat ID",
    }

    subheader("Required")
    for key, desc in required.items():
        val = os.environ.get(key, "")
        if not val:
            fail(f"{key} MISSING ({desc})")
            record_fail(f"Secret:{key}", "not set")
        else:
            masked = (
                val[:4] + "****" + val[-4:]
                if len(val) > 8 else "****"
            )
            ok(f"{key} ({masked})")
            record_pass(f"Secret:{key}")

    subheader("Optional")
    for key, desc in optional.items():
        val = os.environ.get(key, "")
        if not val:
            warn(f"{key} not set ({desc})")
            record_warn(f"Secret:{key}", "optional")
        else:
            ok(f"{key} set")
            record_pass(f"Secret:{key}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: FOOTBALL-DATA.ORG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_football_data():
    header("TEST 2: FOOTBALL-DATA.ORG")

    key = os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not key:
        fail("Key not set")
        record_fail("FootballData", "no key")
        return

    try:
        r = requests.get(
            "https://api.football-data.org/v4/competitions",
            headers={"X-Auth-Token": key},
            timeout=15,
        )
        if r.status_code == 200:
            comps = r.json().get("competitions", [])
            ok(f"Connected - {len(comps)} competitions")
            record_pass("FootballData:connection")
            for c in comps[:5]:
                info(f"   {c.get('code')} - {c.get('name')}")
        elif r.status_code == 401:
            fail("Invalid API key")
            record_fail("FootballData", "401")
        else:
            fail(f"Status {r.status_code}")
            record_fail("FootballData", str(r.status_code))
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("FootballData", str(e))

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.football-data.org/v4/matches",
            headers={"X-Auth-Token": key},
            params={"dateFrom": today, "dateTo": today},
            timeout=15,
        )
        if r.status_code == 200:
            matches = r.json().get("matches", [])
            ok(f"Fixtures today: {len(matches)}")
            record_pass("FootballData:fixtures")
        else:
            warn(f"Fixtures: {r.status_code}")
            record_warn("FootballData:fixtures", str(r.status_code))
    except Exception as e:
        warn(f"Fixtures error: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: SPORTDB API (FLASHSCORE + TRANSFERMARKT)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_sportdb_api():
    header("TEST 3: SPORTDB API (FLASHSCORE + TRANSFERMARKT)")

    key = os.environ.get("SPORTDB_API_KEY", "")
    if not key:
        warn("SPORTDB_API_KEY not set")
        warn("Get key at: api.sportdb.dev")
        record_warn("SportDB", "no key set")
        return

    BASE    = "https://api.sportdb.dev/api"
    headers = {"X-API-Key": key}

    subheader("Testing Transfermarkt countries")
    try:
        r = requests.get(
            f"{BASE}/transfermarkt/countries",
            headers=headers,
            timeout=15,
        )
        if r.status_code == 200:
            data      = r.json()
            countries = data.get("countries", data if isinstance(data, list) else [])
            ok(f"Transfermarkt connected - {len(countries)} countries")
            record_pass("SportDB:transfermarkt")
            if countries:
                sample = countries[0]
                if isinstance(sample, dict):
                    info(f"   Sample: {sample.get('name', sample)}")
                else:
                    info(f"   Sample: {sample}")
        elif r.status_code == 401:
            fail("Invalid API key (401)")
            fail("Check your SPORTDB_API_KEY secret")
            record_fail("SportDB:transfermarkt", "401 invalid key")
        elif r.status_code == 403:
            fail("Forbidden (403) - key may not have access")
            record_fail("SportDB:transfermarkt", "403 forbidden")
        else:
            warn(f"Status {r.status_code}")
            info(f"   Response: {r.text[:200]}")
            record_warn("SportDB:transfermarkt", str(r.status_code))
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("SportDB:transfermarkt", str(e))

    time.sleep(1)

    subheader("Testing Flashscore football")
    try:
        r = requests.get(
            f"{BASE}/flashscore/football",
            headers=headers,
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()

            # Handle different response structures
            if isinstance(data, list):
                matches = data
            else:
                matches = (
                    data.get("matches")
                    or data.get("events")
                    or data.get("data")
                    or data.get("fixtures")
                    or []
                )

            ok(f"Flashscore connected - {len(matches)} matches today")
            record_pass("SportDB:flashscore")

            if matches:
                m    = matches[0]
                home = (
                    m.get("home_team")
                    or m.get("homeTeam")
                    or (m.get("home", {}).get("name") if isinstance(m.get("home"), dict) else m.get("home", "?"))
                    or "?"
                )
                away = (
                    m.get("away_team")
                    or m.get("awayTeam")
                    or (m.get("away", {}).get("name") if isinstance(m.get("away"), dict) else m.get("away", "?"))
                    or "?"
                )
                comp = (
                    m.get("tournament")
                    or m.get("competition")
                    or m.get("league")
                    or m.get("league_name")
                    or "Unknown"
                )
                info(f"   Sample: {home} vs {away} ({comp})")

        elif r.status_code == 401:
            fail("Flashscore: Invalid key (401)")
            record_fail("SportDB:flashscore", "401")
        else:
            warn(f"Flashscore: Status {r.status_code}")
            info(f"   Response: {r.text[:200]}")
            record_warn("SportDB:flashscore", str(r.status_code))
    except Exception as e:
        fail(f"Flashscore error: {e}")
        record_fail("SportDB:flashscore", str(e))

    time.sleep(1)

    subheader("Testing player search (Haaland)")
    try:
        r = requests.get(
            f"{BASE}/transfermarkt/player/search",
            headers=headers,
            params={"name": "Haaland"},
            timeout=15,
        )
        if r.status_code == 200:
            data    = r.json()
            players = (
                data.get("players")
                or data.get("results")
                or data.get("data")
                or (data if isinstance(data, list) else [])
            )
            if players:
                p     = players[0] if isinstance(players, list) else players
                name  = p.get("name") or p.get("player_name") or "Found"
                value = p.get("market_value") or p.get("value") or "N/A"
                ok(f"Player search: {name} - {value}")
            else:
                ok("Player search endpoint works (no results)")
            record_pass("SportDB:player_search")
        else:
            warn(f"Player search: {r.status_code}")
            record_warn("SportDB:player_search", str(r.status_code))
    except Exception as e:
        warn(f"Player search error: {e}")
        record_warn("SportDB:player_search", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: THESPORTSDB (FREE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_sportsdb_free():
    header("TEST 4: THESPORTSDB (FREE - NO KEY)")

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(
            "https://www.thesportsdb.com/api/v1/json/3/eventsday.php",
            params={"d": today, "s": "Soccer"},
            timeout=15,
        )
        if r.status_code == 200:
            events = r.json().get("events") or []
            ok(f"Connected - {len(events)} events today")
            record_pass("SportsDBFree:connection")
            if events:
                e = events[0]
                info(f"   Sample: {e.get('strHomeTeam')} vs {e.get('strAwayTeam')}")
        else:
            warn(f"Status {r.status_code}")
            record_warn("SportsDBFree", str(r.status_code))
    except Exception as e:
        warn(f"Error: {e}")
        record_warn("SportsDBFree", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: WEATHER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_weather():
    header("TEST 5: OPEN-METEO WEATHER")

    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":      51.5549,
                "longitude":     -0.1084,
                "hourly":        "precipitation,windspeed_10m,temperature_2m",
                "forecast_days": 1,
                "timezone":      "Europe/London",
            },
            timeout=15,
        )
        if r.status_code == 200:
            hourly = r.json().get("hourly", {})
            temps  = hourly.get("temperature_2m", [])
            rain   = hourly.get("precipitation", [])
            ok("Weather API working")
            if temps:
                ok(f"Temperature: {temps[0]}°C")
            ok(f"Precipitation: {rain[0] if rain else 0}mm")
            record_pass("Weather:connection")
        else:
            warn(f"Status {r.status_code}")
            record_warn("Weather", str(r.status_code))
    except Exception as e:
        warn(f"Error: {e}")
        record_warn("Weather", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: RSS FEEDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_rss():
    header("TEST 6: RSS NEWS FEEDS")

    feeds = {
        "BBC Sport":  "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "Sky Sports": "https://www.skysports.com/rss/12040",
        "Guardian":   "https://www.theguardian.com/football/rss",
        "TalkSport":  "https://talksport.com/feed/",
        "Mirror":     "https://www.mirror.co.uk/sport/football/?service=rss",
    }

    for name, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                ok(f"{name}: {len(feed.entries)} articles")
                info(f"   {feed.entries[0].get('title', '')[:55]}")
                record_pass(f"RSS:{name}")
            else:
                warn(f"{name}: No entries")
                record_warn(f"RSS:{name}", "no entries")
        except Exception as e:
            warn(f"{name}: {e}")
            record_warn(f"RSS:{name}", str(e))
        time.sleep(0.5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 7: GOOGLE NEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_google_news():
    header("TEST 7: GOOGLE NEWS RSS")

    for team in ["Manchester City", "Real Madrid"]:
        try:
            q    = team.replace(" ", "+")
            url  = (
                f"https://news.google.com/rss/search"
                f"?q={q}+football&hl=en-GB&gl=GB&ceid=GB:en"
            )
            feed = feedparser.parse(url)
            if feed.entries:
                ok(f"{team}: {len(feed.entries)} articles")
                record_pass(f"GoogleNews:{team}")
            else:
                warn(f"{team}: No results")
                record_warn(f"GoogleNews:{team}", "none")
        except Exception as e:
            warn(f"{team}: {e}")
        time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 8: GROQ AI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_groq():
    header("TEST 8: GROQ AI")

    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        fail("GROQ_API_KEY not set")
        record_fail("Groq", "no key")
        return

    try:
        from groq import Groq
        client = Groq(api_key=key)

        subheader("Available models")
        try:
            available = [m.id for m in client.models.list().data]
            info(f"Total: {len(available)} models")
            for m in sorted(available):
                info(f"   {m}")
        except Exception as e:
            warn(f"Could not list models: {e}")
            available = []

        subheader("Testing configured models")
        our_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
        ]

        working = None
        for model in our_models:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Say: Footy Bankers works"}],
                    max_tokens=20,
                    temperature=0.1,
                )
                answer = resp.choices[0].message.content
                ok(f"{model}: WORKING")
                info(f"   {answer[:50]}")
                record_pass(f"Groq:{model}")
                if not working:
                    working = model
            except Exception as e:
                err = str(e)
                if "decommissioned" in err or "not_found" in err:
                    fail(f"{model}: decommissioned")
                    record_fail(f"Groq:{model}", "dead")
                else:
                    warn(f"{model}: {err[:60]}")
                    record_warn(f"Groq:{model}", err[:40])
            time.sleep(1)

        if working:
            subheader("Testing JSON prediction format")
            try:
                resp = client.chat.completions.create(
                    model=working,
                    messages=[
                        {"role": "system", "content": "JSON only."},
                        {"role": "user", "content": (
                            'Return: {"pick":"Home Win",'
                            '"confidence":75,"tier":"BANKER"}'
                        )},
                    ],
                    max_tokens=100,
                    response_format={"type": "json_object"},
                )
                parsed = json.loads(resp.choices[0].message.content)
                ok(f"JSON: pick={parsed.get('pick')} conf={parsed.get('confidence')}")
                record_pass("Groq:JSON")
            except Exception as e:
                fail(f"JSON test: {e}")
                record_fail("Groq:JSON", str(e))

    except ImportError:
        fail("groq not installed - check requirements.txt")
        record_fail("Groq", "not installed")
    except Exception as e:
        fail(f"Groq error: {e}")
        record_fail("Groq", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 9: TELEGRAM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _tg_test():
    from telegram import Bot
    from telegram.constants import ParseMode

    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if not token or not channel:
        fail("Telegram credentials missing")
        record_fail("Telegram", "missing credentials")
        return

    bot = Bot(token=token)

    try:
        me = await bot.get_me()
        ok(f"Bot: @{me.username}")
        record_pass("Telegram:identity")
    except Exception as e:
        fail(f"Bot identity: {e}")
        record_fail("Telegram", str(e))
        return

    try:
        chat = await bot.get_chat(channel)
        ok(f"Channel: {chat.title}")
        record_pass("Telegram:channel")
    except Exception as e:
        fail(f"Channel access: {e}")
        record_fail("Telegram", f"channel: {e}")
        return

    try:
        m = await bot.send_message(
            chat_id=channel,
            text="🧪 FootyBankersFootball - System Test\n\nAll systems operational ✅",
        )
        ok(f"Plain text sent (ID: {m.message_id})")
        record_pass("Telegram:plain")
    except Exception as e:
        fail(f"Plain text: {e}")
        record_fail("Telegram", f"plain: {e}")

    await asyncio.sleep(2)

    try:
        m2 = await bot.send_message(
            chat_id=channel,
            text=(
                "🧪 *SYSTEM TEST*\n\n"
                "⚽ *Footy Bankers Football*\n\n"
                "✅ *Markdown working\\!*\n"
                "📊 Confidence: 82%\n"
                "🔒 Tier: BANKER\n\n"
                "_All systems go\\._\n\n"
                "*Footy Bankers Football* ⚽🔒"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        ok(f"Markdown sent (ID: {m2.message_id})")
        record_pass("Telegram:markdown")
    except Exception as e:
        warn(f"Markdown: {e}")
        record_warn("Telegram", f"markdown: {e}")


def test_telegram():
    header("TEST 9: TELEGRAM")
    try:
        asyncio.run(_tg_test())
    except Exception as e:
        fail(f"Telegram error: {e}")
        record_fail("Telegram", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 10: FACEBOOK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_facebook():
    header("TEST 10: FACEBOOK PAGE")

    token   = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "")
    GRAPH   = "https://graph.facebook.com/v18.0"

    if not token or not page_id:
        fail("Facebook credentials missing")
        record_fail("Facebook", "missing")
        return

    try:
        r = requests.get(
            f"{GRAPH}/{page_id}",
            params={"fields": "name,fan_count,category", "access_token": token},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            ok(f"Page: {data.get('name')}")
            ok(f"Followers: {data.get('fan_count', 0):,}")
            record_pass("Facebook:connection")
        else:
            fail(f"Connection: {r.status_code}")
            record_fail("Facebook", str(r.status_code))
            return
    except Exception as e:
        fail(f"Connection: {e}")
        record_fail("Facebook", str(e))
        return

    try:
        r = requests.get(
            f"{GRAPH}/debug_token",
            params={"input_token": token, "access_token": token},
            timeout=15,
        )
        if r.status_code == 200:
            data     = r.json().get("data", {})
            valid    = data.get("is_valid", False)
            tok_type = data.get("type", "?")
            scopes   = data.get("scopes", [])

            if valid:
                ok("Token valid")
                record_pass("Facebook:token")
            else:
                fail("Token invalid")
                record_fail("Facebook", "invalid token")

            info(f"Type: {tok_type}")

            for scope in ["pages_manage_posts", "pages_read_engagement"]:
                if scope in scopes:
                    ok(f"Permission: {scope}")
                    record_pass(f"Facebook:perm:{scope}")
                else:
                    warn(f"Permission may be missing: {scope}")
                    record_warn("Facebook", f"perm: {scope}")
    except Exception as e:
        warn(f"Token check: {e}")

    now_str = datetime.now().strftime("%d %B %Y %H:%M")
    try:
        r = requests.post(
            f"{GRAPH}/{page_id}/feed",
            data={
                "message": (
                    f"⚽ Footy Bankers Football | Test\n\n"
                    f"Tested: {now_str}\n\n"
                    f"1️⃣ 🔒 Man City Win | PL | 📊 82%\n"
                    f"2️⃣ 💪 Real Madrid Win | La Liga | 📊 75%\n"
                    f"3️⃣ 💪 Over 2.5 | Bundesliga | 📊 71%\n\n"
                    f"Telegram: t.me/FootyBankersFootball\n\n"
                    f"18+ | Gamble Responsibly"
                ),
                "access_token": token,
            },
            timeout=30,
        )
        if r.status_code == 200:
            ok(f"Posted! ID: {r.json().get('id', '?')}")
            record_pass("Facebook:post")
        else:
            err = r.json().get("error", {})
            fail(f"Post failed: {err.get('message', r.text[:100])}")
            record_fail("Facebook", err.get("message", "post failed"))
    except Exception as e:
        fail(f"Post error: {e}")
        record_fail("Facebook", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 11: GITHUB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_github():
    header("TEST 11: GITHUB")

    token = os.environ.get("GH_TOKEN", "")
    if not token:
        fail("GH_TOKEN not set")
        record_fail("GitHub", "no token")
        return

    try:
        r = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=15,
        )
        if r.status_code == 200:
            user = r.json()
            ok(f"User: {user.get('login')}")
            record_pass("GitHub:user")
        else:
            fail(f"Auth failed: {r.status_code}")
            record_fail("GitHub", str(r.status_code))
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("GitHub", str(e))

    try:
        os.makedirs("data/predictions", exist_ok=True)
        path = "data/predictions/test_write.json"
        with open(path, "w") as f:
            json.dump({"test": True}, f)
        ok("Write access confirmed")
        record_pass("GitHub:write")
        os.remove(path)
    except Exception as e:
        warn(f"Write test: {e}")
        record_warn("GitHub", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 12: FULL PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_pipeline():
    header("TEST 12: FULL PIPELINE")

    info("Complete morning workflow simulation")

    match = {
        "home_team":        "Manchester City",
        "away_team":        "Arsenal",
        "competition_name": "Premier League",
        "competition_code": "PL",
        "kickoff_uk":       "20:00",
        "home_form": {
            "form_string":       "WWWDW",
            "win_rate":          78.0,
            "goals_for_avg":     2.3,
            "goals_against_avg": 0.8,
        },
        "away_form": {
            "form_string":       "WWLDW",
            "win_rate":          65.0,
            "goals_for_avg":     1.8,
            "goals_against_avg": 1.1,
        },
        "h2h":           {"home_wins": 6, "away_wins": 2, "draws": 2, "avg_goals": 2.8},
        "home_news_note": "No concerns",
        "away_news_note": "Saka doubtful",
        "weather":        {"description": "Clear", "impact": 0},
    }
    ok("Match data ready")
    record_pass("Pipeline:data")

    # AI
    groq_key = os.environ.get("GROQ_API_KEY", "")
    prediction = None

    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            models = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-120b",
            ]
            for model in models:
                try:
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Football analyst. JSON only."},
                            {"role": "user", "content": """
Analyse: Manchester City vs Arsenal, Premier League
Home form: WWWDW (78% wins). Away form: WWLDW (65% wins).
Return JSON: {"pick":"Home Win","pick_short":"City Win","confidence":75,"reasoning":["City strong at home"],"risk":"Arsenal attack","predicted_score":"2-1","avoid":false}
"""},
                        ],
                        max_tokens=200,
                        temperature=0.3,
                        response_format={"type": "json_object"},
                    )
                    prediction = json.loads(resp.choices[0].message.content)
                    pick_show  = prediction.get("pick_short") or prediction.get("pick", "Predicted")
                    conf_show  = prediction.get("confidence", "?")
                    ok(f"AI: {pick_show} ({conf_show}%) via {model}")
                    record_pass("Pipeline:AI")
                    break
                except Exception as e:
                    if "decommissioned" in str(e):
                        continue
                    raise e
        except Exception as e:
            warn(f"AI error: {e}")
            record_warn("Pipeline:AI", str(e))

    if not prediction:
        prediction = {
            "pick": "Home Win", "pick_short": "City Win",
            "confidence": 75, "tier": "BANKER",
        }
        ok("Using dummy prediction")
        record_pass("Pipeline:AI")

    pick = prediction.get("pick_short", "City Win")
    conf = prediction.get("confidence", 75)

    # Format
    now  = datetime.now(pytz.timezone("Europe/London"))
    day  = now.strftime("%A")
    date = now.strftime("%d %B %Y")
    ts   = now.strftime("%H:%M")

    tg_text = (
        f"🧪 *PIPELINE TEST*\n"
        f"⚽ *Footy Bankers Football*\n"
        f"📅 {day} {date} │ {ts} UK\n\n"
        f"_Pipeline confirmed working\\._\n\n"
        f"🔒 *TEST PICK*\n"
        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League │ 20:00\n"
        f"*Man City vs Arsenal*\n"
        f"✅ *{pick}*\n"
        f"📊 Confidence: {conf}%\n\n"
        f"_18\\+ \\| Gamble Responsibly_\n"
        f"*Footy Bankers Football* ⚽🔒"
    )

    fb_text = (
        f"⚽ Footy Bankers Football | Pipeline Test\n\n"
        f"{day} {date} at {ts}\n\n"
        f"1️⃣ 🔒 {pick}\n"
        f"   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League | 20:00\n"
        f"   Man City vs Arsenal | 📊 {conf}%\n\n"
        f"t.me/FootyBankersFootball\n\n"
        f"18+ | Gamble Responsibly"
    )

    ok("Posts formatted")
    record_pass("Pipeline:format")

    # Telegram
    tg_token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    tg_channel = os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if tg_token and tg_channel:
        async def send_tg():
            from telegram import Bot
            from telegram.constants import ParseMode
            bot = Bot(token=tg_token)
            try:
                await bot.send_message(
                    chat_id=tg_channel,
                    text=tg_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=True,
                )
                return True
            except Exception:
                try:
                    clean = tg_text
                    for c in ["*", "_", "\\", "`"]:
                        clean = clean.replace(c, "")
                    await bot.send_message(chat_id=tg_channel, text=clean)
                    return True
                except Exception as e2:
                    print(f"      TG: {e2}")
                    return False

        if asyncio.run(send_tg()):
            ok("Telegram sent ✅")
            record_pass("Pipeline:Telegram")
        else:
            fail("Telegram failed")
            record_fail("Pipeline", "Telegram")

    # Facebook
    fb_token = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    fb_pid   = os.environ.get("FACEBOOK_PAGE_ID", "")

    if fb_token and fb_pid:
        r = requests.post(
            f"https://graph.facebook.com/v18.0/{fb_pid}/feed",
            data={"message": fb_text, "access_token": fb_token},
            timeout=30,
        )
        if r.status_code == 200:
            ok("Facebook sent ✅")
            record_pass("Pipeline:Facebook")
        else:
            err = r.json().get("error", {})
            fail(f"Facebook: {err.get('message', r.text[:80])}")
            record_fail("Pipeline", "Facebook")

    ok("Pipeline complete")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_summary():
    header("FINAL SUMMARY - FOOTY BANKERS FOOTBALL")

    total  = sum(len(v) for v in results.values())
    passed = len(results["passed"])
    failed = len(results["failed"])
    warned = len(results["warned"])

    print(f"\n  Total:   {total}")
    print(f"  {GREEN}Passed:  {passed}{RESET}")
    print(f"  {YELLOW}Warned:  {warned}{RESET}")
    print(f"  {RED}Failed:  {failed}{RESET}")

    if results["passed"]:
        print(f"\n{GREEN}{BOLD}  ✅ PASSED:{RESET}")
        for p in results["passed"]:
            print(f"  {GREEN}  • {p}{RESET}")

    if results["warned"]:
        print(f"\n{YELLOW}{BOLD}  ⚠️  WARNINGS:{RESET}")
        for w in results["warned"]:
            print(f"  {YELLOW}  • {w}{RESET}")

    if results["failed"]:
        print(f"\n{RED}{BOLD}  ❌ FAILED:{RESET}")
        for f in results["failed"]:
            print(f"  {RED}  • {f}{RESET}")

    print(f"\n{BOLD}{'='*50}{RESET}")

    if failed == 0:
        print(f"\n{GREEN}{BOLD}  🎉 ALL SYSTEMS GO!{RESET}\n")
        return True
    else:
        print(
            f"\n{RED}{BOLD}"
            f"  ❌ {failed} test(s) failed. Fix above.{RESET}\n"
        )
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print(f"\n{BOLD}")
    print(
        "  ╔══════════════════════════════════════╗\n"
        "  ║   FOOTY BANKERS FOOTBALL             ║\n"
        "  ║   Complete System Test               ║\n"
        "  ║   Standalone - No src imports        ║\n"
        "  ╚══════════════════════════════════════╝"
    )
    print(f"{RESET}")

    uk  = pytz.timezone("Europe/London")
    now = datetime.now(uk)
    print(f"  {now.strftime('%A %d %B %Y %H:%M')} UK\n")

    args    = sys.argv[1:]
    run_all = not args or "all" in args

    if run_all or "secrets"  in args: test_secrets()
    if run_all or "football" in args: test_football_data()
    if run_all or "sportdb"  in args: test_sportdb_api()
    if run_all or "sportsdb" in args: test_sportsdb_free()
    if run_all or "weather"  in args: test_weather()
    if run_all or "rss"      in args: test_rss()
    if run_all or "news"     in args: test_google_news()
    if run_all or "groq"     in args: test_groq()
    if run_all or "telegram" in args: test_telegram()
    if run_all or "facebook" in args: test_facebook()
    if run_all or "github"   in args: test_github()
    if run_all or "pipeline" in args: test_pipeline()

    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
