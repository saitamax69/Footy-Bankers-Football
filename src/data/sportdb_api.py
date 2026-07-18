import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API integration.
    Covers Flashscore and Transfermarkt data.
    
    Flashscore: Live scores, fixtures, results
                from virtually every league.
    
    Transfermarkt: Player values, squad data,
                   transfer news.
    
    API docs: api.sportdb.dev
    """

    BASE_URL = "https://api.sportdb.dev/api"

    def __init__(self):
        self.api_key = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers = {
            "X-API-Key": self.api_key,
        }
        self.tz = pytz.timezone("Europe/London")
        self._last_call = 0

    def _get(
        self,
        endpoint: str,
        params: dict = None,
        delay: float = 1.0,
    ) -> dict:
        """
        Rate limited GET request.
        Returns response JSON or empty dict.
        """
        # Enforce delay between calls
        gap = time.time() - self._last_call
        if gap < delay:
            time.sleep(delay - gap)

        try:
            r = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self.headers,
                params=params or {},
                timeout=15,
            )
            self._last_call = time.time()

            if r.status_code == 200:
                return r.json()
            elif r.status_code == 401:
                print(
                    "SportDB: Invalid API key"
                )
                return {}
            elif r.status_code == 429:
                print(
                    "SportDB: Rate limited - waiting 30s"
                )
                time.sleep(30)
                return {}
            elif r.status_code == 404:
                return {}
            else:
                print(
                    f"SportDB error {r.status_code}: "
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
    # FLASHSCORE ENDPOINTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_todays_matches(self) -> list:
        """
        Get all football matches today
        from Flashscore.
        Covers every league on earth.
        """
        data = self._get(
            "/flashscore/football"
        )

        if not data:
            return []

        return self._parse_flashscore_matches(data)

    def get_live_scores(self) -> list:
        """
        Get currently live football matches.
        Use during match hours for live updates.
        """
        data = self._get(
            "/flashscore/football/live"
        )

        if not data:
            return []

        return self._parse_live_matches(data)

    def get_match_details(
        self, match_id: str
    ) -> dict:
        """
        Get detailed stats for a specific match.
        """
        data = self._get(
            f"/flashscore/football/match/{match_id}"
        )
        return data or {}

    def get_league_fixtures(
        self, league_id: str
    ) -> list:
        """
        Get fixtures for a specific league.
        """
        data = self._get(
            f"/flashscore/football/league/{league_id}"
        )

        if not data:
            return []

        return self._parse_flashscore_matches(data)

    def get_team_recent_results(
        self, team_name: str, limit: int = 10
    ) -> list:
        """
        Search for team and get recent results.
        """
        data = self._get(
            "/flashscore/football/search",
            params={"q": team_name},
        )

        if not data:
            return []

        # Extract results from search
        results = []
        matches = data.get("matches", [])
        for m in matches[:limit]:
            if m.get("status") == "finished":
                results.append(m)

        return results

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TRANSFERMARKT ENDPOINTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_countries(self) -> list:
        """Get list of available countries."""
        data = self._get(
            "/transfermarkt/countries"
        )
        return data.get("countries", []) if data else []

    def get_player_value(
        self, player_name: str
    ) -> dict:
        """
        Get market value for a player.
        Useful for injury impact analysis.
        """
        data = self._get(
            "/transfermarkt/player/search",
            params={"name": player_name},
        )

        if not data:
            return {}

        players = data.get("players", [])
        if players:
            return players[0]
        return {}

    def get_team_squad(
        self, team_name: str
    ) -> dict:
        """
        Get squad information including
        player values and ages.
        """
        data = self._get(
            "/transfermarkt/team/search",
            params={"name": team_name},
        )

        if not data:
            return {}

        teams = data.get("teams", [])
        if not teams:
            return {}

        # Get first matching team
        team = teams[0]
        team_id = team.get("id")

        if not team_id:
            return team

        # Get full squad
        squad_data = self._get(
            f"/transfermarkt/team/{team_id}/squad"
        )

        if squad_data:
            team["squad"] = squad_data.get("squad", [])

        return team

    def get_transfer_news(self) -> list:
        """
        Get latest transfer news.
        Useful for media company content.
        """
        data = self._get(
            "/transfermarkt/transfers/latest"
        )
        return data.get("transfers", []) if data else []

    def get_squad_value(
        self, team_name: str
    ) -> dict:
        """
        Get total squad market value.
        Use in injury impact analysis:
        'City missing £150M worth of players'
        """
        squad_info = self.get_team_squad(team_name)

        if not squad_info:
            return {}

        squad = squad_info.get("squad", [])
        if not squad:
            return {}

        total_value = 0
        player_count = 0

        for player in squad:
            value = player.get("market_value", 0)
            if isinstance(value, (int, float)):
                total_value += value
                player_count += 1

        return {
            "team":          team_name,
            "squad_size":    player_count,
            "total_value_m": round(total_value / 1_000_000, 1),
            "avg_value_m":   round(
                total_value / 1_000_000 / player_count, 1
            ) if player_count else 0,
            "players":       squad,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PARSERS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _parse_flashscore_matches(
        self, data: dict
    ) -> list:
        """
        Parse Flashscore match data
        into our standard format.
        """
        out = []

        # Handle different response structures
        matches = (
            data.get("matches")
            or data.get("events")
            or data.get("data")
            or []
        )

        if not matches:
            # Sometimes data IS the list
            if isinstance(data, list):
                matches = data

        for m in matches:
            try:
                home = (
                    m.get("home_team")
                    or m.get("homeTeam")
                    or m.get("home", {}).get("name", "")
                    or ""
                )
                away = (
                    m.get("away_team")
                    or m.get("awayTeam")
                    or m.get("away", {}).get("name", "")
                    or ""
                )

                if not home or not away:
                    continue

                # Parse kickoff time
                kickoff_raw = (
                    m.get("start_time")
                    or m.get("startTime")
                    or m.get("time")
                    or m.get("date")
                    or ""
                )

                uk_time = self._parse_time(kickoff_raw)

                # Get competition
                competition = (
                    m.get("tournament")
                    or m.get("competition")
                    or m.get("league")
                    or m.get("league_name")
                    or "Football"
                )

                # Get status
                status = (
                    m.get("status")
                    or m.get("match_status")
                    or "scheduled"
                ).lower()

                # Get score if available
                home_score = (
                    m.get("home_score")
                    or m.get("score", {}).get("home")
                    or None
                )
                away_score = (
                    m.get("away_score")
                    or m.get("score", {}).get("away")
                    or None
                )

                parsed = {
                    "id":               (
                        m.get("id")
                        or m.get("match_id")
                        or f"sdb_{home}_{away}"
                    ),
                    "source":           "sportdb_api",
                    "competition_name": str(competition),
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
                    "round":            m.get("round", ""),
                }
                out.append(parsed)

            except Exception as e:
                print(
                    f"SportDB parse error: {e}"
                )
                continue

        return out

    def _parse_live_matches(
        self, data: dict
    ) -> list:
        """Parse live match data."""
        matches = self._parse_flashscore_matches(data)

        # Filter to only truly live matches
        live = []
        for m in matches:
            status = m.get("status", "").lower()
            if any(
                s in status
                for s in [
                    "live", "playing", "1h", "2h",
                    "ht", "in_progress", "ongoing"
                ]
            ):
                live.append(m)

        return live

    def _parse_time(self, raw: str) -> str:
        """Convert raw time string to HH:MM UK format."""
        if not raw:
            return "TBC"

        try:
            # Try ISO format
            if "T" in str(raw):
                dt = datetime.fromisoformat(
                    str(raw).replace("Z", "+00:00")
                )
                uk_dt = dt.astimezone(self.tz)
                return uk_dt.strftime("%H:%M")

            # Try Unix timestamp
            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(
                    raw, tz=pytz.utc
                )
                uk_dt = dt.astimezone(self.tz)
                return uk_dt.strftime("%H:%M")

            # Try HH:MM format directly
            if ":" in str(raw) and len(str(raw)) <= 5:
                return str(raw)

        except Exception:
            pass

        return "TBC"

    def test_connection(self) -> bool:
        """Test API connection and key validity."""
        if not self.api_key:
            print("SportDB: No API key set")
            return False

        # Try Transfermarkt countries
        # (simple endpoint to test auth)
        data = self._get(
            "/transfermarkt/countries"
        )

        if data:
            countries = data.get("countries", [])
            print(
                f"SportDB: Connected ✅ "
                f"({len(countries)} countries)"
            )
            return True

        # Try Flashscore
        data2 = self._get(
            "/flashscore/football"
        )
        if data2:
            print("SportDB: Connected via Flashscore ✅")
            return True

        print("SportDB: Connection failed ❌")
        return False
