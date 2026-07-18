import re

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
    if not name:
        return ""
    cleaned = name.lower().strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    for standard, variants in TEAM_NAME_MAP.items():
        if cleaned in [v.lower() for v in variants]:
            return standard
        if cleaned == standard:
            return standard
    return cleaned


def match_names(name1: str, name2: str) -> bool:
    return normalise(name1) == normalise(name2)
