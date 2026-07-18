"""
FOOTY BANKERS FOOTBALL
Complete System Test - Final Version

Includes SportDB API test.
Updated Groq models.
Fixed Facebook PAGE token handling.

Run: python test_all.py all
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


results = {"passed": [], "failed": [], "warned": []}


def record_pass(n):
    results["passed"].append(n)


def record_fail(n, r=""):
    results["failed"].append(f"{n}: {r}")


def record_warn(n, r=""):
    results["warned"].append(f"{n}: {r}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: SECRETS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_secrets():
    header("TEST 1: SECRETS")

    required = {
        "FOOTBALL_DATA_API_KEY": "football-data.org",
        "SPORTDB_API_KEY":       "SportDB API",
        "GROQ_API_KEY":          "Groq AI",
        "TELEGRAM_BOT_TOKEN":    "Telegram bot",
        "TELEGRAM_CHANNEL_ID":   "Telegram channel",
        "FACEBOOK_PAGE_TOKEN":   "Facebook token",
        "FACEBOOK_PAGE_ID":      "Facebook page ID",
        "GH_TOKEN":              "GitHub token",
    }
    optional = {
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
        record_fail("FootballData", "key not set")
        return

    subheader("Competitions")
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
            fail("Invalid key (401)")
            record_fail("FootballData", "invalid key")
            return
        else:
            fail(f"Status {r.status_code}")
            record_fail("FootballData", f"{r.status_code}")
            return
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("FootballData", str(e))
        return

    subheader("Fixtures")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.football-data.org/v4/matches",
            headers={"X-Auth-Token": key},
            params={"dateFrom": today, "dateTo": today},
            timeout=15,
        )
        if r.status_code == 200:
            m = r.json().get("matches", [])
            ok(f"Fixtures today: {len(m)}")
            record_pass("FootballData:fixtures")
            if m:
                info(
                    f"   Sample: "
                    f"{m[0]['homeTeam']['name']} vs "
                    f"{m[0]['awayTeam']['name']}"
                )
        else:
            warn(f"Status {r.status_code}")
            record_warn("FootballData:fixtures", f"{r.status_code}")
    except Exception as e:
        warn(f"Error: {e}")
        record_warn("FootballData:fixtures", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: SPORTDB API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_sportdb_api():
    header("TEST 3: SPORTDB API (FLASHSCORE + TRANSFERMARKT)")

    key = os.environ.get("SPORTDB_API_KEY", "")
    if not key:
        warn("SPORTDB_API_KEY not set - skipping")
        warn("Get key at: api.sportdb.dev")
        record_warn("SportDB_API", "key not set")
        return

    BASE    = "https://api.sportdb.dev/api"
    headers = {"X-API-Key": key}

    subheader("Transfermarkt countries")
    try:
        r = requests.get(
            f"{BASE}/transfermarkt/countries",
            headers=headers,
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            c    = (
                data.get("countries", [])
                if isinstance(data, dict) else data
            )
            ok(f"Transfermarkt connected - {len(c)} countries")
            record_pass("SportDB_API:transfermarkt")
        elif r.status_code == 401:
            fail("Invalid API key (401)")
            record_fail("SportDB_API", "invalid key")
            return
        else:
            warn(f"Status {r.status_code}: {r.text[:100]}")
            record_warn("SportDB_API", f"tm status {r.status_code}")
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("SportDB_API", str(e))
        return

    time.sleep(1)

    subheader("Flashscore football")
    try:
        r = requests.get(
            f"{BASE}/flashscore/football",
            headers=headers,
            timeout=15,
        )
        if r.status_code == 200:
            data    = r.json()
            matches = (
                data.get("matches")
                or data.get("events")
                or data.get("data")
                or (data if isinstance(data, list) else [])
            )
            ok(f"Flashscore connected - {len(matches)} matches")
            record_pass("SportDB_API:flashscore")
            if matches:
                m    = matches[0]
                home = (
                    m.get("home_team")
                    or m.get("homeTeam")
                    or "?"
                )
                away = (
                    m.get("away_team")
                    or m.get("awayTeam")
                    or "?"
                )
                comp = (
                    m.get("tournament")
                    or m.get("competition")
                    or m.get("league")
                    or "?"
                )
                info(f"   Sample: {home} vs {away} ({comp})")
        elif r.status_code == 401:
            fail("Invalid key for Flashscore")
            record_fail("SportDB_API", "fs 401")
        else:
            warn(f"Flashscore status {r.status_code}: {r.text[:100]}")
            record_warn("SportDB_API", f"fs {r.status_code}")
    except Exception as e:
        warn(f"Flashscore error: {e}")
        record_warn("SportDB_API", f"flashscore: {e}")

    time.sleep(1)

    subheader("Player search (Transfermarkt)")
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
                or []
            )
            if players:
                p     = players[0]
                name  = p.get("name") or "Found"
                value = p.get("market_value") or "N/A"
                ok(f"Player search: {name} - {value}")
                record_pass("SportDB_API:player_search")
            else:
                ok("Player search endpoint works")
                record_pass("SportDB_API:player_search")
        else:
            warn(f"Player search {r.status_code}")
            record_warn("SportDB_API", f"player {r.status_code}")
    except Exception as e:
        warn(f"Player search: {e}")
        record_warn("SportDB_API", f"player: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: THESPORTSDB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_sports_db():
    header("TEST 4: THESPORTSDB (FREE)")

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(
            "https://www.thesportsdb.com"
            "/api/v1/json/3/eventsday.php",
            params={"d": today, "s": "Soccer"},
            timeout=15,
        )
        if r.status_code == 200:
            events = r.json().get("events") or []
            ok(f"Connected - {len(events)} events today")
            record_pass("SportsDB:connection")
            if events:
                e = events[0]
                info(
                    f"   {e.get('strHomeTeam')} vs "
                    f"{e.get('strAwayTeam')}"
                )
        else:
            warn(f"Status {r.status_code}")
            record_warn("SportsDB", f"{r.status_code}")
    except Exception as e:
        warn(f"Error: {e}")
        record_warn("SportsDB", str(e))


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
                "hourly":        (
                    "precipitation,"
                    "windspeed_10m,"
                    "temperature_2m"
                ),
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
            if rain:
                ok(f"Precipitation: {rain[0]}mm")
            record_pass("Weather:connection")
        else:
            warn(f"Status {r.status_code}")
            record_warn("Weather", f"{r.status_code}")
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
                info(f"   {feed.entries[0].get('title','?')[:55]}")
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
                f"?q={q}+football"
                f"&hl=en-GB&gl=GB&ceid=GB:en"
            )
            feed = feedparser.parse(url)
            if feed.entries:
                ok(f"{team}: {len(feed.entries)} articles")
                info(f"   {feed.entries[0].get('title','?')[:55]}")
                record_pass(f"GoogleNews:{team}")
            else:
                warn(f"{team}: No results")
                record_warn(f"GoogleNews:{team}", "no results")
        except Exception as e:
            warn(f"{team}: {e}")
            record_warn(f"GoogleNews:{team}", str(e))
        time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 8: GROQ AI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_groq():
    header("TEST 8: GROQ AI")

    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        fail("GROQ_API_KEY not set")
        record_fail("Groq", "key not set")
        return

    try:
        from groq import Groq
        client = Groq(api_key=key)

        subheader("Available models")
        available = []
        try:
            ml        = client.models.list()
            available = [m.id for m in ml.data]
            info(f"Total: {len(available)}")
            for m in sorted(available):
                info(f"   {m}")
        except Exception as e:
            warn(f"Could not list: {e}")

        our_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
        ]

        subheader("Testing configured models")
        working = None

        for model in our_models:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role":    "user",
                        "content": (
                            "Say: Footy Bankers Football works"
                        ),
                    }],
                    max_tokens=20,
                    temperature=0.1,
                )
                answer = resp.choices[0].message.content
                ok(f"{model}: WORKING ✓")
                info(f"   {answer[:50]}")
                record_pass(f"Groq:{model}")
                if not working:
                    working = model
            except Exception as e:
                err = str(e)
                if (
                    "decommissioned" in err
                    or "not_found" in err
                    or "does not exist" in err
                ):
                    fail(f"{model}: not available")
                    record_fail(f"Groq:{model}", "unavailable")
                else:
                    warn(f"{model}: {err[:60]}")
                    record_warn(f"Groq:{model}", err[:60])
            time.sleep(1)

        if not working:
            fail("No working model found!")
            record_fail("Groq", "no working model")
            return

        subheader(f"JSON test with {working}")
        try:
            resp = client.chat.completions.create(
                model=working,
                messages=[
                    {"role": "system", "content": "JSON only."},
                    {"role": "user",   "content": (
                        'Return: {"pick":"Home Win","confidence":72}'
                    )},
                ],
                max_tokens=100,
                response_format={"type": "json_object"},
            )
            p = json.loads(resp.choices[0].message.content)
            ok(f"JSON works - pick={p.get('pick')} conf={p.get('confidence')}")
            record_pass("Groq:JSON")
        except Exception as e:
            fail(f"JSON failed: {e}")
            record_fail("Groq:JSON", str(e))

        subheader("Football prediction test")
        try:
            resp = client.chat.completions.create(
                model=working,
                messages=[
                    {"role": "system", "content": "Football analyst. JSON only."},
                    {"role": "user",   "content": """
Analyse: Man City vs Arsenal. Premier League.
Home form: WWWDW. Away form: WWLDW.
Return: {"pick":"Home Win","pick_short":"City Win","confidence":75,"reasoning":["r1"],"risk":"r","predicted_score":"2-1","avoid":false}
"""},
                ],
                max_tokens=200,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            pred = json.loads(resp.choices[0].message.content)
            ok(
                f"Prediction: "
                f"{pred.get('pick_short')} "
                f"({pred.get('confidence')}%)"
            )
            record_pass("Groq:prediction")
        except Exception as e:
            fail(f"Prediction failed: {e}")
            record_fail("Groq:prediction", str(e))

    except ImportError:
        fail("groq not installed")
        record_fail("Groq", "not installed")
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("Groq", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 9: TELEGRAM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _tg_test():
    from telegram import Bot
    from telegram.constants import ParseMode

    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if not token:
        fail("Token not set")
        record_fail("Telegram", "no token")
        return False
    if not channel:
        fail("Channel not set")
        record_fail("Telegram", "no channel")
        return False

    bot = Bot(token=token)

    subheader("Bot identity")
    try:
        me = await bot.get_me()
        ok(f"Bot: @{me.username}")
        record_pass("Telegram:identity")
    except Exception as e:
        fail(f"Failed: {e}")
        record_fail("Telegram", f"identity: {e}")
        return False

    subheader("Channel access")
    try:
        chat = await bot.get_chat(channel)
        ok(f"Channel: {chat.title}")
        record_pass("Telegram:channel")
    except Exception as e:
        fail(f"Failed: {e}")
        record_fail("Telegram", f"channel: {e}")
        return False

    subheader("Plain text")
    try:
        m = await bot.send_message(
            chat_id=channel,
            text=(
                "🧪 FOOTY BANKERS FOOTBALL\n\n"
                "System Test - Plain Text\n\n"
                "Plain text posting confirmed working."
            ),
        )
        ok(f"Sent (ID: {m.message_id})")
        record_pass("Telegram:plain")
    except Exception as e:
        fail(f"Failed: {e}")
        record_fail("Telegram", f"plain: {e}")
        return False

    await asyncio.sleep(2)

    subheader("Markdown format")
    try:
        m = await bot.send_message(
            chat_id=channel,
            text=(
                "🧪 *FOOTY BANKERS FOOTBALL*\n\n"
                "System Test \\- Markdown\n\n"
                "✅ *Markdown posting works\\!*\n\n"
                "📊 Confidence: 78%\n"
                "🔒 Tier: BANKER\n"
                "⚽ Pick: Man City Win\n\n"
                "_Predictions look like this every day_\n\n"
                "*Footy Bankers Football* ⚽🔒"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        ok(f"Sent (ID: {m.message_id})")
        record_pass("Telegram:markdown")
    except Exception as e:
        warn(f"Markdown: {e}")
        record_warn("Telegram", f"markdown: {e}")

    await asyncio.sleep(2)

    subheader("Full prediction format")
    try:
        m = await bot.send_message(
            chat_id=channel,
            text=(
                "🧪 *FULL FORMAT TEST*\n\n"
                "⚽ *FOOTY BANKERS FOOTBALL*\n"
                "📅 System Check │ All Systems Go\n\n"
                "_Right\\. System running\\. "
                "Predictions look like this\\._\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📊 Picks: *15* │ 🔥 Streak: *4*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🔒 *BANKER PICKS*\n\n"
                "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League │ 20:00\n"
                "*Manchester City vs Arsenal*\n"
                "✅ *City Win*\n"
                "📊 Confidence: 82%\n"
                "🎯 Score: 2\\-0\n\n"
                "_City solid at home\\. "
                "Eight wins from ten\\. "
                "Cannot see past this\\._\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "_18\\+ \\| Gamble Responsibly \\| "
                "begambleaware\\.org_\n"
                "*Footy Bankers Football* ⚽🔒"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        ok(f"Sent (ID: {m.message_id})")
        record_pass("Telegram:full_format")
    except Exception as e:
        warn(f"Full format: {e}")
        record_warn("Telegram", f"full: {e}")

    return True


def test_telegram():
    header("TEST 9: TELEGRAM")
    try:
        return asyncio.run(_tg_test())
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("Telegram", str(e))
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 10: FACEBOOK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_facebook():
    header("TEST 10: FACEBOOK PAGE")

    token   = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "")
    GRAPH   = "https://graph.facebook.com/v18.0"

    if not token:
        fail("Token not set")
        record_fail("Facebook", "no token")
        return False
    if not page_id:
        fail("Page ID not set")
        record_fail("Facebook", "no page ID")
        return False

    subheader("Page connection")
    try:
        r = requests.get(
            f"{GRAPH}/{page_id}",
            params={
                "fields":       "name,fan_count,category",
                "access_token": token,
            },
            timeout=15,
        )
        if r.status_code == 200:
            d = r.json()
            ok(f"Page: {d.get('name')}")
            ok(f"Category: {d.get('category', 'N/A')}")
            ok(f"Followers: {d.get('fan_count', 0):,}")
            record_pass("Facebook:page")
        else:
            err = r.json().get("error", {})
            fail(f"Failed: {err.get('message', r.text[:100])}")
            record_fail("Facebook", err.get("message", "failed"))
            return False
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("Facebook", str(e))
        return False

    subheader("Token info")
    try:
        r = requests.get(
            f"{GRAPH}/debug_token",
            params={
                "input_token":  token,
                "access_token": token,
            },
            timeout=15,
        )
        if r.status_code == 200:
            data     = r.json().get("data", {})
            valid    = data.get("is_valid", False)
            tok_type = data.get("type", "unknown")
            scopes   = data.get("scopes", [])

            if valid:
                ok("Token valid")
                record_pass("Facebook:token_valid")
            else:
                fail("Token INVALID")
                record_fail("Facebook", "invalid token")

            info(f"Token type: {tok_type}")

            if tok_type == "PAGE":
                ok("PAGE token - correct type ✅")
                record_pass("Facebook:token_type")
            else:
                warn(
                    "USER token detected. "
                    "Convert to PAGE token for best results."
                )
                record_warn("Facebook", "user not page token")

            for scope in [
                "pages_manage_posts",
                "pages_read_engagement",
            ]:
                if scope in scopes:
                    ok(f"Permission: {scope} ✓")
                    record_pass(f"Facebook:perm:{scope}")
                else:
                    warn(f"Permission not listed: {scope}")
                    record_warn("Facebook", f"missing: {scope}")

    except Exception as e:
        warn(f"Token check: {e}")
        record_warn("Facebook", f"token check: {e}")

    subheader("Post test (THE REAL TEST)")
    info("If this passes, Facebook is fully working")
    try:
        now_str = datetime.now().strftime("%d %B %Y %H:%M")
        msg = (
            f"⚽ Footy Bankers Football | System Test\n\n"
            f"Tested: {now_str}\n\n"
            f"Automated posting confirmed.\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"1️⃣ 🔒 Man City Win\n"
            f"   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League | 20:00\n"
            f"   Man City vs Arsenal | 📊 82%\n\n"
            f"2️⃣ 💪 Real Madrid Win\n"
            f"   🇪🇸 La Liga | 21:00\n"
            f"   Real Madrid vs Getafe | 📊 75%\n\n"
            f"3️⃣ 💪 Over 2.5 Goals\n"
            f"   🇩🇪 Bundesliga | 19:30\n"
            f"   Bayern vs Dortmund | 📊 71%\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"Full analysis:\n"
            f"t.me/FootyBankersFootball\n\n"
            f"18+ | Gamble Responsibly | begambleaware.org"
        )
        r = requests.post(
            f"{GRAPH}/{page_id}/feed",
            data={"message": msg, "access_token": token},
            timeout=30,
        )
        if r.status_code == 200:
            pid = r.json().get("id", "")
            ok(f"POST PUBLISHED! ID: {pid}")
            ok("Facebook fully working ✅")
            record_pass("Facebook:post")
        else:
            err  = r.json().get("error", {})
            code = err.get("code", "?")
            msg  = err.get("message", r.text[:200])
            fail(f"Post failed (code {code}): {msg}")
            record_fail("Facebook", f"code {code}")
            return False
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("Facebook", str(e))
        return False

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 11: GITHUB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_github():
    header("TEST 11: GITHUB TOKEN")

    token = os.environ.get("GH_TOKEN", "")
    if not token:
        fail("GH_TOKEN not set")
        record_fail("GitHub", "not set")
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
            u = r.json()
            ok(f"User: {u.get('login')}")
            ok(f"Name: {u.get('name', 'N/A')}")
            record_pass("GitHub:user")
        else:
            fail(f"Auth failed: {r.status_code}")
            record_fail("GitHub", f"{r.status_code}")
            return
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("GitHub", str(e))
        return

    subheader("Write access")
    try:
        os.makedirs("data/predictions", exist_ok=True)
        p = "data/predictions/test_write.json"
        with open(p, "w") as f:
            json.dump({"test": True}, f)
        ok("Can write data files")
        record_pass("GitHub:write")
        os.remove(p)
    except Exception as e:
        warn(f"Write test: {e}")
        record_warn("GitHub", f"write: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 12: FULL PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_pipeline():
    header("TEST 12: FULL PIPELINE")

    info("Complete morning workflow simulation")

    subheader("Step 1: Match data")
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
        "h2h":             {
            "home_wins": 6,
            "away_wins": 2,
            "draws":     2,
            "avg_goals": 2.8,
        },
        "home_news_note":  "No injury concerns",
        "away_news_note":  "Saka doubtful",
        "weather":         {
            "description": "Clear",
            "impact":      0,
        },
        "home_squad_value": {},
        "away_squad_value": {},
    }
    ok("Test match: Man City vs Arsenal")
    record_pass("Pipeline:match")

    subheader("Step 2: AI prediction")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_key:
        warn("No Groq key - using dummy")
        prediction = {
            "pick":            "Home Win",
            "pick_short":      "City Win",
            "confidence":      78,
            "tier":            "BANKER",
            "reasoning":       ["City strong at home"],
            "risk":            "Arsenal attack",
            "predicted_score": "2-1",
            "human_analysis":  (
                "City flying at home. Cannot see past this."
            ),
            "match_data": match,
        }
        ok("Dummy prediction created")
        record_pass("Pipeline:AI")
    else:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            models = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-120b",
            ]
            prediction = None
            for model in models:
                try:
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role":    "system",
                                "content": "Football analyst. JSON only.",
                            },
                            {
                                "role": "user",
                                "content": (
                                    "Analyse: Man City vs Arsenal. "
                                    "Premier League. Home form WWWDW. "
                                    "Return: {\"pick\":\"Home Win\","
                                    "\"pick_short\":\"City Win\","
                                    "\"confidence\":75,"
                                    "\"reasoning\":[\"City strong\"],"
                                    "\"risk\":\"Arsenal attack\","
                                    "\"predicted_score\":\"2-1\","
                                    "\"avoid\":false}"
                                ),
                            },
                        ],
                        max_tokens=200,
                        temperature=0.3,
                        response_format={"type": "json_object"},
                    )
                    prediction = json.loads(
                        resp.choices[0].message.content
                    )
                    prediction["tier"]           = "BANKER"
                    prediction["human_analysis"] = (
                        "City have been brilliant at home. "
                        "Cannot see past this one."
                    )
                    prediction["match_data"] = match
                    ok(
                        f"AI: "
                        f"{prediction.get('pick_short', 'City Win')} "
                        f"({prediction.get('confidence', 75)}%) "
                        f"via {model}"
                    )
                    record_pass("Pipeline:AI")
                    break
                except Exception as e:
                    if (
                        "decommissioned" in str(e)
                        or "not_found" in str(e)
                    ):
                        continue
                    raise e

            if not prediction:
                fail("All AI models failed")
                record_fail("Pipeline", "AI failed")
                return False

        except Exception as e:
            fail(f"AI error: {e}")
            record_fail("Pipeline", f"AI: {e}")
            return False

    subheader("Step 3: Format posts")
    now  = datetime.now(pytz.timezone("Europe/London"))
    day  = now.strftime("%A")
    date = now.strftime("%d %B %Y")
    ts   = now.strftime("%H:%M")
    pick = prediction.get("pick_short", "City Win")
    conf = prediction.get("confidence", 75)

    tg_text = (
        f"🧪 *PIPELINE TEST*\n"
        f"⚽ *FOOTY BANKERS FOOTBALL*\n"
        f"📅 {day} {date} │ {ts} UK\n\n"
        f"_Pipeline complete\\. System working\\._\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 *TEST PREDICTION*\n\n"
        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League │ 20:00\n"
        f"*Manchester City vs Arsenal*\n"
        f"✅ *{pick}*\n"
        f"📊 Confidence: {conf}%\n\n"
        f"_City brilliant at home\\. "
        f"Cannot see past this\\._\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_18\\+ \\| Gamble Responsibly \\| "
        f"begambleaware\\.org_\n"
        f"*Footy Bankers Football* ⚽🔒"
    )
    fb_text = (
        f"⚽ Footy Bankers Football | Pipeline Test\n\n"
        f"{day} {date} at {ts} UK\n\n"
        f"1️⃣ 🔒 {pick}\n"
        f"   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League | 20:00\n"
        f"   Man City vs Arsenal\n"
        f"   📊 {conf}% confidence\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"Full picks: t.me/FootyBankersFootball\n\n"
        f"18+ | Gamble Responsibly | begambleaware.org"
    )
    ok("Posts formatted")
    record_pass("Pipeline:formatting")

    subheader("Step 4: Send to platforms")

    tg_tok 
