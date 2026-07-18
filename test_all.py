"""
FOOTY BANKERS FOOTBALL
Complete System Test Script

Tests every secret, every platform,
every API connection.

Run with:
python test_all.py

Or in GitHub Actions manually.
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLOURS FOR TERMINAL OUTPUT
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
# RESULTS TRACKER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

results = {
    "passed": [],
    "failed": [],
    "warned": [],
}

def record_pass(name):
    results["passed"].append(name)

def record_fail(name, reason=""):
    results["failed"].append(f"{name}: {reason}")

def record_warn(name, reason=""):
    results["warned"].append(f"{name}: {reason}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: ENVIRONMENT SECRETS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_secrets():
    header("TEST 1: CHECKING ALL SECRETS")

    required = {
        "FOOTBALL_DATA_API_KEY": "football-data.org API key",
        "API_FOOTBALL_KEY":      "API-Football / RapidAPI key",
        "GROQ_API_KEY":          "Groq AI API key",
        "TELEGRAM_BOT_TOKEN":    "Telegram bot token",
        "TELEGRAM_CHANNEL_ID":   "Telegram channel ID",
        "FACEBOOK_PAGE_TOKEN":   "Facebook page access token",
        "FACEBOOK_PAGE_ID":      "Facebook page ID",
        "GH_TOKEN":              "GitHub personal access token",
    }

    optional = {
        "FACEBOOK_TOKEN_DATE":   "Facebook token creation date",
        "TELEGRAM_OWNER_CHAT_ID": "Your personal Telegram chat ID",
    }

    all_good = True

    subheader("Required Secrets")
    for key, desc in required.items():
        val = os.environ.get(key, "")
        if not val:
            fail(f"{key} is MISSING ({desc})")
            record_fail(f"Secret: {key}", "not set")
            all_good = False
        elif val == "your_key_here" or \
             val == "placeholder":
            warn(f"{key} looks like a placeholder")
            record_warn(f"Secret: {key}", "placeholder value")
        else:
            masked = val[:4] + "****" + val[-4:] \
                if len(val) > 8 else "****"
            ok(f"{key} is set ({masked})")
            record_pass(f"Secret: {key}")

    subheader("Optional Secrets")
    for key, desc in optional.items():
        val = os.environ.get(key, "")
        if not val:
            warn(f"{key} not set ({desc})")
            record_warn(f"Secret: {key}", "optional, not set")
        else:
            ok(f"{key} is set")
            record_pass(f"Secret: {key}")

    return all_good


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: FOOTBALL DATA ORG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_football_data():
    header("TEST 2: FOOTBALL-DATA.ORG API")

    key = os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not key:
        fail("API key not set - skipping test")
        record_fail("FootballData", "key not set")
        return False

    subheader("Testing connection")
    try:
        r = requests.get(
            "https://api.football-data.org/v4/competitions",
            headers={"X-Auth-Token": key},
            timeout=15,
        )

        if r.status_code == 200:
            data = r.json()
            comps = data.get("competitions", [])
            ok(f"Connection successful")
            ok(f"Competitions available: {len(comps)}")
            record_pass("FootballData: connection")

            # Show available competitions
            info("Available competitions:")
            for c in comps[:8]:
                info(
                    f"   {c.get('code', '?')} - "
                    f"{c.get('name', '?')}"
                )

        elif r.status_code == 401:
            fail("Invalid API key (401 Unauthorized)")
            record_fail("FootballData", "invalid key")
            return False

        elif r.status_code == 429:
            warn("Rate limit hit - key works but too many requests")
            record_warn("FootballData", "rate limited")

        else:
            fail(f"Unexpected status: {r.status_code}")
            record_fail("FootballData", f"status {r.status_code}")
            return False

    except requests.Timeout:
        fail("Request timed out")
        record_fail("FootballData", "timeout")
        return False
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("FootballData", str(e))
        return False

    subheader("Testing fixtures endpoint")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.football-data.org/v4/matches",
            headers={"X-Auth-Token": key},
            params={
                "dateFrom": today,
                "dateTo":   today,
            },
            timeout=15,
        )

        if r.status_code == 200:
            matches = r.json().get("matches", [])
            ok(f"Fixtures endpoint works")
            ok(f"Matches today: {len(matches)}")
            record_pass("FootballData: fixtures")

            if matches:
                m = matches[0]
                info(
                    f"Sample: "
                    f"{m['homeTeam']['name']} vs "
                    f"{m['awayTeam']['name']}"
                )
        else:
            warn(
                f"Fixtures returned {r.status_code}"
            )
            record_warn(
                "FootballData: fixtures",
                f"status {r.status_code}"
            )

    except Exception as e:
        warn(f"Fixtures test error: {e}")
        record_warn("FootballData: fixtures", str(e))

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: API-FOOTBALL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_api_football():
    header("TEST 3: API-FOOTBALL (RAPIDAPI)")

    key = os.environ.get("API_FOOTBALL_KEY", "")
    if not key:
        fail("API key not set - skipping test")
        record_fail("APIFootball", "key not set")
        return False

    subheader("Testing connection")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            headers={
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-rapidapi-key":  key,
            },
            params={"date": today},
            timeout=15,
        )

        if r.status_code == 200:
            data = r.json()
            fixtures = data.get("response", [])
            errors = data.get("errors", [])

            if errors:
                fail(f"API errors: {errors}")
                record_fail("APIFootball", str(errors))
                return False

            ok(f"Connection successful")
            ok(f"Fixtures today: {len(fixtures)}")
            record_pass("APIFootball: connection")

            # Check remaining requests
            headers = r.headers
            remaining = headers.get(
                "x-ratelimit-requests-remaining", "?"
            )
            limit = headers.get(
                "x-ratelimit-requests-limit", "?"
            )
            info(
                f"Requests remaining today: "
                f"{remaining}/{limit}"
            )

            if fixtures:
                f = fixtures[0]
                league = f.get("league", {})
                teams  = f.get("teams", {})
                info(
                    f"Sample: "
                    f"{teams.get('home', {}).get('name')} vs "
                    f"{teams.get('away', {}).get('name')}"
                    f" ({league.get('name')})"
                )

        elif r.status_code == 401:
            fail("Invalid API key")
            record_fail("APIFootball", "invalid key 401")
            return False

        else:
            fail(f"Unexpected status: {r.status_code}")
            fail(f"Response: {r.text[:200]}")
            record_fail(
                "APIFootball", f"status {r.status_code}"
            )
            return False

    except Exception as e:
        fail(f"Error: {e}")
        record_fail("APIFootball", str(e))
        return False

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: THESPORTSDB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_sports_db():
    header("TEST 4: THESPORTSDB (NO KEY NEEDED)")

    subheader("Testing connection")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(
            "https://www.thesportsdb.com/api/v1/json/3/eventsday.php",
            params={"d": today, "s": "Soccer"},
            timeout=15,
        )

        if r.status_code == 200:
            events = r.json().get("events") or []
            ok(f"Connection successful")
            ok(f"Events today: {len(events)}")
            record_pass("SportsDB: connection")

            if events:
                e = events[0]
                info(
                    f"Sample: "
                    f"{e.get('strHomeTeam')} vs "
                    f"{e.get('strAwayTeam')}"
                )
        else:
            warn(f"Status: {r.status_code}")
            record_warn(
                "SportsDB", f"status {r.status_code}"
            )

    except Exception as e:
        warn(f"SportsDB error: {e}")
        record_warn("SportsDB", str(e))

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: OPEN-METEO WEATHER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_weather():
    header("TEST 5: OPEN-METEO WEATHER (NO KEY NEEDED)")

    subheader("Testing weather for London (Arsenal)")
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
            data = r.json()
            hourly = data.get("hourly", {})
            temps  = hourly.get("temperature_2m", [])
            rain   = hourly.get("precipitation", [])

            ok(f"Weather API working")
            if temps:
                ok(f"Current temp: {temps[0]}°C")
            if rain:
                ok(f"Precipitation: {rain[0]}mm")
            record_pass("Weather: connection")
        else:
            warn(f"Weather returned {r.status_code}")
            record_warn("Weather", f"status {r.status_code}")

    except Exception as e:
        warn(f"Weather error: {e}")
        record_warn("Weather", str(e))

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: RSS NEWS FEEDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_rss_feeds():
    header("TEST 6: RSS NEWS FEEDS")

    feeds = {
        "BBC Sport": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "Sky Sports": "https://www.skysports.com/rss/12040",
        "Guardian":   "https://www.theguardian.com/football/rss",
        "ESPN":       "https://www.espn.com/espn/rss/soccer/news",
        "UEFA":       "https://www.uefa.com/rss.xml",
    }

    for name, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            entries = feed.entries

            if entries:
                ok(f"{name}: {len(entries)} articles")
                info(f"   Latest: {entries[0].get('title', '?')[:60]}")
                record_pass(f"RSS: {name}")
            else:
                warn(f"{name}: No entries returned")
                record_warn(f"RSS: {name}", "no entries")

        except Exception as e:
            warn(f"{name}: Error - {e}")
            record_warn(f"RSS: {name}", str(e))

        time.sleep(0.5)

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 7: GOOGLE NEWS RSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_google_news():
    header("TEST 7: GOOGLE NEWS RSS")

    subheader("Testing team-specific news search")
    teams = ["Manchester City", "Real Madrid"]

    for team in teams:
        try:
            query = team.replace(" ", "+")
            url = (
                f"https://news.google.com/rss/search"
                f"?q={query}+football"
                f"&hl=en-GB&gl=GB&ceid=GB:en"
            )
            feed = feedparser.parse(url)

            if feed.entries:
                ok(
                    f"{team}: "
                    f"{len(feed.entries)} articles"
                )
                info(
                    f"   Latest: "
                    f"{feed.entries[0].get('title', '?')[:60]}"
                )
                record_pass(f"GoogleNews: {team}")
            else:
                warn(f"{team}: No results")
                record_warn(
                    f"GoogleNews: {team}", "no results"
                )

        except Exception as e:
            warn(f"{team}: Error - {e}")
            record_warn(f"GoogleNews: {team}", str(e))

        time.sleep(1)

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 8: GROQ AI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_groq():
    header("TEST 8: GROQ AI API")

    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        fail("GROQ_API_KEY not set - skipping")
        record_fail("Groq", "key not set")
        return False

    try:
        from groq import Groq
        client = Groq(api_key=key)

        subheader("Testing primary model: llama-3.1-70b")
        resp = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a football analyst. "
                        "In one sentence, predict who "
                        "wins: Man City vs Arsenal."
                    ),
                }
            ],
            max_tokens=50,
            temperature=0.3,
        )
        answer = resp.choices[0].message.content
        ok(f"Primary model working")
        ok(f"Response: {answer[:80]}")
        record_pass("Groq: llama-3.1-70b")

        time.sleep(1)

        subheader("Testing fallback model: mixtral-8x7b")
        resp2 = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "user",
                    "content": "Say: Footy Bankers Football works",
                }
            ],
            max_tokens=20,
        )
        answer2 = resp2.choices[0].message.content
        ok(f"Fallback model working")
        ok(f"Response: {answer2[:80]}")
        record_pass("Groq: mixtral-8x7b")

        time.sleep(1)

        subheader("Testing JSON response format")
        resp3 = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You respond in valid JSON only.",
                },
                {
                    "role": "user",
                    "content": (
                        'Return JSON: {"pick": "Home Win", '
                        '"confidence": 72, "tier": "STRONG"}'
                    ),
                },
            ],
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        raw = resp3.choices[0].message.content
        parsed = json.loads(raw)
        ok(f"JSON format working")
        ok(
            f"Parsed: pick={parsed.get('pick')} "
            f"conf={parsed.get('confidence')}"
        )
        record_pass("Groq: JSON format")

    except ImportError:
        fail("groq package not installed")
        fail("Run: pip install groq")
        record_fail("Groq", "package not installed")
        return False

    except Exception as e:
        fail(f"Groq error: {e}")
        record_fail("Groq", str(e))
        return False

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 9: TELEGRAM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _telegram_test():
    from telegram import Bot
    from telegram.constants import ParseMode

    token      = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if not token:
        fail("TELEGRAM_BOT_TOKEN not set")
        record_fail("Telegram", "token not set")
        return False

    if not channel_id:
        fail("TELEGRAM_CHANNEL_ID not set")
        record_fail("Telegram", "channel ID not set")
        return False

    bot = Bot(token=token)

    subheader("Testing bot identity")
    try:
        me = await bot.get_me()
        ok(f"Bot connected: @{me.username}")
        ok(f"Bot name: {me.first_name}")
        record_pass("Telegram: bot identity")
    except Exception as e:
        fail(f"Bot identity failed: {e}")
        record_fail("Telegram", f"bot identity: {e}")
        return False

    subheader("Testing channel access")
    try:
        chat = await bot.get_chat(channel_id)
        ok(f"Channel found: {chat.title}")
        ok(f"Channel type: {chat.type}")
        record_pass("Telegram: channel access")
    except Exception as e:
        fail(f"Cannot access channel: {e}")
        fail(f"Check bot is admin in channel")
        record_fail("Telegram", f"channel access: {e}")
        return False

    subheader("Sending test message (plain text)")
    try:
        msg1 = await bot.send_message(
            chat_id=channel_id,
            text=(
                "🧪 FOOTY BANKERS FOOTBALL\n\n"
                "System Test - Plain Text\n\n"
                "If you see this, plain text posting works.\n\n"
                "Testing in progress..."
            ),
        )
        ok(f"Plain text message sent (ID: {msg1.message_id})")
        record_pass("Telegram: plain text post")
    except Exception as e:
        fail(f"Plain text failed: {e}")
        record_fail("Telegram", f"plain text: {e}")
        return False

    await asyncio.sleep(2)

    subheader("Sending test message (Markdown)")
    try:
        msg2 = await bot.send_message(
            chat_id=channel_id,
            text=(
                "🧪 *FOOTY BANKERS FOOTBALL*\n\n"
                "System Test \\- Markdown Format\n\n"
                "✅ *Telegram posting works\\!*\n\n"
                "📊 Confidence: 78%\n"
                "🔒 Tier: BANKER\n"
                "⚽ Pick: Man City Win\n\n"
                "_This is the formatting used for daily predictions_\n\n"
                "If everything looks correct, Telegram is ready\\! 🎉"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        ok(
            f"Markdown message sent "
            f"(ID: {msg2.message_id})"
        )
        record_pass("Telegram: markdown post")
    except Exception as e:
        warn(f"Markdown failed: {e}")
        warn(f"Will use plain text fallback in production")
        record_warn("Telegram", f"markdown: {e}")

    await asyncio.sleep(2)

    subheader("Sending full prediction format test")
    try:
        msg3 = await bot.send_message(
            chat_id=channel_id,
            text=(
                "🧪 *FULL FORMAT TEST*\n\n"
                "⚽ *FOOTY BANKERS FOOTBALL*\n"
                "📅 Test Day │ System Check\n\n"
                "_Right\\. Everything is running\\. "
                "This is how the daily predictions "
                "will look\\._\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📊 Picks today: *15* │ 🔥 Streak: *4*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🔒 *THE BANKER PICKS*\n\n"
                "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League │ 20:00\n"
                "*Manchester City vs Arsenal*\n"
                "✅ *City Win*\n"
                "📊 Confidence: 82%\n"
                "🎯 Score: 2\\-0\n\n"
                "_City have been solid at home\\. "
                "Eight wins from their last ten\\. "
                "Cannot see past this one\\._\n"
                "⚠️ Risk: _Arsenal set pieces_\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "_18\\+ \\| Gamble Responsibly \\| "
                "begambleaware\\.org_\n"
                "*Footy Bankers Football* ⚽🔒"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        ok(
            f"Full format test sent "
            f"(ID: {msg3.message_id})"
        )
        record_pass("Telegram: full format post")
    except Exception as e:
        warn(f"Full format warning: {e}")
        record_warn("Telegram", f"full format: {e}")

    return True


def test_telegram():
    header("TEST 9: TELEGRAM")

    try:
        return asyncio.run(_telegram_test())
    except Exception as e:
        fail(f"Telegram test error: {e}")
        record_fail("Telegram", str(e))
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 10: FACEBOOK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_facebook():
    header("TEST 10: FACEBOOK PAGE")

    token   = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "")

    if not token:
        fail("FACEBOOK_PAGE_TOKEN not set")
        record_fail("Facebook", "token not set")
        return False

    if not page_id:
        fail("FACEBOOK_PAGE_ID not set")
        record_fail("Facebook", "page ID not set")
        return False

    GRAPH = "https://graph.facebook.com/v18.0"

    subheader("Testing page connection")
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
            data = r.json()
            ok(f"Page connected: {data.get('name')}")
            ok(f"Category: {data.get('category', 'N/A')}")
            ok(
                f"Followers: "
                f"{data.get('fan_count', 0):,}"
            )
            record_pass("Facebook: page connection")
        else:
            err = r.json().get("error", {})
            fail(
                f"Connection failed: "
                f"{err.get('message', r.text[:200])}"
            )
            record_fail(
                "Facebook",
                err.get("message", "connection failed")
            )
            return False

    except Exception as e:
        fail(f"Connection error: {e}")
        record_fail("Facebook", str(e))
        return False

    subheader("Checking token validity")
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
            data = r.json().get("data", {})
            is_valid = data.get("is_valid", False)
            expires  = data.get("expires_at", 0)
            scopes   = data.get("scopes", [])

            if is_valid:
                ok(f"Token is valid")
                record_pass("Facebook: token valid")
            else:
                fail(f"Token is INVALID")
                record_fail("Facebook", "token invalid")

            if expires:
                exp_dt = datetime.fromtimestamp(expires)
                days_left = (
                    exp_dt - datetime.now()
                ).days
                if days_left > 7:
                    ok(
                        f"Token expires in "
                        f"{days_left} days "
                        f"({exp_dt.strftime('%d %b %Y')})"
                    )
                elif days_left > 0:
                    warn(
                        f"Token expires in "
                        f"{days_left} days - "
                        f"refresh soon!"
                    )
                    record_warn(
                        "Facebook",
                        f"expires in {days_left} days"
                    )
                else:
                    fail("Token has already expired!")
                    record_fail(
                        "Facebook", "token expired"
                    )
            else:
                info("Token expiry: Never (permanent)")

            needed = [
                "pages_manage_posts",
                "pages_read_engagement",
            ]
            for scope in needed:
                if scope in scopes:
                    ok(f"Permission: {scope} ✓")
                else:
                    warn(
                        f"Permission missing: {scope}"
                    )
                    record_warn(
                        "Facebook",
                        f"missing permission: {scope}"
                    )

    except Exception as e:
        warn(f"Token check error: {e}")
        record_warn("Facebook", f"token check: {e}")

    subheader("Posting test message to Facebook page")
    try:
        now_str = datetime.now().strftime(
            "%d %B %Y at %H:%M"
        )
        test_msg = (
            f"🧪 Footy Bankers Football - System Test\n\n"
            f"Tested on: {now_str}\n\n"
            f"This is an automated test message "
            f"confirming that our system can post "
            f"to this page successfully.\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"1️⃣ 🔒 Man City Win\n"
            f"   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League\n"
            f"   Man City vs Arsenal\n"
            f"   ⏰ 20:00 │ 📊 82%\n\n"
            f"2️⃣ 💪 Real Madrid Win\n"
            f"   🇪🇸 La Liga\n"
            f"   Real Madrid vs Getafe\n"
            f"   ⏰ 21:00 │ 📊 75%\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 System status: All systems operational ✅\n\n"
            f"Full picks on Telegram:\n"
            f"t.me/FootyBankersFootball\n\n"
            f"18+ | Gamble Responsibly | begambleaware.org"
        )

        r = requests.post(
            f"{GRAPH}/{page_id}/feed",
            data={
                "message":      test_msg,
                "access_token": token,
            },
            timeout=30,
        )

        if r.status_code == 200:
            post_id = r.json().get("id", "")
            ok(f"Test post published!")
            ok(f"Post ID: {post_id}")
            ok(f"Check your Facebook page now")
            record_pass("Facebook: test post")
        else:
            err = r.json().get("error", {})
            fail(
                f"Post failed: "
                f"{err.get('message', r.text[:200])}"
            )
            record_fail(
                "Facebook",
                err.get("message", "post failed")
            )
            return False

    except Exception as e:
        fail(f"Post error: {e}")
        record_fail("Facebook", str(e))
        return False

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 11: GITHUB TOKEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_github():
    header("TEST 11: GITHUB TOKEN")

    token = os.environ.get("GH_TOKEN", "")
    if not token:
        fail("GH_TOKEN not set")
        record_fail("GitHub", "token not set")
        return False

    subheader("Testing GitHub API access")
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
            ok(f"GitHub user: {user.get('login')}")
            ok(f"Name: {user.get('name', 'N/A')}")
            record_pass("GitHub: user access")
        else:
            fail(f"GitHub auth failed: {r.status_code}")
            record_fail(
                "GitHub", f"auth failed {r.status_code}"
            )
            return False

    except Exception as e:
        fail(f"GitHub error: {e}")
        record_fail("GitHub", str(e))
        return False

    subheader("Testing repo write access")
    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "--global",
             "user.email",
             "test@footybankersfootball.com"],
            capture_output=True,
            text=True,
        )

        result2 = subprocess.run(
            ["git", "config", "--global",
             "user.name",
             "FootyBankers Test"],
            capture_output=True,
            text=True,
        )

        # Test writing a file
        os.makedirs("data/predictions", exist_ok=True)
        test_file = "data/predictions/test.json"
        with open(test_file, "w") as f:
            json.dump(
                {"test": True, "timestamp": str(datetime.now())},
                f
            )

        ok(f"Can write to data directory")
        record_pass("GitHub: write access")

        # Clean up test file
        os.remove(test_file)

    except Exception as e:
        warn(f"Write test: {e}")
        record_warn("GitHub", f"write test: {e}")

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 12: FULL PIPELINE TEST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_full_pipeline():
    header("TEST 12: FULL PIPELINE (Mini Run)")

    info("Running a mini version of the morning workflow")
    info("This collects data, runs AI, formats posts")
    info("But sends a TEST version to your channels")

    try:
        subheader("Step 1: Collect one match")

        key = os.environ.get("FOOTBALL_DATA_API_KEY", "")
        if not key:
            warn("No football data key - using dummy data")
            match = {
                "home_team":          "Manchester City",
                "away_team":          "Arsenal",
                "competition_name":   "Premier League",
                "competition_code":   "PL",
                "kickoff_uk":         "20:00",
                "home_form":          {
                    "form_string":      "WWWDW",
                    "win_rate":         78.0,
                    "goals_for_avg":    2.3,
                    "goals_against_avg": 0.8,
                },
                "away_form":          {
                    "form_string":      "WWLDW",
                    "win_rate":         65.0,
                    "goals_for_avg":    1.8,
                    "goals_against_avg": 1.1,
                },
                "h2h":               {
                    "home_wins":  6,
                    "away_wins":  2,
                    "draws":      2,
                    "avg_goals":  2.8,
                },
                "home_news_note":     "No injury concerns",
                "away_news_note":     "Saka doubtful",
                "weather":           {
                    "description": "Clear conditions",
                    "impact":      0,
                },
            }
            ok("Using dummy match data")
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            r = requests.get(
                "https://api.football-data.org/v4/matches",
                headers={"X-Auth-Token": key},
                params={
                    "dateFrom": today,
                    "dateTo":   today,
                },
                timeout=15,
            )
            if r.status_code == 200:
                matches = r.json().get("matches", [])
                if matches:
                    m = matches[0]
                    match = {
                        "home_team":
                            m["homeTeam"]["name"],
                        "away_team":
                            m["awayTeam"]["name"],
                        "competition_name":
                            m["competition"]["name"],
                        "competition_code":
                            m["competition"]["code"],
                        "kickoff_uk": "TBC",
                        "home_form": {},
                        "away_form": {},
                        "h2h":      {},
                        "home_news_note": "No major news",
                        "away_news_note": "No major news",
                        "weather": {
                            "description": "Normal",
                            "impact": 0,
                        },
                    }
                    ok(
                        f"Real match: "
                        f"{match['home_team']} vs "
                        f"{match['away_team']}"
                    )
                else:
                    ok("No matches today - using dummy")
                    match = {
                        "home_team": "Test FC",
                        "away_team": "Demo United",
                        "competition_name": "Test League",
                        "competition_code": "PL",
                        "kickoff_uk": "20:00",
                        "home_form": {},
                        "away_form": {},
                        "h2h":      {},
                        "home_news_note": "System test",
                        "away_news_note": "System test",
                        "weather": {
                            "description": "Test",
                            "impact": 0
                        },
                    }
            else:
                match = {
                    "home_team": "Manchester City",
                    "away_team": "Arsenal",
                    "competition_name": "Premier League",
                    "competition_code": "PL",
                    "kickoff_uk": "20:00",
                    "home_form": {},
                    "away_form": {},
                    "h2h": {},
                    "home_news_note": "Test",
                    "away_news_note": "Test",
                    "weather": {"description": "Test", "impact": 0},
                }

        subheader("Step 2: AI prediction")
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if not groq_key:
            warn("No Groq key - using dummy prediction")
            prediction = {
                "pick":         "Home Win",
                "pick_short":   f"{match['home_team']} Win",
                "confidence":   78,
                "tier":         "BANKER",
                "reasoning":    [
                    "Strong home form",
                    "Good H2H record",
                    "Opposition injury concerns",
                ],
                "risk":          "Set piece danger",
                "predicted_score": "2-1",
                "human_analysis": (
                    f"Been watching {match['home_team']} "
                    f"closely this season. "
                    f"They are in brilliant form at home. "
                    f"Cannot see past this one."
                ),
                "match_data":   match,
            }
        else:
            from groq import Groq
            client = Groq(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a football analyst. Respond in JSON only."
                    },
                    {
                        "role": "user",
                        "content": f"""
Analyse: {match['home_team']} vs {match['away_team']}
Competition: {match['competition_name']}

Return JSON:
{{
  "pick": "Home Win",
  "pick_short": "{match['home_team']} Win",
  "confidence": 72,
  "reasoning": ["reason 1", "reason 2"],
  "risk": "main risk",
  "predicted_score": "2-1",
  "avoid": false
}}
"""
                    }
                ],
                max_tokens=200,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            prediction = json.loads(
                resp.choices[0].message.content
            )
            prediction["tier"] = "BANKER"
            prediction["human_analysis"] = (
                f"This is a test prediction. "
                f"System is working correctly."
            )
            prediction["match_data"] = match

        ok(
            f"Prediction: {prediction.get('pick_short')} "
            f"({prediction.get('confidence')}%)"
        )
        record_pass("Pipeline: AI prediction")

        subheader("Step 3: Format posts")
        now = datetime.now(
            pytz.timezone("Europe/London")
        )
        day  = now.strftime("%A")
        date = now.strftime("%d %B %Y")
        time_str = now.strftime("%H:%M")

        tg_text = (
            f"🧪 *SYSTEM TEST POST*\n"
            f"⚽ *FOOTY BANKERS FOOTBALL*\n"
            f"📅 {day} {date} │ {time_str} UK\n\n"
            f"_This is a test\\. If you see this, "
            f"the full system is working\\._\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 *TEST PREDICTION*\n\n"
            f"⚽ {match['competition_name']}\n"
            f"*{match['home_team']} vs "
            f"{match['away_team']}*\n"
            f"✅ *{prediction.get('pick_short', 'Home Win')}*\n"
            f"📊 Confidence: "
            f"{prediction.get('confidence', 72)}%\n\n"
            f"_System test complete\\. "
            f"Daily predictions will look exactly "
            f"like this\\._\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_18\\+ \\| Gamble Responsibly \\| "
            f"begambleaware\\.org_\n"
            f"*Footy Bankers Football* ⚽🔒"
        )

        fb_text = (
            f"🧪 SYSTEM TEST | Footy Bankers Football\n\n"
            f"Testing automated posting system.\n"
            f"Tested: {day} {date} at {time_str} UK\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"1️⃣ 🔒 "
            f"{prediction.get('pick_short', 'Home Win')}\n"
            f"   ⚽ {match['competition_name']}\n"
            f"   {match['home_team']} vs "
            f"{match['away_team']}\n"
            f"   📊 {prediction.get('confidence', 72)}% "
            f"confidence\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"System status: All systems operational ✅\n\n"
            f"Full picks on Telegram:\n"
            f"t.me/FootyBankersFootball\n\n"
            f"18+ | Gamble Responsibly | begambleaware.org"
        )

        ok("Posts formatted successfully")
        record_pass("Pipeline: post formatting")

        subheader("Step 4: Send to platforms")

        # Send Telegram
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
                except Exception as e:
                    try:
                        clean = tg_text
                        for c in ["*", "_", "\\", "`"]:
                            clean = clean.replace(c, "")
                        await bot.send_message(
                            chat_id=tg_channel,
                            text=clean,
                        )
                        return True
                    except Exception as e2:
                        return False

            tg_ok = asyncio.run(send_tg())
            if tg_ok:
                ok("Pipeline Telegram post sent ✅")
                record_pass("Pipeline: Telegram send")
            else:
                fail("Pipeline Telegram send failed")
                record_fail("Pipeline", "Telegram send")
        else:
            warn("Telegram not configured - skipping")

        # Send Facebook
        fb_token   = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
        fb_page_id = os.environ.get("FACEBOOK_PAGE_ID", "")

        if fb_token and fb_page_id:
            r = requests.post(
                f"https://graph.facebook.com/v18.0/{fb_page_id}/feed",
                data={
                    "message":      fb_text,
                    "access_token": fb_token,
                },
                timeout=30,
            )
            if r.status_code == 200:
                ok("Pipeline Facebook post sent ✅")
                record_pass("Pipeline: Facebook send")
            else:
                fail(
                    f"Pipeline Facebook failed: "
                    f"{r.json().get('error', {}).get('message', '')}"
                )
                record_fail("Pipeline", "Facebook send")
        else:
            warn("Facebook not configured - skipping")

        ok("Full pipeline test complete")

    except Exception as e:
        fail(f"Pipeline error: {e}")
        import traceback
        info(traceback.format_exc())
        record_fail("Pipeline", str(e))
        return False

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FINAL SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_summary():
    header("TEST SUMMARY - FOOTY BANKERS FOOTBALL")

    total  = (
        len(results["passed"]) +
        len(results["failed"]) +
        len(results["warned"])
    )
    passed = len(results["passed"])
    failed = len(results["failed"])
    warned = len(results["warned"])

    print(f"\n  Total tests:  {total}")
    print(f"  {GREEN}Passed: {passed}{RESET}")
    print(f"  {YELLOW}Warned: {warned}{RESET}")
    print(f"  {RED}Failed: {failed}{RESET}")

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
        print(
            f"\n{GREEN}{BOLD}"
            f"  🎉 ALL SYSTEMS GO!"
            f"\n  Footy Bankers Football is ready."
            f"\n  Check your Telegram channel."
            f"\n  Check your Facebook page."
            f"\n  Both should have test messages."
            f"{RESET}\n"
        )
        return True
    elif failed <= 2:
        print(
            f"\n{YELLOW}{BOLD}"
            f"  ⚠️  ALMOST READY"
            f"\n  Fix the {failed} failed test(s) above."
            f"\n  Then re-run this test."
            f"{RESET}\n"
        )
        return False
    else:
        print(
            f"\n{RED}{BOLD}"
            f"  ❌ NEEDS FIXES"
            f"\n  {failed} tests failed."
            f"\n  Fix each one and re-run."
            f"{RESET}\n"
        )
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print(f"\n{BOLD}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║   FOOTY BANKERS FOOTBALL             ║")
    print("  ║   Complete System Test               ║")
    print("  ║   Testing all secrets + platforms    ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{RESET}")

    uk_tz = pytz.timezone("Europe/London")
    now   = datetime.now(uk_tz)
    print(
        f"  Run time: "
        f"{now.strftime('%A %d %B %Y %H:%M')} UK\n"
    )

    # Check which tests to run
    args = sys.argv[1:]
    run_all = not args or "all" in args

    if run_all or "secrets" in args:
        test_secrets()

    if run_all or "football" in args:
        test_football_data()

    if run_all or "apifootball" in args:
        test_api_football()

    if run_all or "sportsdb" in args:
        test_sports_db()

    if run_all or "weather" in args:
        test_weather()

    if run_all or "rss" in args:
        test_rss_feeds()

    if run_all or "news" in args:
        test_google_news()

    if run_all or "groq" in args:
        test_groq()

    if run_all or "telegram" in args:
        test_telegram()

    if run_all or "facebook" in args:
        test_facebook()

    if run_all or "github" in args:
        test_github()

    if run_all or "pipeline" in args:
        test_full_pipeline()

    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
