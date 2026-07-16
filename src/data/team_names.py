import json
import os
import re


# Core normalisation dictionary
TEAM_NAME_MAP = {
    "manchester city": [
        "Manchester City FC", "Manchester City",
        "Man City", "Man. City", "MCFC", "City",
    ],
    "manchester united": [
        "Manchester United FC", "Manchester United",
        "Man United", "Man Utd", "MUFC",
    ],
    "arsenal": [
        "Arsenal FC", "Arsenal", "The Gunners",
    ],
    "liverpool": [
        "Liverpool FC", "Liverpool", "LFC",
    ],
    "chelsea": [
        "Chelsea FC", "Chelsea", "The Blues",
    ],
    "tottenham": [
        "Tottenham Hotspur FC", "Tottenham Hotspur",
        "Tottenham", "Spurs", "THFC",
    ],
    "newcastle": [
        "Newcastle United FC", "Newcastle United",
        "Newcastle", "NUFC",
    ],
    "aston villa": [
        "Aston Villa FC", "Aston Villa", "Villa",
    ],
    "west ham": [
        "West Ham United FC", "West Ham United",
        "West Ham", "WHUFC",
    ],
    "brighton": [
        "Brighton & Hove Albion FC",
        "Brighton & Hove Albion",
        "Brighton", "Albion",
    ],
    "real madrid": [
        "Real Madrid CF", "Real Madrid", "Madrid",
    ],
    "barcelona": [
        "FC Barcelona", "Barcelona", "Barca",
    ],
    "atletico madrid": [
        "Club Atletico de Madrid",
        "Atletico Madrid", "Atletico",
    ],
    "bayern munich": [
        "FC Bayern Munchen", "FC Bayern Munich",
        "Bayern Munich", "Bayern",
    ],
    "borussia dortmund": [
        "Borussia Dortmund", "Dortmund", "BVB",
    ],
    "juventus": [
        "Juventus FC", "Juventus", "Juve",
    ],
    "ac milan": [
        "AC Milan", "Milan",
    ],
    "inter milan": [
        "FC Internazionale Milano",
        "Inter Milan", "Inter", "Internazionale",
    ],
    "paris saint-germain": [
        "Paris Saint-Germain FC",
        "Paris Saint-Germain",
        "PSG", "Paris SG",
    ],
}


def normalise(name: str) -> str:
    """
    Convert any team name variant
    to a clean standard form.
    """
    if not name:
        return ""

    cleaned = name.lower().strip()
    cleaned = re.sub(r"\s+", " ", cleaned)

    for standard, variants in TEAM_NAME_MAP.items():
        variants_lower = [v.lower() for v in variants]
        if cleaned in variants_lower:
            return standard
        if cleaned == standard:
            return standard

    return cleaned


def match_names(name1: str, name2: str) -> bool:
    """
    Check if two team name strings
    refer to the same team.
    """
    return normalise(name1) == normalise(name2)


def load_from_file(path: str) -> dict:
    """Load extended name map from JSON file."""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}
