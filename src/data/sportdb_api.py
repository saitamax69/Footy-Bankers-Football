import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API integration.
    Flashscore: Live scores and fixtures
                from every league on earth.
    Transfermarkt: Player values and squad data.

    API: api.sportdb.dev
    Key: SPORTDB_API_KEY secret
    """

    BASE = "https://api.sportdb.dev/api"

    def __init__(self):
        self.api_key = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers = {"X-API-Key": self.api_key}
        self.tz      = pytz.timezone("Europe/London")
        self._last   = 0

    def _get(
        self,
        endpoint: str,
        params: dict = None,
        delay: float = 1.0,
    ) -> dict:
        """Rate limited GET request."""
        if not self.api_key:
            return {}

        gap = time.time() - self._last
        if gap < delay:
            time.sleep(delay - gap)

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
            elif r.status_code == 401:
                print("SportDB: Invalid API key")
                return {}
            elif r.status_code == 429:
                print("SportDB: Rate limited - 30s")
                time.sleep(30)
                return {}
            elif r.status_code == 404:
                return {}
            else:
                print(
                    f"SportDB {r.status_code}: "
                    f"{endpoint}"
                )
                return {}

        except requests.Timeout:
            print(f"SportDB timeout: {endpoint}")
            return {}
        except Exception as e:
            print(f"SportDB error: {e}")
            return {}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FLASHSCORE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_todays_matches(self) -> list:
        """All football matches today."""
        data = self._get("/flashscore/football")
        if not data:
            return []
        return self._parse_matches(data)

    def get_live_scores(self) -> list:
        """Currently live matches."""
        data = self._get(
            "/flashscore/football/live"
        )
        if not data:
            return []
        matches = self._parse_matches(data)
        live = []
        for m in matches:
            status = m.get("status", "").lower()
            if any(
                s in status for s in [
                    "live", "playing", "1h",
                    "2h", "ht", "in_progress",
                ]
            ):
                live.append(m)
        return live

    def get_match_details(
        self, match_id: str
    ) -> dict:
        """Detailed stats for one match."""
        return self._get(
            f"/flashscore/football/match/{match_id}"
        ) or {}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TRANSFERMARKT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_player_value(
        self, player_name: str
    ) -> dict:
        """Market value for a player."""
        data = self._get(
            "/transfermarkt/player/search",
            params={"name": player_name},
        )
        if not data:
            return {}
        players = (
            data.get("players")
            or data.get("results")
            or data.get("data")
            or []
        )
        return players[0] if players else {}

    def get_squad_value(
        self, team_name: str
    ) -> dict:
        """
        Total squad market value.
        For injury impact context.
        'City missing £150M of squad'
        """
        data = self._get(
            "/transfermarkt/team/search",
            params={"name": team_name},
        )
        if not data:
            return {}

        teams = (
            data.get("teams")
            or data.get("results")
            or data.get("data")
            or []
        )
        if not teams:
            return {}

        team    = teams[0]
        team_id = team.get("id")

        if not team_id:
            return {}

        squad_data = self._get(
            f"/transfermarkt/team/{team_id}/squad"
        )
        if not squad_data:
            return {}

        squad = (
            squad_data.get("squad")
            or squad_data.get("players")
            or []
        )

        total = 0
        count = 0
        for p in squad:
            v = p.get("market_value", 0)
            if isinstance(v, (int, float)) and v > 0:
                total += v
                count += 1

        return {
            "team":          team_name,
            "squad_size":    count,
            "total_value_m": round(
                total / 1_000_000, 1
            ),
            "avg_value_m": round(
                total / 1_000_000 / count, 1
            ) if count else 0,
        }

    def get_transfer_news(self) -> list:
        """Latest transfer news for media posts."""
        data = self._get(
            "/transfermarkt/transfers/latest"
        )
        return (
            data.get("transfers", [])
            if data else []
        )

    def test_connection(self) -> bool:
        """Test API key and connection."""
        if not self.api_key:
            return False
        data = self._get(
            "/transfermarkt/countries"
        )
        if data:
            return True
        data2 = self._get("/flashscore/football")
        return bool(data2)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PARSER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _parse_matches(self, data) -> list:
        """Parse Flashscore data to standard format."""
        out = []

        if isinstance(data, list):
            matches = data
        else:
            matches = (
                data.get("matches")
                or data.get("events")
                or data.get("data")
                or []
            )

        for m in matches:
            try:
                home = (
                    m.get("home_team")
                    or m.get("homeTeam")
                    or (
                        m.get("home", {}).get("name")
                        if isinstance(m.get("home"), dict)
                        else m.get("home")
                    )
                    or ""
                )
                away = (
                    m.get("away_team")
                    or m.get("awayTeam")
                    or (
                        m.get("away", {}).get("name")
                        if isinstance(m.get("away"), dict)
                        else m.get("away")
                    )
                    or ""
                )

                if not home or not away:
                    continue

                kickoff_raw = (
                    m.get("start_time")
                    or m.get("startTime")
                    or m.get("time")
                    or m.get("date")
                    or ""
                )
                uk_time = self._parse_time(
                    kickoff_raw
                )

                competition = str(
                    m.get("tournament")
                    or m.get("competition")
                    or m.get("league")
                    or m.get("league_name")
                    or "Football"
                )

                status = str(
                    m.get("status")
                    or m.get("match_status")
                    or "scheduled"
                ).lower()

                home_score = (
                    m.get("home_score")
                    or (
                        m.get("score", {}).get("home")
                        if isinstance(
                            m.get("score"), dict
                        )
                        else None
                    )
                )
                away_score = (
                    m.get("away_score")
                    or (
                        m.get("score", {}).get("away")
                        if isinstance(
                            m.get("score"), dict
                        )
                        else None
                    )
                )

                out.append({
                    "id": (
                        m.get("id")
                        or m.get("match_id")
                        or f"sdb_{home}_{away}"
                    ),
                    "source":           "sportdb_api",
                    "competition_name": competition,
                    "competition_code": "",
                    "home_team":        home,
                    "home_team_norm":   normalise(home),
                    "home_team_id":     m.get("home_id"),
                    "away_team":        away,
                    "away_team_norm":   normalise(away),
                    "away_team_id":     m.get("away_id"),
                    "kickoff_uk":       uk_time,
                    "kickoff_dt":       None,
                    "status":           status,
                    "home_score":       home_score,
                    "away_score":       away_score,
                    "country":          m.get("country", ""),
                })

            except Exception as e:
                print(f"SportDB parse error: {e}")
                continue

        return out

    def _parse_time(self, raw) -> str:
        """Convert raw time to HH:MM UK format."""
        if not raw:
            return "TBC"
        try:
            if "T" in str(raw):
                dt = datetime.fromisoformat(
                    str(raw).replace("Z", "+00:00")
                )
                return dt.astimezone(
                    self.tz
                ).strftime("%H:%M")
            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(
                    raw, tz=pytz.utc
                )
                return dt.astimezone(
                    self.tz
                ).strftime("%H:%M")
            if ":" in str(raw) and len(str(raw)) <= 5:
                return str(raw)
        except Exception:
            pass
        return "TBC"
