import pytz

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTY BANKERS FOOTBALL
# Configuration - Final Version
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Brand
BRAND_NAME      = "Footy Bankers Football"
BRAND_SHORT     = "FootyBankers"
BRAND_TAGLINE   = "Data. Predictions. Football."
BRAND_EMOJI     = "⚽🔒"
TELEGRAM_HANDLE = "@FootyBankersFootball"
TELEGRAM_LINK   = "https://t.me/FootyBankersFootball"
FACEBOOK_HANDLE = "Footy Bankers Football"
TWITTER_HANDLE  = "@FootyBankersFC"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AFFILIATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AFFILIATE_LINK = "https://stake.com/?c=stakesoccer24"
AFFILIATE_NAME = "Stake"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DISCLAIMER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DISCLAIMER = "18+ | Gamble Responsibly | begambleaware.org"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIMEZONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIMEZONE = pytz.timezone("Europe/London")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PICKS SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TELEGRAM_MIN_PICKS = 3
TELEGRAM_MAX_PICKS = 20
FACEBOOK_PICKS     = 5
MIN_CONFIDENCE     = 55

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIDENCE TIERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BANKER_MIN = 75
STRONG_MIN = 65
VALUE_MIN  = 55

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GROQ MODELS - Verified Working July 2026
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GROQ_PRIMARY_MODEL  = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"
GROQ_FAST_MODEL     = "openai/gpt-oss-120b"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCORING WEIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WEIGHTS = {
    "form":      0.25,
    "h2h":       0.20,
    "home_away": 0.15,
    "goals_avg": 0.15,
    "news":      0.10,
    "rest":      0.10,
    "weather":   0.05,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POSTING SCHEDULE (UK TIME)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MORNING_HOUR   = 8
MORNING_MINUTE = 0
EVENING_HOUR   = 22
EVENING_MINUTE = 30

# Random delay to look human (minutes)
DELAY_MIN = 2
DELAY_MAX = 25

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA SOURCES - Flashscore FIRST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA_SOURCES = [
    "sportdb_flashscore",
    "football_data_org",
    "sports_db",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAJOR TOURNAMENTS
# AI will always cover these regardless of data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAJOR_TOURNAMENTS = [
    "world cup",
    "fifa world cup",
    "worldcup",
    "champions league",
    "uefa champions league",
    "europa league",
    "euros",
    "euro 2024",
    "euro 2026",
    "copa america",
    "africa cup",
    "afcon",
    "premier league",
    "la liga",
    "bundesliga",
    "serie a",
    "ligue 1",
    "fa cup",
    "carabao cup",
    "conference league",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LEAGUES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEAGUES = {
    "PL":  {"name": "Premier League",    "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "tier": 1},
    "PD":  {"name": "La Liga",           "flag": "🇪🇸", "tier": 1},
    "BL1": {"name": "Bundesliga",        "flag": "🇩🇪", "tier": 1},
    "SA":  {"name": "Serie A",           "flag": "🇮🇹", "tier": 1},
    "FL1": {"name": "Ligue 1",           "flag": "🇫🇷", "tier": 1},
    "CL":  {"name": "Champions League",  "flag": "🏆",  "tier": 1},
    "WC":  {"name": "World Cup",         "flag": "🌍",  "tier": 1},
    "EC":  {"name": "Euros",             "flag": "🇪🇺", "tier": 1},
    "EL":  {"name": "Europa League",     "flag": "🟠",  "tier": 2},
    "ELC": {"name": "Championship",      "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "tier": 2},
    "PPL": {"name": "Primeira Liga",     "flag": "🇵🇹", "tier": 2},
    "DED": {"name": "Eredivisie",        "flag": "🇳🇱", "tier": 2},
    "BSA": {"name": "Brasileirao",       "flag": "🇧🇷", "tier": 2},
    "CLI": {"name": "Copa Libertadores", "flag": "🌎",  "tier": 3},
    "MLS": {"name": "MLS",              "flag": "🇺🇸", "tier": 3},
    "FAC": {"name": "FA Cup",            "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "tier": 3},
    "COL": {"name": "Carabao Cup",       "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "tier": 3},
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RSS FEEDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RSS_FEEDS = {
    "bbc":       "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "sky":       "https://www.skysports.com/rss/12040",
    "guardian":  "https://www.theguardian.com/football/rss",
    "talksport": "https://talksport.com/feed/",
    "mirror":    "https://www.mirror.co.uk/sport/football/?service=rss",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KEYWORDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INJURY_KEYWORDS = [
    "injured", "injury", "out", "doubt", "miss",
    "absent", "ruled out", "fitness", "suspended",
    "ban", "unavailable", "knock", "strain",
    "hamstring", "ankle", "knee", "calf", "thigh",
]

POSITIVE_KEYWORDS = [
    "returns", "fit", "available", "back",
    "trained", "recovered", "return", "ready",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STORAGE PATHS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PREDICTIONS_DIR = "data/predictions"
RESULTS_DIR     = "data/results"
ACCURACY_FILE   = "data/accuracy.json"
TOPICS_FILE     = "data/used_topics.json"
TEAM_NAMES_FILE = "data/static/team_names.json"
STADIUMS_FILE   = "data/static/stadiums.json"
