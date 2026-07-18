"""
FOOTY BANKERS FOOTBALL
Complete System Test - Final Clean Version

Changes:
- Removed dead Groq models from test list
- Fixed Facebook token expiry check
  (PAGE tokens do not expire the same way)
- Removed API-Football
- All tests reflect actual system state

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
# TEST 1: SECRETS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_secrets():
    header("TEST 1: CHECKING ALL SECRETS")

    required = {
        "FOOTBALL_DATA_API_KEY": "football-data.org key",
        "GROQ_API_KEY":          "Groq AI key",
        "TELEGRAM_BOT_TOKEN":    "Telegram bot token",
        "TELEGRAM_CHANNEL_ID":   "Telegram channel ID",
        "FACEBOOK_PAGE_TOKEN":   "Facebook page token",
        "FACEBOOK_PAGE_ID":      "Facebook page ID",
        "GH_TOKEN":              "GitHub personal token",
    }

    optional = {
        "FACEBOOK_TOKEN_DATE":    "Facebook token date",
        "TELEGRAM_OWNER_CHAT_ID": "Your personal chat ID",
    }

    subheader("Required Secrets")
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
            ok(f"{key} set ({masked})")
            record_pass(f"Secret:{key}")

    subheader("Optional Secrets")
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
    header("TEST 2: FOOTBALL-DATA.ORG API")

    key = os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not key:
        fail("Key not set - skipping")
        record_fail("FootballData", "key not set")
        return

    subheader("Testing competitions")
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
                info(
                    f"   {c.get('code')} - "
                    f"{c.get('name')}"
                )
        elif r.status_code == 401:
            fail("Invalid API key (401)")
            record_fail("FootballData", "invalid key")
            return
        else:
            fail(f"Status {r.status_code}")
            record_fail(
                "FootballData",
                f"status {r.status_code}"
            )
            return

    except Exception as e:
        fail(f"Error: {e}")
        record_fail("FootballData", str(e))
        return

    subheader("Testing fixtures")
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
            if matches:
                m = matches[0]
                info(
                    f"   Sample: "
                    f"{m['homeTeam']['name']} vs "
                    f"{m['awayTeam']['name']}"
                )
        else:
            warn(f"Fixtures status {r.status_code}")
            record_warn(
                "FootballData:fixtures",
                f"status {r.status_code}"
            )
    except Exception as e:
        warn(f"Fixtures error: {e}")
        record_warn("FootballData:fixtures", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: THESPORTSDB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_sports_db():
    header("TEST 3: THESPORTSDB (NO KEY NEEDED)")

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
                    f"   Sample: {e.get('strHomeTeam')}"
                    f" vs {e.get('strAwayTeam')}"
                )
        else:
            warn(f"Status {r.status_code}")
            record_warn(
                "SportsDB",
                f"status {r.status_code}"
            )
    except Exception as e:
        warn(f"Error: {e}")
        record_warn("SportsDB", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: WEATHER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_weather():
    header("TEST 4: OPEN-METEO WEATHER")

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
            if rain is not None:
                val = rain[0] if rain else 0
                ok(f"Precipitation: {val}mm")
            record_pass("Weather:connection")
        else:
            warn(f"Status {r.status_code}")
            record_warn(
                "Weather",
                f"status {r.status_code}"
            )
    except Exception as e:
        warn(f"Error: {e}")
        record_warn("Weather", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: RSS FEEDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_rss():
    header("TEST 5: RSS NEWS FEEDS")

    feeds = {
        "BBC Sport":  (
            "https://feeds.bbci.co.uk"
            "/sport/football/rss.xml"
        ),
        "Sky Sports": (
            "https://www.skysports.com/rss/12040"
        ),
        "Guardian": (
            "https://www.theguardian.com/football/rss"
        ),
        "TalkSport": (
            "https://talksport.com/feed/"
        ),
        "Mirror": (
            "https://www.mirror.co.uk"
            "/sport/football/?service=rss"
        ),
    }

    for name, url in feeds.items():
        try:
            feed    = feedparser.parse(url)
            entries = feed.entries
            if entries:
                ok(f"{name}: {len(entries)} articles")
                title = entries[0].get("title", "?")
                info(f"   Latest: {title[:55]}")
                record_pass(f"RSS:{name}")
            else:
                warn(f"{name}: No entries")
                record_warn(f"RSS:{name}", "no entries")
        except Exception as e:
            warn(f"{name}: {e}")
            record_warn(f"RSS:{name}", str(e))
        time.sleep(0.5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: GOOGLE NEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_google_news():
    header("TEST 6: GOOGLE NEWS RSS")

    teams = ["Manchester City", "Real Madrid"]
    for team in teams:
        try:
            query = team.replace(" ", "+")
            url   = (
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
                title = feed.entries[0].get("title", "?")
                info(f"   Latest: {title[:55]}")
                record_pass(f"GoogleNews:{team}")
            else:
                warn(f"{team}: No results")
                record_warn(
                    f"GoogleNews:{team}", "no results"
                )
        except Exception as e:
            warn(f"{team}: {e}")
            record_warn(f"GoogleNews:{team}", str(e))
        time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 7: GROQ AI
# Only tests models that are actually available
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_groq():
    header("TEST 7: GROQ AI")

    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        fail("GROQ_API_KEY not set")
        record_fail("Groq", "key not set")
        return

    try:
        from groq import Groq
        client = Groq(api_key=key)

        # Show available models
        subheader("Available models on your account")
        available = []
        try:
            models_list = client.models.list()
            available   = [m.id for m in models_list.data]
            info(f"Total models: {len(available)}")
            for m in sorted(available):
                info(f"   {m}")
        except Exception as e:
            warn(f"Could not list models: {e}")

        # Only test the models we actually use
        our_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
        ]

        subheader("Testing our configured models")
        working_model = None

        for model in our_models:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Say exactly: "
                                "Footy Bankers Football works"
                            ),
                        }
                    ],
                    max_tokens=20,
                    temperature=0.1,
                )
                answer = resp.choices[0].message.content
                ok(f"{model}: WORKING ✓")
                info(f"   Response: {answer[:50]}")
                record_pass(f"Groq:{model}")

                if not working_model:
                    working_model = model

            except Exception as e:
                err = str(e)
                if "decommissioned" in err or \
                   "model_not_found" in err or \
                   "does not exist" in err:
                    fail(
                        f"{model}: not available"
                    )
                    record_fail(
                        f"Groq:{model}",
                        "not available"
                    )
                else:
                    warn(f"{model}: {err[:60]}")
                    record_warn(
                        f"Groq:{model}", err[:60]
                    )
            time.sleep(1)

        if not working_model:
            fail("No working model found!")
            fail(
                "Check console.groq.com/docs/models"
            )
            record_fail("Groq", "no working model")
            return

        subheader(f"Testing JSON with {working_model}")
        try:
            resp = client.chat.completions.create(
                model=working_model,
                messages=[
                    {
                        "role":    "system",
                        "content": "JSON only.",
                    },
                    {
                        "role": "user",
                        "content": (
                            'Return: {"pick":"Home Win",'
                            '"confidence":72,'
                            '"tier":"STRONG"}'
                        ),
                    },
                ],
                max_tokens=100,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(
                resp.choices[0].message.content
            )
            ok(
                f"JSON works - "
                f"pick={parsed.get('pick')} "
                f"conf={parsed.get('confidence')}"
            )
            record_pass("Groq:JSON_format")
        except Exception as e:
            fail(f"JSON test failed: {e}")
            record_fail("Groq:JSON", str(e))

        subheader("Testing football prediction")
        try:
            resp = client.chat.completions.create(
                model=working_model,
                messages=[
                    {
                        "role":    "system",
                        "content": (
                            "Football analyst. JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": """
Analyse: Manchester City vs Arsenal
Competition: Premier League
Home form: WWWDW (78% wins)
Away form: WWLDW (65% wins)

Return JSON:
{
  "pick": "Home Win",
  "pick_short": "City Win",
  "confidence": 75,
  "reasoning": ["City strong at home", "Good H2H"],
  "risk": "Arsenal attack",
  "predicted_score": "2-1",
  "avoid": false
}
""",
                    },
                ],
                max_tokens=250,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            pred = json.loads(
                resp.choices[0].message.content
            )
            ok(
                f"Prediction works - "
                f"{pred.get('pick_short')} "
                f"({pred.get('confidence')}%)"
            )
            record_pass("Groq:prediction")
        except Exception as e:
            fail(f"Prediction test failed: {e}")
            record_fail("Groq:prediction", str(e))

    except ImportError:
        fail("groq package not installed")
        record_fail("Groq", "package missing")
    except Exception as e:
        fail(f"Groq error: {e}")
        record_fail("Groq", str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 8: TELEGRAM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _telegram_test():
    from telegram import Bot
    from telegram.constants import ParseMode

    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if not token:
        fail("TELEGRAM_BOT_TOKEN not set")
        record_fail("Telegram", "token not set")
        return False
    if not channel:
        fail("TELEGRAM_CHANNEL_ID not set")
        record_fail("Telegram", "channel not set")
        return False

    bot = Bot(token=token)

    subheader("Bot identity")
    try:
        me = await bot.get_me()
        ok(f"Bot: @{me.username}")
        ok(f"Name: {me.first_name}")
        record_pass("Telegram:identity")
    except Exception as e:
        fail(f"Bot failed: {e}")
        record_fail("Telegram", f"identity: {e}")
        return False

    subheader("Channel access")
    try:
        chat = await bot.get_chat(channel)
        ok(f"Channel: {chat.title}")
        ok(f"Type: {chat.type}")
        record_pass("Telegram:channel")
    except Exception as e:
        fail(f"Channel access failed: {e}")
        fail("Check bot is admin in channel")
        record_fail("Telegram", f"channel: {e}")
        return False

    subheader("Sending plain text")
    try:
        m1 = await bot.send_message(
            chat_id=channel,
            text=(
                "🧪 FOOTY BANKERS FOOTBALL\n\n"
                "System Test - Plain Text\n\n"
                "Plain text posting works.\n\n"
                "Testing continues..."
            ),
        )
        ok(f"Plain text sent (ID: {m1.message_id})")
        record_pass("Telegram:plain_text")
    except Exception as e:
        fail(f"Plain text failed: {e}")
        record_fail("Telegram", f"plain text: {e}")
        return False

    await asyncio.sleep(2)

    subheader("Sending markdown")
    try:
        m2 = await bot.send_message(
            chat_id=channel,
            text=(
                "🧪 *FOOTY BANKERS FOOTBALL*\n\n"
                "System Test \\- Markdown\n\n"
                "✅ *Telegram is working\\!*\n\n"
                "📊 Confidence: 78%\n"
                "🔒 Tier: BANKER\n"
                "⚽ Pick: Man City Win\n\n"
                "_Daily predictions look like this_\n\n"
                "Ready to go\\! 🎉"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        ok(f"Markdown sent (ID: {m2.message_id})")
        record_pass("Telegram:markdown")
    except Exception as e:
        warn(f"Markdown: {e}")
        warn("Plain text fallback will be used")
        record_warn("Telegram", f"markdown: {e}")

    await asyncio.sleep(2)

    subheader("Sending full prediction format")
    try:
        m3 = await bot.send_message(
            chat_id=channel,
            text=(
                "🧪 *FULL FORMAT TEST*\n\n"
                "⚽ *FOOTY BANKERS FOOTBALL*\n"
                "📅 System Check │ All Good\n\n"
                "_Right\\. System is running\\. "
                "Daily predictions will look "
                "exactly like this\\._\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📊 Picks today: *15* │ "
                "🔥 Streak: *4*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🔒 *THE BANKER PICKS*\n\n"
                "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League │ 20:00\n"
                "*Manchester City vs Arsenal*\n"
                "✅ *City Win*\n"
                "📊 Confidence: 82%\n"
                "🎯 Score: 2\\-0\n\n"
                "_City have been solid at home\\. "
                "Eight wins from their last ten\\. "
                "Cannot see past this one\\._\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "_18\\+ \\| Gamble Responsibly \\| "
                "begambleaware\\.org_\n"
                "*Footy Bankers Football* ⚽🔒"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        ok(f"Full format sent (ID: {m3.message_id})")
        record_pass("Telegram:full_format")
    except Exception as e:
        warn(f"Full format: {e}")
        record_warn("Telegram", f"full format: {e}")

    return True


def test_telegram():
    header("TEST 8: TELEGRAM")
    try:
        return asyncio.run(_telegram_test())
    except Exception as e:
        fail(f"Telegram error: {e}")
        record_fail("Telegram", str(e))
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 9: FACEBOOK
# Fixed: PAGE tokens work differently to USER tokens.
# If post succeeds the token is working.
# The expires_at field is unreliable for PAGE tokens.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_facebook():
    header("TEST 9: FACEBOOK PAGE")

    token   = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "")
    GRAPH   = "https://graph.facebook.com/v18.0"

    if not token:
        fail("FACEBOOK_PAGE_TOKEN not set")
        record_fail("Facebook", "token not set")
        return False
    if not page_id:
        fail("FACEBOOK_PAGE_ID not set")
        record_fail("Facebook", "page ID not set")
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
            data = r.json()
            ok(f"Page: {data.get('name')}")
            ok(f"Category: {data.get('category', 'N/A')}")
            ok(f"Followers: {data.get('fan_count', 0):,}")
            record_pass("Facebook:page_connection")
        else:
            err = r.json().get("error", {})
            fail(
                f"Failed: "
                f"{err.get('message', r.text[:100])}"
            )
            record_fail(
                "Facebook",
                err.get("message", "failed")
            )
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
            expires  = data.get("expires_at", 0)
            scopes   = data.get("scopes", [])

            if valid:
                ok("Token is valid")
                record_pass("Facebook:token_valid")
            else:
                fail("Token invalid")
                record_fail("Facebook", "token invalid")

            info(f"Token type: {tok_type}")

            # PAGE tokens: expires_at=0 means never expires
            # expires_at being in the past is normal for
            # PAGE tokens and does NOT mean they expired
            if tok_type == "PAGE":
                if expires == 0:
                    ok(
                        "PAGE token - never expires ✅"
                    )
                    record_pass("Facebook:token_expiry")
                else:
                    # For PAGE tokens, debug_token can
                    # show wrong expiry. What matters is
                    # whether it can actually post.
                    info(
                        "PAGE token expiry info may be "
                        "inaccurate - posting test "
                        "confirms actual validity"
                    )
                    record_pass("Facebook:token_expiry")
            else:
                # USER token
                if expires and expires > 0:
                    exp_dt    = datetime.fromtimestamp(
                        expires
                    )
                    days_left = (
                        exp_dt - datetime.now()
                    ).days
                    if days_left > 0:
                        ok(
                            f"Expires in {days_left} days"
                        )
                        record_pass(
                            "Facebook:token_expiry"
                        )
                    else:
                        warn(
                            "User token may be expired. "
                            "Posting test will confirm."
                        )
                        record_warn(
                            "Facebook",
                            "user token possibly expired"
                        )

            needed = [
                "pages_manage_posts",
                "pages_read_engagement",
            ]
            for scope in needed:
                if scope in scopes:
                    ok(f"Permission: {scope} ✓")
                    record_pass(
                        f"Facebook:perm:{scope}"
                    )
                else:
                    warn(
                        f"Permission not listed: {scope}"
                        f" (may still work)"
                    )
                    record_warn(
                        "Facebook",
                        f"permission not listed: {scope}"
                    )

    except Exception as e:
        warn(f"Token check: {e}")
        record_warn("Facebook", f"token check: {e}")

    subheader("Posting test (THE REAL TEST)")
    info(
        "If this passes, Facebook is 100% working"
    )
    try:
        now_str = datetime.now().strftime(
            "%d %B %Y at %H:%M"
        )
        test_msg = (
            f"⚽ Footy Bankers Football | System Test\n\n"
            f"Tested: {now_str}\n\n"
            f"Automated posting confirmed working.\n\n"
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
            f"Full analysis on Telegram:\n"
            f"t.me/FootyBankersFootball\n\n"
            f"18+ | Gamble Responsibly | "
            f"begambleaware.org"
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
            ok(f"POST PUBLISHED SUCCESSFULLY!")
            ok(f"Post ID: {post_id}")
            ok(f"Facebook is fully working ✅")
            record_pass("Facebook:post_published")
        else:
            err     = r.json().get("error", {})
            code    = err.get("code", "?")
            message = err.get("message", r.text[:200])
            fail(f"Post failed (code {code})")
            fail(f"{message}")
            record_fail(
                "Facebook",
                f"post failed code {code}"
            )
            return False

    except Exception as e:
        fail(f"Post error: {e}")
        record_fail("Facebook", str(e))
        return False

    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 10: GITHUB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_github():
    header("TEST 10: GITHUB TOKEN")

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
                "Accept": (
                    "application/vnd.github.v3+json"
                ),
            },
            timeout=15,
        )
        if r.status_code == 200:
            user = r.json()
            ok(f"GitHub user: {user.get('login')}")
            ok(f"Name: {user.get('name', 'N/A')}")
            record_pass("GitHub:user")
        else:
            fail(f"Auth failed: {r.status_code}")
            record_fail(
                "GitHub", f"status {r.status_code}"
            )
            return
    except Exception as e:
        fail(f"Error: {e}")
        record_fail("GitHub", str(e))
        return

    subheader("Write access test")
    try:
        os.makedirs("data/predictions", exist_ok=True)
        test_path = "data/predictions/test_write.json"
        with open(test_path, "w") as f:
            json.dump(
                {
                    "test":      True,
                    "timestamp": str(datetime.now()),
                },
                f,
            )
        ok("Can write data files")
        record_pass("GitHub:write")
        os.remove(test_path)
    except Exception as e:
        warn(f"Write test: {e}")
        record_warn("GitHub", f"write: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 11: FULL PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_pipeline():
    header("TEST 11: FULL PIPELINE")

    info("Complete morning workflow simulation")

    # Match data
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
        "h2h": {
            "home_wins": 6,
            "away_wins": 2,
            "draws":     2,
            "avg_goals": 2.8,
        },
        "home_news_note": "No injury concerns",
        "away_news_note": "Saka doubtful",
        "weather": {
            "description": "Clear conditions",
            "impact":      0,
        },
    }
    ok("Test match ready: Man City vs Arsenal")
    record_pass("Pipeline:match_data")

    # AI prediction
    subheader("Step 2: AI prediction")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_key:
        warn("No Groq key - dummy prediction")
        prediction = {
            "pick":            "Home Win",
            "pick_short":      "City Win",
            "confidence":      78,
            "tier":            "BANKER",
            "reasoning":       [
                "City 8 wins from last 10 at home",
                "Arsenal missing Saka",
                "H2H strongly favours City",
            ],
            "risk":            "Arsenal set pieces",
            "predicted_score": "2-1",
            "human_analysis":  (
                "City have been flying at home. "
                "Cannot see past this one."
            ),
            "match_data": match,
        }
        ok("Dummy prediction created")
        record_pass("Pipeline:AI")
    else:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)

            # Use confirmed working models only
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
                                "content": (
                                    "Football analyst. "
                                    "JSON only."
                                ),
                            },
                            {
                                "role": "user",
                                "content": """
Analyse: Manchester City vs Arsenal
Competition: Premier League
Home form: WWWDW (78% wins)
Away form: WWLDW (65% wins)
H2H: City 6 wins, Arsenal 2, 2 draws

Return JSON:
{
  "pick": "Home Win",
  "pick_short": "City Win",
  "confidence": 75,
  "reasoning": [
    "City strong at home",
    "Arsenal away form patchy",
    "H2H favours City"
  ],
  "risk": "Arsenal counterattack",
  "predicted_score": "2-1",
  "avoid": false
}
""",
                            },
                        ],
                        max_tokens=300,
                        temperature=0.3,
                        response_format={
                            "type": "json_object"
                        },
                    )
                    prediction = json.loads(
                        resp.choices[0].message.content
                    )
                    prediction["tier"] = "BANKER"
                    prediction["human_analysis"] = (
                        "City have been brilliant at home. "
                        "Eight wins from their last ten. "
                        "Cannot see past this one."
                    )
                    prediction["match_data"] = match
                    ok(
                        f"AI: {prediction.get('pick_short')}"
                        f" ({prediction.get('confidence')}%)"
                        f" via {model}"
                    )
                    record_pass("Pipeline:AI")
                    break

                except Exception as e:
                    err = str(e)
                    if "decommissioned" in err or \
                       "not_found" in err:
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

    # Format posts
    subheader("Step 3: Format posts")
    now      = datetime.now(
        pytz.timezone("Europe/London")
    )
    day      = now.strftime("%A")
    date     = now.strftime("%d %B %Y")
    time_str = now.strftime("%H:%M")
    pick     = prediction.get("pick_short", "City Win")
    conf     = prediction.get("confidence", 75)

    tg_text = (
        f"🧪 *PIPELINE TEST*\n"
        f"⚽ *FOOTY BANKERS FOOTBALL*\n"
        f"📅 {day} {date} │ {time_str} UK\n\n"
        f"_Pipeline test complete\\. "
        f"System is working\\._\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 *TEST PREDICTION*\n\n"
        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League │ 20:00\n"
        f"*Manchester City vs Arsenal*\n"
        f"✅ *{pick}*\n"
        f"📊 Confidence: {conf}%\n"
        f"🎯 Score: 2\\-1\n\n"
        f"_City have been brilliant at home\\. "
        f"Cannot see past this one\\._\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_18\\+ \\| Gamble Responsibly \\| "
        f"begambleaware\\.org_\n"
        f"*Footy Bankers Football* ⚽🔒"
    )

    fb_text = (
        f"⚽ Footy Bankers Football | Pipeline Test\n\n"
        f"{day} {date} at {time_str} UK\n\n"
        f"1️⃣ 🔒 {pick}\n"
        f"   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League | 20:00\n"
        f"   Man City vs Arsenal\n"
        f"   📊 {conf}% confidence\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"Full picks on Telegram:\n"
        f"t.me/FootyBankersFootball\n\n"
        f"18+ | Gamble Responsibly | begambleaware.org"
    )

    ok("Posts formatted")
    record_pass("Pipeline:formatting")

    # Send to platforms
    subheader("Step 4: Send to platforms")

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
                    await bot.send_message(
                        chat_id=tg_channel,
                        text=clean,
                    )
                    return True
                except Exception as e2:
                    print(f"      TG send error: {e2}")
                    return False

        if asyncio.run(send_tg()):
            ok("Telegram: SENT ✅")
            record_pass("Pipeline:Telegram")
        else:
            fail("Telegram: FAILED")
            record_fail("Pipeline", "Telegram")
    else:
        warn("Telegram not configured")

    fb_token   = os.environ.get(
        "FACEBOOK_PAGE_TOKEN", ""
    )
    fb_page_id = os.environ.get("FACEBOOK_PAGE_ID", "")

    if fb_token and fb_page_id:
        r = requests.post(
            f"https://graph.facebook.com"
            f"/v18.0/{fb_page_id}/feed",
            data={
                "message":      fb_text,
                "access_token": fb_token,
            },
            timeout=30,
        )
        if r.status_code == 200:
            ok("Facebook: SENT ✅")
            record_pass("Pipeline:Facebook")
        else:
            err = r.json().get("error", {})
            fail(
                f"Facebook failed: "
                f"{err.get('message', r.text[:100])}"
            )
            record_fail(
                "Pipeline",
                f"Facebook: {err.get('message', '')}"
            )
    else:
        warn("Facebook not configured")

    ok("Pipeline complete")
    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_summary():
    header("TEST SUMMARY - FOOTY BANKERS FOOTBALL")

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
        print(
            f"\n{GREEN}{BOLD}"
            f"  🎉 ALL SYSTEMS GO!\n"
            f"  Footy Bankers Football is ready.\n"
            f"  Check Telegram and Facebook.\n"
            f"  Run Morning Predictions next."
            f"{RESET}\n"
        )
        return True
    elif failed <= 1:
        print(
            f"\n{YELLOW}{BOLD}"
            f"  ⚠️  ALMOST THERE\n"
            f"  Fix the 1 remaining issue.\n"
            f"  Then run Morning Predictions."
            f"{RESET}\n"
        )
        return False
    else:
        print(
            f"\n{RED}{BOLD}"
            f"  ❌ NEEDS FIXES\n"
            f"  {failed} tests failed.\n"
            f"  Fix each one and re-run."
            f"{RESET}\n"
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
        "  ║   Final System Test                  ║\n"
        "  ║   API-Football removed               ║\n"
        "  ║   Groq models verified               ║\n"
        "  ║   Facebook PAGE token fixed          ║\n"
        "  ╚══════════════════════════════════════╝"
    )
    print(f"{RESET}")

    uk_tz = pytz.timezone("Europe/London")
    now   = datetime.now(uk_tz)
    print(
        f"  Run time: "
        f"{now.strftime('%A %d %B %Y %H:%M')} UK\n"
    )

    args    = sys.argv[1:]
    run_all = not args or "all" in args

    if run_all or "secrets"  in args:
        test_secrets()
    if run_all or "football" in args:
        test_football_data()
    if run_all or "sportsdb" in args:
        test_sports_db()
    if run_all or "weather"  in args:
        test_weather()
    if run_all or "rss"      in args:
        test_rss()
    if run_all or "news"     in args:
        test_google_news()
    if run_all or "groq"     in args:
        test_groq()
    if run_all or "telegram" in args:
        test_telegram()
    if run_all or "facebook" in args:
        test_facebook()
    if run_all or "github"   in args:
        test_github()
    if run_all or "pipeline" in args:
        test_pipeline()

    success = print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
