import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API - Flashscore integration.

    CONFIRMED WORKING ENDPOINTS:
    /flashscore/football/live
    → All currently live matches (115+ matches)
    → Field names: homeFirstName, awayFirstName
    → Competition: tournamentName
    → Time: startDateTimeUtc (ISO format)

    /flashscore/football/{country}:{id}
    → List of competitions

    {competition_link}
    → Returns: {live: url, seasons: [{fixtures: url}]}

    {competition_link}/live
    → Live matches for that competition

    {competition_link}/{season}/fixtures
    → Scheduled matches for that competition

    NOT WORKING:
    /flashscore/football/matches (empty)
    /flashscore/football/today (empty)
    /flashscore/football/{country}/{id}/matches (500)

    KNOWN COMPETITIONS:
    World Championship: world:8/world-championship:lvUBR5F8
    Premier League: england:198/premier-league:dYlOSQOD
    """

    BASE_URL = "https://api.sportdb.dev/api"

    # Key competitions to always check
    # Format: (country_slug:id, comp_slug:id, name)
    KEY_COMPETITIONS = [
        # World level
        (
            "world:8",
            "world-championship:lvUBR5F8",
            "World Championship (World Cup)",
        ),
        (
            "world:8",
            "olympic-games:SdMQZTB5",
            "Olympic Games Football",
        ),
        (
            "world:8",
            "fifa-club-world-cup:YoSkIXsp",
            "FIFA Club World Cup",
        ),
        (
            "world:8",
            "friendly-international:f1GbGBCd",
            "International Friendly",
        ),
        # England
        (
            "england:198",
            "premier-league:dYlOSQOD",
            "Premier League",
        ),
        (
            "england:198",
            "championship:2DSCa5fE",
            "Championship",
        ),
        # Spain
        (
            "spain:45",
            "laliga:KdeLeEoP",
            "La Liga",
        ),
        # Germany
        (
            "germany:78",
            "bundesliga:zZbySFaJ",
            "Bundesliga",
        ),
        # Italy
        (
            "italy:102",
            "serie-a:WXed4pIG",
            "Serie A",
        ),
        # France
        (
            "france:74",
            "ligue-1:lVoHFKcx",
            "Ligue 1",
        ),
    ]

    # Priority countries to scan for competitions
    PRIORITY_COUNTRIES = [
        ("world", 8),
        ("england", 198),
        ("spain", 45),
        ("germany", 78),
        ("italy", 102),
        ("france", 74),
        ("netherlands", 130),
        ("portugal", 155),
        ("brazil", 32),
        ("argentina", 11),
        ("usa", 200),
        ("turkey", 186),
        ("belgium", 24),
        ("scotland", 166),
        ("mexico", 119),
    ]

    def __init__(self):
        self.api_key    = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers    = {"X-API-Key": self.api_key}
        self.tz         = pytz.timezone("Europe/London")
        self._last_call = 0
        self._comp_cache = {}

    def _get(
        self,
        endpoint: str,
        delay: float = 0.3,
    ):
        """Rate limited GET. Handles /api prefix."""
        gap = time.time() - self._last_call
        if gap < delay:
            time.sleep(delay - gap)

        # Handle full paths that start with /api
        if endpoint.startswith("/api/"):
            url = f"{self.BASE_URL}{endpoint[4:]}"
        elif endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.BASE_URL}{endpoint}"

        try:
            r = requests.get(
                url,
                headers=self.headers,
                timeout=15,
            )
            self._last_call = time.time()

            if r.status_code == 200:
                data = r.json()
                # Skip empty responses
                if data is None:
                    return None
                if isinstance(data, list) and len(data) == 0:
                    return None
                if isinstance(data, dict) and not data:
                    return None
                return data
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
            print(f"SportDB error {endpoint[:50]}: {e}")
            return None

    def get_todays_matches(
        self, max_countries: int = 20
    ) -> list:
        """
        Get todays matches using confirmed endpoints.

        Strategy:
        1. Get all live matches (/live endpoint)
        2. Get fixtures for key competitions
        3. Scan priority countries for more
        """
        if not self.api_key:
            print("   SportDB: No API key")
            return []

        all_matches = []
        seen        = set()

        def add_matches(matches: list):
            added = 0
            for m in matches:
                hn = m.get("home_team_norm", "")
                an = m.get("away_team_norm", "")
                if not hn or not an:
                    continue
                key = (hn, an)
                if key not in seen:
                    seen.add(key)
                    all_matches.append(m)
                    added += 1
            return added

        # ── STEP 1: Global live matches ──
        # This is the most reliable endpoint
        print("   SportDB: Getting live matches...")
        live_data = self._get(
            "/flashscore/football/live"
        )
        if live_data and isinstance(live_data, list):
            parsed = self._parse_matches(live_data)
            added  = add_matches(parsed)
            print(
                f"   SportDB /live: {added} matches"
            )

        time.sleep(0.5)

        # ── STEP 2: Key competition fixtures ──
        print(
            "   SportDB: Getting competition fixtures..."
        )

        for country_path, comp_path, comp_name in \
                self.KEY_COMPETITIONS:

            # Get competition details
            comp_url = (
                f"/flashscore/football"
                f"/{country_path}/{comp_path}"
            )
            comp_info = self._get(comp_url)

            if not comp_info or \
               not isinstance(comp_info, dict):
                continue

            comp_added = 0

            # Try live matches for this competition
            live_url = comp_info.get("live", "")
            if live_url:
                live_data = self._get(live_url)
                if live_data:
                    matches = (
                        live_data
                        if isinstance(live_data, list)
                        else []
                    )
                    parsed = self._parse_matches(
                        matches, comp_name
                    )
                    comp_added += add_matches(parsed)

            # Try fixtures for current season
            seasons = comp_info.get("seasons", [])
            if seasons and isinstance(seasons, list):
                # Get most recent season
                latest = seasons[0]
                fixtures_url = latest.get(
                    "fixtures", ""
                )

                if fixtures_url:
                    fix_data = self._get(fixtures_url)
                    if fix_data:
                        matches = self._extract_matches(
                            fix_data
                        )
                        # Only get todays fixtures
                        todays = self._filter_today(
                            matches
                        )
                        parsed = self._parse_matches(
                            todays, comp_name
                        )
                        comp_added += add_matches(parsed)

            if comp_added > 0:
                print(
                    f"   {comp_name}: "
                    f"+{comp_added} matches"
                )

            time.sleep(0.3)

        # ── STEP 3: Scan priority countries ──
        print(
            "   SportDB: Scanning priority countries..."
        )

        countries_data = self._get(
            "/flashscore/football"
        )
        if not countries_data:
            countries_data = []

        country_map = {}
        if isinstance(countries_data, list):
            for c in countries_data:
                slug = c.get("slug", "").lower()
                country_map[slug] = c

        checked = 0
        for slug, fallback_id in self.PRIORITY_COUNTRIES:
            if checked >= max_countries:
                break

            country = country_map.get(slug)
            cid     = (
                country.get("id") if country
                else fallback_id
            )

            if not cid:
                checked += 1
                continue

            comps_data = self._get(
                f"/flashscore/football/{slug}:{cid}"
            )

            if not comps_data:
                checked += 1
                continue

            comps = (
                comps_data
                if isinstance(comps_data, list)
                else []
            )

            for comp in comps[:4]:
                link      = comp.get("link", "")
                comp_name = comp.get("name", slug)

                if not link:
                    continue

                # Get competition info
                comp_endpoint = link.replace(
                    "/api", ""
                )
                comp_info = self._get(comp_endpoint)

                if not comp_info or \
                   not isinstance(comp_info, dict):
                    continue

                # Live matches
                live_url = comp_info.get("live", "")
                if live_url:
                    live_data = self._get(live_url)
                    if live_data:
                        matches = (
                            live_data
                            if isinstance(
                                live_data, list
                            ) else []
                        )
                        parsed = self._parse_matches(
                            matches, comp_name
                        )
                        n = add_matches(parsed)
                        if n > 0:
                            print(
                                f"   {comp_name}: "
                                f"+{n}"
                            )

                # Todays fixtures
                seasons = comp_info.get("seasons", [])
                if seasons:
                    latest      = seasons[0]
                    fix_url     = latest.get(
                        "fixtures", ""
                    )
                    if fix_url:
                        fix_data = self._get(fix_url)
                        if fix_data:
                            matches = \
                                self._extract_matches(
                                    fix_data
                                )
                            todays = self._filter_today(
                                matches
                            )
                            if todays:
                                parsed = \
                                    self._parse_matches(
                                        todays,
                                        comp_name
                                    )
                                n = add_matches(parsed)
                                if n > 0:
                                    print(
                                        f"   {comp_name}"
                                        f" fixtures: +{n}"
                                    )

                time.sleep(0.3)

            checked += 1

        print(
            f"   SportDB TOTAL: "
            f"{len(all_matches)} matches"
        )
        return all_matches

    def _extract_matches(self, data) -> list:
        """Extract match list from any response."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for key in [
                "matches", "events", "fixtures",
                "data", "results", "items",
            ]:
                val = data.get(key)
                if isinstance(val, list) and val:
                    return val
        return []

    def _filter_today(self, matches: list) -> list:
        """Filter matches to only todays fixtures."""
        today = datetime.now(self.tz).date()
        result = []

        for m in matches:
            match_date = self._get_match_date(m)
            if match_date and match_date == today:
                result.append(m)
            elif not match_date:
                # If we cannot parse date include it
                result.append(m)

        return result

    def _get_match_date(self, m: dict):
        """Extract match date."""
        raw = (
            m.get("startDateTimeUtc")
            or m.get("startTime")
            or m.get("startUtime")
            or m.get("date")
        )

        if not raw:
            return None

        try:
            if isinstance(raw, str) and "T" in raw:
                dt = datetime.fromisoformat(
                    raw.replace("Z", "+00:00")
                )
                return dt.astimezone(self.tz).date()

            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(
                    int(raw), tz=pytz.utc
                )
                return dt.astimezone(self.tz).date()

        except Exception:
            pass

        return None

    def _parse_matches(
        self,
        matches: list,
        comp_name: str = "",
    ) -> list:
        """
        Parse matches using confirmed field names.

        From debug output:
        homeFirstName = home team name
        awayFirstName = away team name
        tournamentName = competition
        startDateTimeUtc = kickoff (ISO)
        eventStage = status
        eventId = match ID
        """
        out = []

        for m in matches:
            if not isinstance(m, dict):
                continue

            try:
                # Team names - confirmed field names
                home = (
                    m.get("homeFirstName")
                    or m.get("homeName")
                    or m.get("home_team")
                    or m.get("homeTeam")
                    or ""
                ).strip()

                away = (
                    m.get("awayFirstName")
                    or m.get("awayName")
                    or m.get("away_team")
                    or m.get("awayTeam")
                    or ""
                ).strip()

                if not home or not away:
                    continue
                if home.lower() == away.lower():
                    continue
                if len(home) < 2 or len(away) < 2:
                    continue

                # Competition name
                competition = (
                    m.get("tournamentName")
                    or m.get("tournament")
                    or m.get("leagueName")
                    or m.get("competitionName")
                    or m.get("league")
                    or comp_name
                    or "Football"
                )

                # Kickoff time
                kickoff = self._get_kickoff(m)

                # Status
                status = str(
                    m.get("eventStage")
                    or m.get("status")
                    or m.get("matchStatus")
                    or "scheduled"
                ).lower()

                # Match ID
                match_id = (
                    m.get("eventId")
                    or m.get("id")
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
                    "home_team_id": (
                        m.get("homeEventParticipantId")
                        or m.get("homeId")
                    ),
                    "away_team":        away,
                    "away_team_norm":   normalise(away),
                    "away_team_id": (
                        m.get("awayEventParticipantId")
                        or m.get("awayId")
                    ),
                    "kickoff_uk":       kickoff,
                    "kickoff_dt":       None,
                    "status":           status,
                    "match_links": m.get("links", {}),
                })

            except Exception:
                continue

        return out

    def _get_kickoff(self, m: dict) -> str:
        """Extract kickoff as HH:MM UK time."""
        raw = (
            m.get("startDateTimeUtc")
            or m.get("startTime")
            or m.get("startUtime")
            or m.get("kickoff")
            or m.get("time")
            or m.get("date")
        )

        if not raw:
            return "TBC"

        try:
            # ISO datetime string (confirmed format)
            if isinstance(raw, str) and "T" in raw:
                dt = datetime.fromisoformat(
                    raw.replace("Z", "+00:00")
                )
                uk = dt.astimezone(self.tz)
                return uk.strftime("%H:%M")

            # Unix timestamp
            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(
                    int(raw), tz=pytz.utc
                )
                uk = dt.astimezone(self.tz)
                return uk.strftime("%H:%M")

            # String timestamp
            if isinstance(raw, str) and raw.isdigit():
                dt = datetime.fromtimestamp(
                    int(raw), tz=pytz.utc
                )
                uk = dt.astimezone(self.tz)
                return uk.strftime("%H:%M")

            # Already HH:MM
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
        """Test API works."""
        if not self.api_key:
            return False
        data = self._get(
            "/flashscore/football/live"
        )
        if data and isinstance(data, list):
            print(
                f"SportDB connected: "
                f"{len(data)} live matches"
            )
            return True
        return False
