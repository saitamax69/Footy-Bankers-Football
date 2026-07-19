import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API - Flashscore + Transfermarkt

    Flashscore API structure:
    GET /flashscore/football
    Returns: list of countries
    [{"name":"England","id":1,"slug":"england",
      "competitions":"/api/flashscore/football/england:1"}]

    GET /flashscore/football/{slug}:{id}
    Returns: list of competitions in that country

    GET /flashscore/football/{comp_slug}:{comp_id}/matches
    Returns: list of todays matches
    """

    BASE_URL = "https://api.sportdb.dev/api"

    # Countries to always check first
    # These cover all major tournaments
    PRIORITY_SLUGS = [
        "world",
        "international",
        "europe",
        "england",
        "spain",
        "germany",
        "italy",
        "france",
        "netherlands",
        "portugal",
        "scotland",
        "turkey",
        "belgium",
        "brazil",
        "argentina",
        "usa",
        "mexico",
        "greece",
        "russia",
        "ukraine",
        "sweden",
        "norway",
        "denmark",
        "switzerland",
        "austria",
        "czech-republic",
        "poland",
        "romania",
        "serbia",
        "croatia",
        "south-africa",
        "morocco",
        "nigeria",
        "ghana",
        "egypt",
        "china",
        "japan",
        "south-korea",
        "australia",
    ]

    def __init__(self):
        self.api_key = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers     = {"X-API-Key": self.api_key}
        self.tz          = pytz.timezone("Europe/London")
        self._last_call  = 0
        self._country_cache = []
        self._comp_cache    = {}

    def _get(
        self,
        endpoint: str,
        delay: float = 0.4,
    ):
        """Rate limited GET request."""
        gap = time.time() - self._last_call
        if gap < delay:
            time.sleep(delay - gap)

        try:
            r = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self.headers,
                timeout=15,
            )
            self._last_call = time.time()

            if r.status_code == 200:
                return r.json()
            elif r.status_code == 401:
                print("SportDB: Invalid API key")
                return None
            elif r.status_code == 429:
                print("SportDB: Rate limited")
                time.sleep(10)
                return None
            else:
                return None

        except Exception as e:
            print(f"SportDB error: {e}")
            return None

    def _get_countries(self) -> list:
        """Get all countries with caching."""
        if self._country_cache:
            return self._country_cache

        data = self._get("/flashscore/football")
        if not data:
            return []

        if isinstance(data, list):
            self._country_cache = data
        elif isinstance(data, dict):
            self._country_cache = (
                data.get("countries")
                or data.get("data")
                or []
            )

        return self._country_cache

    def _get_competitions(
        self, slug: str, cid: int
    ) -> list:
        """Get competitions for a country."""
        cache_key = f"{slug}:{cid}"
        if cache_key in self._comp_cache:
            return self._comp_cache[cache_key]

        data = self._get(
            f"/flashscore/football/{slug}:{cid}"
        )

        if not data:
            return []

        if isinstance(data, list):
            comps = data
        elif isinstance(data, dict):
            comps = (
                data.get("competitions")
                or data.get("data")
                or data.get("results")
                or []
            )
        else:
            comps = []

        self._comp_cache[cache_key] = comps
        return comps

    def _get_matches(
        self, comp_slug: str, comp_id: int
    ) -> list:
        """Get todays matches for a competition."""
        data = self._get(
            f"/flashscore/football"
            f"/{comp_slug}:{comp_id}/matches"
        )

        if not data:
            return []

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return (
                data.get("matches")
                or data.get("events")
                or data.get("data")
                or data.get("fixtures")
                or []
            )
        return []

    def get_todays_matches(
        self, max_countries: int = 30
    ) -> list:
        """
        Get all todays matches from Flashscore.
        Checks priority countries first.
        """
        if not self.api_key:
            print("   SportDB: No API key")
            return []

        countries = self._get_countries()
        if not countries:
            print("   SportDB: No countries found")
            return []

        print(
            f"   SportDB: {len(countries)} "
            f"countries available"
        )

        # Sort priority countries first
        def sort_priority(country):
            slug = country.get("slug", "").lower()
            name = country.get("name", "").lower()
            for i, p in enumerate(self.PRIORITY_SLUGS):
                if p in slug or p in name:
                    return i
            return 999

        sorted_countries = sorted(
            countries, key=sort_priority
        )

        all_matches = []
        checked     = 0

        for country in sorted_countries:
            if checked >= max_countries:
                break

            slug  = country.get("slug", "")
            cid   = country.get("id")
            cname = country.get("name", "")

            if not slug or not cid:
                continue

            competitions = self._get_competitions(
                slug, cid
            )

            if not competitions:
                checked += 1
                continue

            for comp in competitions[:4]:
                comp_slug = comp.get("slug", "")
                comp_id   = comp.get("id")
                comp_name = (
                    comp.get("name")
                    or comp.get("title")
                    or cname
                )

                if not comp_slug or not comp_id:
                    continue

                raw_matches = self._get_matches(
                    comp_slug, comp_id
                )

                parsed = self._parse_matches(
                    raw_matches, comp_name, cname
                )

                all_matches.extend(parsed)

                if parsed:
                    print(
                        f"   SportDB: {cname} - "
                        f"{comp_name}: "
                        f"{len(parsed)} matches"
                    )

            checked += 1

        print(
            f"   SportDB total: "
            f"{len(all_matches)} matches"
        )
        return all_matches

    def _parse_matches(
        self,
        raw: list,
        comp_name: str,
        country_name: str,
    ) -> list:
        """Convert raw match data to standard format."""
        out = []

        for m in raw:
            try:
                if not isinstance(m, dict):
                    continue

                home = self._get_team(m, "home")
                away = self._get_team(m, "away")

                if not home or not away:
                    continue
                if home.lower() == away.lower():
                    continue

                competition = (
                    m.get("competition")
                    or m.get("tournament")
                    or m.get("league")
                    or m.get("name")
                    or comp_name
                )

                kickoff = self._get_kickoff(m)
                status  = str(
                    m.get("status", "scheduled")
                ).lower()

                out.append({
                    "id": (
                        m.get("id")
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
                    "country":          country_name,
                })

            except Exception:
                continue

        return out

    def _get_team(self, m: dict, side: str) -> str:
        """Extract team name trying all possible keys."""
        # Direct string keys
        for key in [
            f"{side}_team",
            f"{side}Team",
            f"{side}_name",
            f"{side}_team_name",
            f"{side}Name",
        ]:
            val = m.get(key)
            if val and isinstance(val, str):
                return val.strip()

        # Nested dict
        nested = m.get(side)
        if isinstance(nested, dict):
            name = (
                nested.get("name")
                or nested.get("team_name")
                or nested.get("title")
                or nested.get("shortName")
            )
            if name:
                return str(name).strip()

        # teams object
        teams = m.get("teams", {})
        if isinstance(teams, dict):
            team = teams.get(side, {})
            if isinstance(team, dict):
                name = team.get("name", "")
                if name:
                    return str(name).strip()

        return ""

    def _get_kickoff(self, m: dict) -> str:
        """Get kickoff time as HH:MM UK."""
        raw = (
            m.get("start_time")
            or m.get("startTime")
            or m.get("time")
            or m.get("date")
            or m.get("kickoff")
            or m.get("timestamp")
            or m.get("match_time")
        )

        if not raw:
            return "TBC"

        try:
            if isinstance(raw, str) and "T" in raw:
                dt = datetime.fromisoformat(
                    raw.replace("Z", "+00:00")
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

    def test_connection(self) -> bool:
        """Test API connection."""
        if not self.api_key:
            return False
        data = self._get("/transfermarkt/countries")
        return bool(data)
