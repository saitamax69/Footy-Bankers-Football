import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API - Flashscore + Transfermarkt
    
    Flashscore structure:
    /flashscore/football
    → Returns list of countries
    
    /flashscore/football/{country}:{id}
    → Returns competitions in that country
    
    /flashscore/football/{competition}:{id}/matches
    → Returns actual matches
    
    We cache country/competition IDs
    and only fetch matches we need.
    """

    BASE_URL = "https://api.sportdb.dev/api"

    # Top competitions to always check
    # Format: "slug:id" from the API
    TOP_COMPETITIONS = [
        # These will be populated after
        # first run discovers them
        # We start with known major ones
        # and add more as API reveals them
    ]

    def __init__(self):
        self.api_key = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers = {
            "X-API-Key": self.api_key,
        }
        self.tz = pytz.timezone("Europe/London")
        self._last_call = 0
        self._countries_cache = []
        self._competitions_cache = {}

    def _get(
        self,
        endpoint: str,
        params: dict = None,
        delay: float = 0.5,
    ) -> any:
        """Rate limited GET. Returns parsed JSON."""
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
                print("SportDB: Invalid API key")
                return None
            elif r.status_code == 429:
                print("SportDB: Rate limited - waiting")
                time.sleep(10)
                return None
            elif r.status_code == 404:
                return None
            else:
                return None

        except Exception as e:
            print(f"SportDB request error: {e}")
            return None

    def get_countries(self) -> list:
        """
        Get list of all countries.
        Returns: [{"name": "Albania", "id": 17, ...}]
        """
        if self._countries_cache:
            return self._countries_cache

        data = self._get("/flashscore/football")

        if not data:
            return []

        if isinstance(data, list):
            self._countries_cache = data
        elif isinstance(data, dict):
            self._countries_cache = (
                data.get("countries")
                or data.get("data")
                or []
            )

        return self._countries_cache

    def get_competitions_for_country(
        self, country_slug: str, country_id: int
    ) -> list:
        """
        Get competitions for a specific country.
        """
        cache_key = f"{country_slug}:{country_id}"

        if cache_key in self._competitions_cache:
            return self._competitions_cache[cache_key]

        data = self._get(
            f"/flashscore/football"
            f"/{country_slug}:{country_id}"
        )

        if not data:
            return []

        if isinstance(data, list):
            comps = data
        elif isinstance(data, dict):
            comps = (
                data.get("competitions")
                or data.get("data")
                or []
            )
        else:
            comps = []

        self._competitions_cache[cache_key] = comps
        return comps

    def get_matches_for_competition(
        self,
        competition_slug: str,
        competition_id: int,
    ) -> list:
        """
        Get todays matches for a specific competition.
        """
        data = self._get(
            f"/flashscore/football"
            f"/{competition_slug}:{competition_id}"
            f"/matches"
        )

        if not data:
            return []

        if isinstance(data, list):
            matches = data
        elif isinstance(data, dict):
            matches = (
                data.get("matches")
                or data.get("events")
                or data.get("data")
                or []
            )
        else:
            matches = []

        return self._parse_matches(
            matches,
            competition_slug
        )

    def get_todays_matches(
        self,
        max_countries: int = 20,
    ) -> list:
        """
        Get todays matches from Flashscore.
        
        Strategy:
        1. Get country list
        2. For top countries get competitions
        3. For each competition get matches
        4. Return all matches found
        
        max_countries limits API calls.
        Priority countries checked first.
        """
        if not self.api_key:
            return []

        print(
            "   SportDB: Fetching matches..."
        )

        # Priority country names to check first
        priority_countries = [
            "england", "spain", "germany",
            "italy", "france", "netherlands",
            "portugal", "scotland", "turkey",
            "belgium", "brazil", "argentina",
            "usa", "greece", "russia",
            "ukraine", "czech-republic",
            "croatia", "austria", "switzerland",
        ]

        countries = self.get_countries()
        if not countries:
            print("   SportDB: No countries found")
            return []

        print(
            f"   SportDB: {len(countries)} countries"
        )

        # Sort: priority countries first
        def priority_sort(country):
            slug = country.get("slug", "").lower()
            name = country.get("name", "").lower()
            for i, p in enumerate(priority_countries):
                if p in slug or p in name:
                    return i
            return 999

        sorted_countries = sorted(
            countries, key=priority_sort
        )

        all_matches = []
        countries_checked = 0

        for country in sorted_countries:
            if countries_checked >= max_countries:
                break

            slug = country.get("slug", "")
            cid  = country.get("id")

            if not slug or not cid:
                continue

            # Get competitions for this country
            competitions = \
                self.get_competitions_for_country(
                    slug, cid
                )

            for comp in competitions[:3]:
                # Max 3 competitions per country
                comp_slug = comp.get("slug", "")
                comp_id   = comp.get("id")

                if not comp_slug or not comp_id:
                    continue

                matches = \
                    self.get_matches_for_competition(
                        comp_slug, comp_id
                    )

                for m in matches:
                    m["country"] = country.get("name")
                    all_matches.append(m)

                time.sleep(0.3)

            countries_checked += 1

        print(
            f"   SportDB: Found "
            f"{len(all_matches)} matches"
        )
        return all_matches

    def _parse_matches(
        self, matches: list, comp_name: str = ""
    ) -> list:
        """Parse match data to standard format."""
        out = []

        for m in matches:
            try:
                # Try every possible field name
                home = self._extract_team(m, "home")
                away = self._extract_team(m, "away")

                if not home or not away:
                    continue

                competition = (
                    m.get("tournament")
                    or m.get("competition")
                    or m.get("league")
                    or m.get("name")
                    or m.get("competition_name")
                    or comp_name
                    or "Football"
                )

                kickoff = self._extract_time(m)
                status  = self._extract_status(m)

                out.append({
                    "id": (
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
                    "kickoff_uk":       kickoff,
                    "kickoff_dt":       None,
                    "status":           status,
                    "country":          m.get("country", ""),
                })

            except Exception as e:
                continue

        return out

    def _extract_team(
        self, m: dict, side: str
    ) -> str:
        """Extract team name trying all field names."""
        direct_keys = [
            f"{side}_team",
            f"{side}Team",
            f"{side}_name",
            f"{side}_team_name",
            f"{side}TeamName",
        ]

        for key in direct_keys:
            val = m.get(key)
            if val and isinstance(val, str):
                return val

        # Try nested dict
        nested = m.get(side)
        if isinstance(nested, dict):
            return (
                nested.get("name")
                or nested.get("team_name")
                or nested.get("title")
                or ""
            )

        # Try teams dict
        teams = m.get("teams", {})
        if isinstance(teams, dict):
            team = teams.get(side, {})
            if isinstance(team, dict):
                return team.get("name", "")

        return ""

    def _extract_time(self, m: dict) -> str:
        """Extract kickoff time as HH:MM UK."""
        raw = (
            m.get("start_time")
            or m.get("startTime")
            or m.get("time")
            or m.get("date")
            or m.get("kickoff")
            or m.get("match_time")
        )

        if not raw:
            return "TBC"

        try:
            if "T" in str(raw):
                dt = datetime.fromisoformat(
                    str(raw).replace("Z", "+00:00")
                )
                uk = dt.astimezone(self.tz)
                return uk.strftime("%H:%M")

            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(
                    raw, tz=pytz.utc
                )
                uk = dt.astimezone(self.tz)
                return uk.strftime("%H:%M")

            if (
                isinstance(raw, str)
                and ":" in raw
                and len(raw) <= 5
            ):
                return raw

        except Exception:
            pass

        return "TBC"

    def _extract_status(self, m: dict) -> str:
        """Extract match status."""
        raw = (
            m.get("status")
            or m.get("match_status")
            or m.get("state")
            or "scheduled"
        )
        return str(raw).lower()

    def test_connection(self) -> bool:
        """Test API is working."""
        if not self.api_key:
            return False
        data = self._get("/transfermarkt/countries")
        return bool(data)
