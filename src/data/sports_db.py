import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class TheSportsDB:
    """
    Third source - no API key needed.
    thesportsdb.com free tier.
    """

    BASE = "https://www.thesportsdb.com/api/v1/json/3"

    def __init__(self):
        self.tz = pytz.timezone("Europe/London")

    def get_todays_matches(self) -> list:
        today = datetime.now(self.tz).strftime("%Y-%m-%d")
        try:
            r = requests.get(
                f"{self.BASE}/eventsday.php",
                params={"d": today, "s": "Soccer"},
                timeout=10,
            )
            if r.status_code == 200:
                events = r.json().get("events") or []
                return self._parse(events)
            return []
        except Exception as e:
            print(f"SportsDB failed: {e}")
            return []

    def _parse(self, events: list) -> list:
        out = []
        for e in events:
            try:
                t = e.get("strTime", "")
                try:
                    uk_time = datetime.strptime(
                        t, "%H:%M:%S"
                    ).strftime("%H:%M")
                except Exception:
                    uk_time = "TBC"

                home = e.get("strHomeTeam", "")
                away = e.get("strAwayTeam", "")

                if not home or not away:
                    continue

                out.append({
                    "id":               e.get("idEvent"),
                    "source":           "sports_db",
                    "competition_name": e.get(
                        "strLeague", ""
                    ),
                    "competition_code": "",
                    "home_team":        home,
                    "home_team_norm":   normalise(home),
                    "home_team_id":     e.get("idHomeTeam"),
                    "away_team":        away,
                    "away_team_norm":   normalise(away),
                    "away_team_id":     e.get("idAwayTeam"),
                    "kickoff_uk":       uk_time,
                    "kickoff_dt":       None,
                    "status":           "scheduled",
                })
            except Exception as ex:
                print(f"SportsDB parse error: {ex}")
        return out
