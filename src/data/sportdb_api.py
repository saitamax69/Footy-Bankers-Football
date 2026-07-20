import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API - Flashscore integration.

    Correct endpoints discovered via debug:

    GET /flashscore/football/matches
    → All todays matches

    GET /flashscore/football/today
    → Todays matches (alternative)

    GET /flashscore/football/live
    → Currently live matches

    GET /flashscore/football/{country_slug}:{id}
    → Competitions in that country
    Returns: [{"id":"xxx","name":"...","slug":"...","link":"/api/..."}]

    GET {link_from_competition}
    → Matches for that competition
    Use the full "link" field from competition object

    Team name fields in match objects:
    homeFirstName, awayFirstName (primary)
    home3CharName, away3CharName (short names)
    """

    BASE_URL = "https://api.sportdb.dev/api"

    def __init__(self):
        self.api_key    = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers    = {"X-API-Key": self.api_key}
        self.tz         = pytz.timezone("Europe/London")
        self._last_call = 0

    def _get(
        self,
        endpoint: str,
        delay: float = 0.3,
        full_url: bool = False,
    ):
        """Rate limited GET request."""
        gap = time.time() - self._last_call
        if gap < delay:
            time.sleep(delay - gap)

        url = (
            endpoint if full_url
            else f"{self.BASE_URL}{endpoint}"
        )

        try:
            r = requests.get(
                url,
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
                print("SportDB: Rate limited - waiting")
                time.sleep(10)
                return None
            else:
                return None

        except Exception as e:
            print(f"SportDB request error: {e}")
            return None

    def get_todays_matches(
        self, max_countries: int = 30
    ) -> list:
        """
        Get all todays matches using correct endpoints.

        Strategy:
        1. Try /flashscore/football/matches (main)
        2. Try /flashscore/football/today (backup)
        3. Get World Cup via world:8 country
        4. Get top competition matches
        """
        if not self.api_key:
            print("   SportDB: No API key")
            return []

        all_matches = []
        seen        = set()

        # ── METHOD 1: Direct matches endpoint ──
        print("   SportDB: Trying /matches endpoint...")
        data = self._get("/flashscore/football/matches")
        if data:
            matches = self._extract_list(data)
            parsed  = self._parse_matches(matches)
            for m in parsed:
                key = (
                    m.get("home_team_norm", ""),
                    m.get("away_team_norm", ""),
                )
                if key[0] and key not in seen:
                    seen.add(key)
                    all_matches.append(m)
            print(
                f"   SportDB /matches: "
                f"{len(all_matches)} found"
            )

        time.sleep(0.5)

        # ── METHOD 2: Today endpoint ──
        if len(all_matches) < 10:
            print(
                "   SportDB: Trying /today endpoint..."
            )
            data = self._get(
                "/flashscore/football/today"
            )
            if data:
                matches = self._extract_list(data)
                parsed  = self._parse_matches(matches)
                added   = 0
                for m in parsed:
                    key = (
                        m.get("home_team_norm", ""),
                        m.get("away_team_norm", ""),
                    )
                    if key[0] and key not in seen:
                        seen.add(key)
                        all_matches.append(m)
                        added += 1
                print(
                    f"   SportDB /today: +{added}"
                )

        time.sleep(0.5)

        # ── METHOD 3: World Cup via world:8 ──
        print("   SportDB: Getting World competitions...")
        world_comps = self._get(
            "/flashscore/football/world:8"
        )
        if world_comps:
            comps = self._extract_list(world_comps)
            print(
                f"   World competitions: {len(comps)}"
            )
            for comp in comps[:5]:
                link = comp.get("link", "")
                name = comp.get("name", "World")
                if not link:
                    continue

                # Follow the competition link
                comp_data = self._get(link)
                if not comp_data:
                    continue

                comp_matches = self._extract_list(
                    comp_data
                )
                parsed = self._parse_matches(
                    comp_matches, name
                )
                added = 0
                for m in parsed:
                    key = (
                        m.get("home_team_norm", ""),
                        m.get("away_team_norm", ""),
                    )
                    if key[0] and key not in seen:
                        seen.add(key)
                        all_matches.append(m)
                        added += 1

                if added > 0:
                    print(
                        f"   {name}: +{added} matches"
                    )
                time.sleep(0.3)

        # ── METHOD 4: Top countries competitions ──
        print(
            "   SportDB: Getting top league matches..."
        )
        priority = [
            ("england", 198),
            ("spain",   None),
            ("germany", None),
            ("italy",   None),
            ("france",  None),
        ]

        # Get all countries to find IDs
        countries_data = self._get(
            "/flashscore/football"
        )
        if countries_data:
            countries = self._extract_list(
                countries_data
            )
            country_map = {
                c.get("slug", "").lower(): c
                for c in countries
            }

            for slug, fallback_id in priority:
                country = country_map.get(slug)
                if not country:
                    continue

                cid  = country.get("id", fallback_id)
                name = country.get("name", slug)

                if not cid:
                    continue

                comps_data = self._get(
                    f"/flashscore/football/{slug}:{cid}"
                )
                if not comps_data:
                    continue

                comps = self._extract_list(comps_data)

                for comp in comps[:3]:
                    link      = comp.get("link", "")
                    comp_name = comp.get("name", name)

                    if not link:
                        continue

                    comp_data = self._get(link)
                    if not comp_data:
                        continue

                    comp_matches = self._extract_list(
                        comp_data
                    )
                    parsed = self._parse_matches(
                        comp_matches, comp_name
                    )
                    added = 0
                    for m in parsed:
                        key = (
                            m.get("home_team_norm", ""),
                            m.get("away_team_norm", ""),
                        )
                        if key[0] and key not in seen:
                            seen.add(key)
                            all_matches.append(m)
                            added += 1

                    if added > 0:
                        print(
                            f"   {comp_name}: "
                            f"+{added}"
                        )
                    time.sleep(0.3)

        print(
            f"   SportDB TOTAL: "
            f"{len(all_matches)} matches"
        )
        return all_matches

    def get_live_matches(self) -> list:
        """Get currently live matches."""
        data = self._get("/flashscore/football/live")
        if not data:
            return []
        matches = self._extract_list(data)
        return self._parse_matches(matches)

    def _extract_list(self, data) -> list:
        """
        Extract list from any response format.
        API can return list directly or dict.
        """
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for key in [
                "matches", "events", "data",
                "fixtures", "results", "items",
                "competitions", "leagues",
            ]:
                val = data.get(key)
                if isinstance(val, list):
                    return val
        return []

    def _parse_matches(
        self,
        raw: list,
        comp_name: str = "",
    ) -> list:
        """
        Parse match objects to standard format.

        Known field names from debug:
        homeFirstName, awayFirstName (team names)
        home3CharName, away3CharName (short)
        awayEventParticipantId (team ID)
        """
        out = []

        for m in raw:
            if not isinstance(m, dict):
                continue

            try:
                home = self._get_team_name(m, "home")
                away = self._get_team_name(m, "away")

                if not home or not away:
                    continue
                if home.lower() == away.lower():
                    continue
                if len(home) < 2 or len(away) < 2:
                    continue

                competition = (
                    m.get("tournamentName")
                    or m.get("leagueName")
                    or m.get("competitionName")
                    or m.get("tournament")
                    or m.get("competition")
                    or m.get("league")
                    or m.get("name")
                    or comp_name
                    or "Football"
                )

                kickoff = self._get_kickoff(m)
                status  = self._get_status(m)

                match_id = (
                    m.get("id")
                    or m.get("eventId")
                    or m.get("matchId")
                    or f"sdb_{home}_{away}"
                )

                out.append({
                    "id":               str(match_id),
                    "source":           "sportdb_api",
                    "competition_name": str(competition),
                    "competition_code": "",
                    "home_team":        home,
                    "home_team_norm":   normalise(home),
                    "home_team_id":     (
                        m.get("homeEventParticipantId")
                        or m.get("homeId")
                    ),
                    "away_team":        away,
                    "away_team_norm":   normalise(away),
                    "away_team_id":     (
                        m.get("awayEventParticipantId")
                        or m.get("awayId")
                    ),
                    "kickoff_uk":       kickoff,
                    "kickoff_dt":       None,
                    "status":           status,
                    "country":          m.get(
                        "country", ""
                    ),
                })

            except Exception as e:
                continue

        return out

    def _get_team_name(
        self, m: dict, side: str
    ) -> str:
        """
        Extract team name from match object.
        Uses field names discovered in debug output.
        """
        # Primary fields from Flashscore
        primary_keys = [
            f"{side}FirstName",      # homeFirstName
            f"{side}Name",           # homeName
            f"{side}TeamName",       # homeTeamName
            f"{side}FullName",       # homeFullName
            f"{side}LongName",       # homeLongName
            f"{side}_team",          # home_team
            f"{side}Team",           # homeTeam
            f"{side}_name",          # home_name
        ]

        for key in primary_keys:
            val = m.get(key)
            if val and isinstance(val, str):
                val = val.strip()
                if len(val) >= 2:
                    return val

        # Try nested objects
        for nested_key in [side, f"{side}Team"]:
            obj = m.get(nested_key)
            if isinstance(obj, dict):
                for name_key in [
                    "name", "fullName",
                    "firstName", "longName",
                ]:
                    val = obj.get(name_key)
                    if val and isinstance(val, str):
                        val = val.strip()
                        if len(val) >= 2:
                            return val

        # Short name as last resort
        short = m.get(f"{side}3CharName", "")
        if short and len(short) >= 2:
            return short

        return ""

    def _get_kickoff(self, m: dict) -> str:
        """Extract kickoff time as HH:MM UK."""
        raw = (
            m.get("startTimestamp")
            or m.get("startTime")
            or m.get("kickoff")
            or m.get("time")
            or m.get("date")
            or m.get("timestamp")
            or m.get("matchTime")
        )

        if not raw:
            return "TBC"

        try:
            # Unix timestamp
            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(
                    raw, tz=pytz.utc
                )
                uk = dt.astimezone(self.tz)
                return uk.strftime("%H:%M")

            # ISO string
            if isinstance(raw, str):
                if "T" in raw:
                    dt = datetime.fromisoformat(
                        raw.replace("Z", "+00:00")
                    )
                    uk = dt.astimezone(self.tz)
                    return uk.strftime("%H:%M")

                # Already HH:MM
                if ":" in raw and len(raw) <= 5:
                    return raw

        except Exception:
            pass

        return "TBC"

    def _get_status(self, m: dict) -> str:
        """Extract match status."""
        raw = (
            m.get("status")
            or m.get("matchStatus")
            or m.get("state")
            or m.get("statusCode")
            or "scheduled"
        )
        return str(raw).lower()

    def test_connection(self) -> bool:
        """Quick connection test."""
        if not self.api_key:
            return False
        data = self._get(
            "/flashscore/football/matches"
        )
        return data is not None
