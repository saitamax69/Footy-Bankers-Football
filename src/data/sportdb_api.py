import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API - Flashscore integration.

    CONFIRMED WORKING:
    - /flashscore/football/live (115+ matches)
    - /flashscore/football/{slug}:{id} (competitions)
    - {competition_link} (comp details with live/seasons)
    - {competition_link}/live (live matches for comp)
    - {competition_link}/{season}/fixtures (upcoming)

    CONFIRMED FIELD NAMES:
    homeFirstName / awayFirstName = team names
    tournamentName = competition name
    startDateTimeUtc = kickoff (ISO format)
    eventStage = status
    eventId = match ID

    VERIFIED COMPETITION LINKS:
    World Cup: world:8/world-championship:lvUBR5F8
    Premier League: england:198/premier-league:dYlOSQOD
    Championship: england:198/championship:2DSCa5fE
    Liga Portugal: portugal:155/liga-portugal:UmMRoGzp
    MLS: usa:200/mls:CQv5qrFt
    """

    BASE_URL = "https://api.sportdb.dev/api"

    # Verified competition links from debug output
    VERIFIED_COMPETITIONS = [
        # World level - HIGHEST PRIORITY
        (
            "world:8",
            "world-championship:lvUBR5F8",
            "World Championship (World Cup)",
            1,
        ),
        (
            "world:8",
            "olympic-games:SdMQZTB5",
            "Olympic Games Football",
            1,
        ),
        (
            "world:8",
            "fifa-club-world-cup:YoSkIXsp",
            "FIFA Club World Cup",
            1,
        ),
        (
            "world:8",
            "friendly-international:f1GbGBCd",
            "International Friendly",
            2,
        ),
        (
            "world:8",
            "world-cup-u20:86F6KN7r",
            "World Cup U20",
            2,
        ),
        # England - verified IDs
        (
            "england:198",
            "premier-league:dYlOSQOD",
            "Premier League",
            1,
        ),
        (
            "england:198",
            "championship:2DSCa5fE",
            "Championship",
            2,
        ),
        (
            "england:198",
            "fa-cup:lYQtaqPQ",
            "FA Cup",
            2,
        ),
        (
            "england:198",
            "efl-cup:OMT80ou8",
            "EFL Cup (Carabao Cup)",
            2,
        ),
        (
            "england:198",
            "league-one:rJSMG3H0",
            "League One",
            3,
        ),
        # Portugal - verified IDs
        (
            "portugal:155",
            "liga-portugal:UmMRoGzp",
            "Liga Portugal (Primeira Liga)",
            2,
        ),
        (
            "portugal:155",
            "liga-portugal-2:hSUajdSS",
            "Liga Portugal 2",
            3,
        ),
        # USA - verified IDs
        (
            "usa:200",
            "mls:CQv5qrFt",
            "MLS",
            2,
        ),
        (
            "usa:200",
            "usl-championship:OjCHtstG",
            "USL Championship",
            3,
        ),
    ]

    def __init__(self):
        self.api_key    = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers    = {"X-API-Key": self.api_key}
        self.tz         = pytz.timezone("Europe/London")
        self._last_call = 0
        self._country_cache = {}

    def _get(self, endpoint: str, delay: float = 0.3):
        """Rate limited GET. Handles /api prefix."""
        gap = time.time() - self._last_call
        if gap < delay:
            time.sleep(delay - gap)

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
                if data is None:
                    return None
                if isinstance(data, list) and not data:
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
            print(f"SportDB error: {e}")
            return None

    def get_todays_matches(
        self, max_countries: int = 20
    ) -> list:
        """
        Get all todays matches.

        Step 1: Global /live endpoint (all matches now)
        Step 2: Verified competitions live endpoint
        Step 3: Verified competitions fixtures
        Step 4: Discover more leagues from all countries
        """
        if not self.api_key:
            print("   SportDB: No API key set")
            return []

        all_matches = []
        seen        = set()

        def add(matches):
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

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 1: Global live matches
        # Best source - covers everything live now
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("   SportDB [1]: Global live matches...")
        live = self._get("/flashscore/football/live")
        if live and isinstance(live, list):
            parsed = self._parse_matches(live)
            n      = add(parsed)
            print(f"   SportDB /live: {n} matches")

        time.sleep(0.5)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2: Verified competition live
        # Gets matches for known competitions
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print(
            "   SportDB [2]: Competition live feeds..."
        )
        for country_path, comp_path, name, tier in \
                self.VERIFIED_COMPETITIONS:

            comp_url = (
                f"/flashscore/football"
                f"/{country_path}/{comp_path}"
            )
            comp_info = self._get(comp_url)

            if not comp_info or \
               not isinstance(comp_info, dict):
                continue

            # Live matches for this competition
            live_url = comp_info.get("live", "")
            if live_url:
                live_data = self._get(live_url)
                if live_data:
                    matches = (
                        live_data
                        if isinstance(live_data, list)
                        else self._extract_list(live_data)
                    )
                    if matches:
                        parsed = self._parse_matches(
                            matches, name
                        )
                        n = add(parsed)
                        if n > 0:
                            print(
                                f"   {name} live: +{n}"
                            )

            # Fixtures for today
            seasons = comp_info.get("seasons", [])
            if seasons and isinstance(seasons, list):
                latest  = seasons[0]
                fix_url = latest.get("fixtures", "")
                if fix_url:
                    fix_data = self._get(fix_url)
                    if fix_data:
                        matches = self._extract_list(
                            fix_data
                        )
                        todays = self._filter_today(
                            matches
                        )
                        if todays:
                            parsed = self._parse_matches(
                                todays, name
                            )
                            n = add(parsed)
                            if n > 0:
                                print(
                                    f"   {name} "
                                    f"fixtures: +{n}"
                                )

            time.sleep(0.3)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 3: Scan ALL 176 countries
        # Find the real IDs for Spain, Germany etc
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("   SportDB [3]: Scanning all countries...")
        countries = self._get("/flashscore/football")

        if countries and isinstance(countries, list):
            # Build slug to country map
            country_map = {
                c.get("slug", "").lower(): c
                for c in countries
            }

            # Countries to find - use slug not ID
            target_slugs = [
                "spain",
                "germany",
                "italy",
                "france",
                "brazil",
                "netherlands",
                "argentina",
                "turkey",
                "belgium",
                "scotland",
                "mexico",
                "greece",
                "ukraine",
                "russia",
                "switzerland",
                "austria",
                "czech-republic",
                "poland",
                "croatia",
                "serbia",
                "denmark",
                "sweden",
                "norway",
                "south-africa",
                "nigeria",
                "ghana",
                "egypt",
                "morocco",
                "china",
                "japan",
                "south-korea",
                "australia",
                "india",
                "saudi-arabia",
                "uae",
                "iran",
            ]

            checked = 0
            for slug in target_slugs:
                if checked >= max_countries:
                    break

                country = country_map.get(slug)
                if not country:
                    continue

                cid  = country.get("id")
                name = country.get("name", slug)

                if not cid:
                    continue

                # Get competitions for this country
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

                # Check top competitions
                for comp in comps[:3]:
                    link      = comp.get("link", "")
                    comp_name = comp.get("name", name)

                    if not link:
                        continue

                    endpoint  = link.replace("/api", "")
                    comp_info = self._get(endpoint)

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
                                )
                                else self._extract_list(
                                    live_data
                                )
                            )
                            parsed = self._parse_matches(
                                matches, comp_name
                            )
                            n = add(parsed)
                            if n > 0:
                                print(
                                    f"   {comp_name}: "
                                    f"+{n}"
                                )

                    # Fixtures
                    seasons = comp_info.get(
                        "seasons", []
                    )
                    if seasons:
                        fix_url = seasons[0].get(
                            "fixtures", ""
                        )
                        if fix_url:
                            fix_data = self._get(fix_url)
                            if fix_data:
                                matches = \
                                    self._extract_list(
                                        fix_data
                                    )
                                todays = \
                                    self._filter_today(
                                        matches
                                    )
                                parsed = \
                                    self._parse_matches(
                                        todays,
                                        comp_name
                                    )
                                n = add(parsed)
                                if n > 0:
                                    print(
                                        f"   {comp_name}"
                                        f" fix: +{n}"
                                    )

                    time.sleep(0.2)

                checked += 1

        print(
            f"   SportDB TOTAL: "
            f"{len(all_matches)} matches"
        )
        return all_matches

    def _extract_list(self, data) -> list:
        """Extract list from any response format."""
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
        """Keep only todays matches."""
        today  = datetime.now(self.tz).date()
        result = []

        for m in matches:
            d = self._match_date(m)
            if d is None or d == today:
                result.append(m)

        return result

    def _match_date(self, m: dict):
        """Extract date from match."""
        raw = (
            m.get("startDateTimeUtc")
            or m.get("startUtime")
            or m.get("startTime")
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
            if isinstance(raw, str) and raw.isdigit():
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
        Parse matches using CONFIRMED field names.

        Confirmed from debug:
        homeFirstName = home team
        awayFirstName = away team
        tournamentName = competition
        startDateTimeUtc = kickoff ISO
        eventStage = status
        eventId = ID
        """
        out = []

        for m in matches:
            if not isinstance(m, dict):
                continue
            try:
                # CONFIRMED field names
                home = (
                    m.get("homeFirstName")
                    or m.get("homeName")
                    or m.get("home_team")
                    or ""
                ).strip()

                away = (
                    m.get("awayFirstName")
                    or m.get("awayName")
                    or m.get("away_team")
                    or ""
                ).strip()

                if not home or not away:
                    continue
                if home.lower() == away.lower():
                    continue
                if len(home) < 2 or len(away) < 2:
                    continue

                competition = (
                    m.get("tournamentName")
                    or m.get("leagueName")
                    or m.get("competition")
                    or m.get("tournament")
                    or comp_name
                    or "Football"
                )

                kickoff  = self._kickoff(m)
                status   = str(
                    m.get("eventStage")
                    or m.get("status")
                    or "scheduled"
                ).lower()
                match_id = (
                    m.get("eventId")
                    or m.get("id")
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
                    ),
                    "away_team":        away,
                    "away_team_norm":   normalise(away),
                    "away_team_id": (
                        m.get("awayEventParticipantId")
                    ),
                    "kickoff_uk":       kickoff,
                    "kickoff_dt":       None,
                    "status":           status,
                    "match_links":      m.get("links", {}),
                })

            except Exception:
                continue

        return out

    def _kickoff(self, m: dict) -> str:
        """Get kickoff as HH:MM UK time."""
        raw = (
            m.get("startDateTimeUtc")
            or m.get("startUtime")
            or m.get("startTime")
            or m.get("kickoff")
            or m.get("date")
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
                    int(raw), tz=pytz.utc
                )
                uk = dt.astimezone(self.tz)
                return uk.strftime("%H:%M")

            if isinstance(raw, str) and raw.isdigit():
                dt = datetime.fromtimestamp(
                    int(raw), tz=pytz.utc
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
        """Test API works."""
        if not self.api_key:
            return False
        data = self._get("/flashscore/football/live")
        if data and isinstance(data, list):
            print(
                f"SportDB: {len(data)} live matches"
            )
            return True
        return False
