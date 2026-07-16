import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class ApiFootball:
    """
    Secondary source.
    api-football.com free tier.
    100 requests per day.
    """

    BASE = "https://v3.football.api-sports.io"

    def __init__(self):
        self.key = os.environ.get("API_FOOTBALL_KEY", "")
        self.headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key":  self.key,
        }
        self.tz = pytz.timezone("Europe/London")
        self.calls = 0
        self.limit = 85  # Stay under 100

    def _get(self, endpoint: str, params: dict = None):
        if self.calls >= self.limit:
            print("API-Football daily limit reached")
            return None

        try:
            r = requests.get(
                f"{self.BASE}{endpoint}",
                headers=self.headers,
                params=params or {},
                timeout=15,
            )
            self.calls += 1

            if r.status_code == 200:
                return r.json().get("response")
            else:
                print(
                    f"API-Football error {r.status_code}"
                )
                return None

        except Exception as e:
            print(f"API-Football failed: {e}")
            return None

    def get_todays_matches(self) -> list:
        today = datetime.now(self.tz).strftime("%Y-%m-%d")
        data = self._get("/fixtures", {"date": today})
        if not data:
            return []
        return self._parse(data)

    def get_injuries(self, fixture_id: int) -> list:
        data = self._get(
            "/injuries", {"fixture": fixture_id}
        )
        return data or []

    def _parse(self, fixtures: list) -> list:
        out = []
        for f in fixtures:
            try:
                fix = f.get("fixture", {})
                teams = f.get("teams", {})
                league = f.get("league", {})
                ts = fix.get("timestamp")

                if ts:
                    utc_dt = datetime.utcfromtimestamp(ts)
                    utc_dt = utc_dt.replace(
                        tzinfo=pytz.utc
                    )
                    uk_dt = utc_dt.astimezone(self.tz)
                    uk_time = uk_dt.strftime("%H:%M")
                else:
                    uk_dt = None
                    uk_time = "TBC"

                home = teams.get("home", {}).get("name", "")
                away = teams.get("away", {}).get("name", "")

                out.append({
                    "id":               fix.get("id"),
                    "source":           "api_football",
                    "competition_code": str(
                        league.get("id", "")
                    ),
                    "competition_name": league.get("name", ""),
                    "competition_country": league.get(
                        "country", ""
                    ),
                    "home_team":        home,
                    "home_team_norm":   normalise(home),
                    "home_team_id":     teams.get(
                        "home", {}
                    ).get("id"),
                    "away_team":        away,
                    "away_team_norm":   normalise(away),
                    "away_team_id":     teams.get(
                        "away", {}
                    ).get("id"),
                    "kickoff_uk":       uk_time,
                    "kickoff_dt":       uk_dt,
                    "status":           fix.get(
                        "status", {}
                    ).get("short", ""),
                    "venue":            fix.get(
                        "venue", {}
                    ).get("name", ""),
                })
            except Exception as e:
                print(f"API-Football parse error: {e}")
        return out
