import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class FootballDataOrg:
    """
    Primary data source.
    football-data.org free tier.
    10 requests per minute limit.
    """

    BASE = "https://api.football-data.org/v4"

    def __init__(self):
        self.key     = os.environ.get(
            "FOOTBALL_DATA_API_KEY", ""
        )
        self.headers = {"X-Auth-Token": self.key}
        self.tz      = pytz.timezone("Europe/London")
        self._last   = 0

    def _get(self, endpoint: str, params: dict = None):
        gap = time.time() - self._last
        if gap < 6:
            time.sleep(6 - gap)
        try:
            r = requests.get(
                f"{self.BASE}{endpoint}",
                headers=self.headers,
                params=params or {},
                timeout=15,
            )
            self._last = time.time()
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                print("FD: Rate limited. Waiting 60s.")
                time.sleep(60)
                return None
            else:
                print(
                    f"FD error {r.status_code}: "
                    f"{endpoint}"
                )
                return None
        except Exception as e:
            print(f"FD request failed: {e}")
            return None

    def get_todays_matches(self) -> list:
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        data = self._get(
            "/matches",
            {"dateFrom": today, "dateTo": today},
        )
        if not data:
            return []
        return self._parse_matches(
            data.get("matches", [])
        )

    def get_team_form(self, team_id: int) -> dict:
        data = self._get(
            f"/teams/{team_id}/matches",
            {"status": "FINISHED", "limit": 10},
        )
        if not data:
            return {}
        return self._calc_form(
            data.get("matches", []), team_id
        )

    def get_h2h(self, match_id: int) -> dict:
        data = self._get(
            f"/matches/{match_id}/head2head",
            {"limit": 10},
        )
        if not data:
            return {}
        return self._parse_h2h(data)

    def get_result(self, match_id: int) -> dict:
        data = self._get(f"/matches/{match_id}")
        if not data:
            return {}
        m  = data.get("match", data)
        ft = m.get("score", {}).get("fullTime", {})
        return {
            "status":     m.get("status", ""),
            "home_goals": ft.get("home"),
            "away_goals": ft.get("away"),
        }

    def _parse_matches(self, raw: list) -> list:
        out = []
        for m in raw:
            try:
                utc = datetime.fromisoformat(
                    m["utcDate"].replace("Z", "+00:00")
                )
                uk = utc.astimezone(self.tz)
                out.append({
                    "id":               m["id"],
                    "source":           "football_data_org",
                    "competition_code": m["competition"]["code"],
                    "competition_name": m["competition"]["name"],
                    "home_team":        m["homeTeam"]["name"],
                    "home_team_norm":   normalise(
                        m["homeTeam"]["name"]
                    ),
                    "home_team_id":     m["homeTeam"]["id"],
                    "away_team":        m["awayTeam"]["name"],
                    "away_team_norm":   normalise(
                        m["awayTeam"]["name"]
                    ),
                    "away_team_id":     m["awayTeam"]["id"],
                    "kickoff_uk":       uk.strftime("%H:%M"),
                    "kickoff_dt":       uk,
                    "kickoff_utc":      m["utcDate"],
                    "status":           m.get("status", ""),
                    "matchday":         m.get("matchday"),
                })
            except Exception as e:
                print(f"FD match parse error: {e}")
        return out

    def _calc_form(
        self, matches: list, team_id: int
    ) -> dict:
        wins = draws = losses = 0
        gf = ga = 0
        form = []
        for m in matches[-10:]:
            ft = m.get("score", {}).get(
                "fullTime", {}
            )
            h = ft.get("home")
            a = ft.get("away")
            if h is None or a is None:
                continue
            is_home = m["homeTeam"]["id"] == team_id
            scored    = h if is_home else a
            conceded  = a if is_home else h
            gf += scored
            ga += conceded
            if scored > conceded:
                wins += 1
                form.append("W")
            elif scored == conceded:
                draws += 1
                form.append("D")
            else:
                losses += 1
                form.append("L")
        total = wins + draws + losses
        if total == 0:
            return {}
        return {
            "wins":              wins,
            "draws":             draws,
            "losses":            losses,
            "total":             total,
            "win_rate":          round(
                wins / total * 100, 1
            ),
            "goals_for_avg":     round(gf / total, 2),
            "goals_against_avg": round(ga / total, 2),
            "form_string":       "".join(reversed(form)),
            "ppg":               round(
                (wins * 3 + draws) / total, 2
            ),
        }

    def _parse_h2h(self, data: dict) -> dict:
        matches = data.get("matches", [])
        if not matches:
            return {}
        hw = aw = dr = goals = 0
        for m in matches:
            ft = m.get("score", {}).get(
                "fullTime", {}
            )
            h = ft.get("home")
            a = ft.get("away")
            if h is None or a is None:
                continue
            goals += h + a
            if h > a:
                hw += 1
            elif a > h:
                aw += 1
            else:
                dr += 1
        total = hw + aw + dr
        return {
            "home_wins": hw,
            "away_wins": aw,
            "draws":     dr,
            "total":     total,
            "avg_goals": round(
                goals / total, 2
            ) if total else 0,
        }
