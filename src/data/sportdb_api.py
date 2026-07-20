import os
import time
import requests
from datetime import datetime
import pytz

from src.data.team_names import normalise


class SportDBApi:
    """
    SportDB API - Flashscore integration.

    All competition IDs verified via debug script.
    Uses /live endpoint as primary source.
    Uses competition-specific endpoints as backup.
    """

    BASE_URL = "https://api.sportdb.dev/api"

    # ALL VERIFIED COMPETITION LINKS
    # Format: (country_path, comp_path, display_name, tier)
    # Tier 1 = World Cup/UCL level
    # Tier 2 = Top domestic leagues
    # Tier 3 = Secondary leagues
    VERIFIED_COMPETITIONS = [

        # ── WORLD LEVEL ──────────────────────────
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
        (
            "world:8",
            "world-cup-u17:INHpQ3aR",
            "World Cup U17",
            3,
        ),

        # ── ENGLAND ──────────────────────────────
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

        # ── SPAIN ────────────────────────────────
        (
            "spain:176",
            "laliga:QVmLl54o",
            "La Liga",
            1,
        ),
        (
            "spain:176",
            "laliga2:vZiPmPJi",
            "La Liga 2",
            2,
        ),

        # ── GERMANY ──────────────────────────────
        (
            "germany:81",
            "bundesliga:W6BOzpK2",
            "Bundesliga",
            1,
        ),
        (
            "germany:81",
            "2-bundesliga:tKH71vSe",
            "2. Bundesliga",
            2,
        ),

        # ── ITALY ────────────────────────────────
        (
            "italy:98",
            "serie-a:COuk57Ci",
            "Serie A",
            1,
        ),
        (
            "italy:98",
            "serie-b:6oug4RRc",
            "Serie B",
            2,
        ),

        # ── FRANCE ───────────────────────────────
        (
            "france:77",
            "ligue-1:KIShoMk3",
            "Ligue 1",
            1,
        ),
        (
            "france:77",
            "ligue-2:Y35Jer59",
            "Ligue 2",
            2,
        ),

        # ── NETHERLANDS ──────────────────────────
        (
            "netherlands:139",
            "eredivisie:Or1bBrWD",
            "Eredivisie",
            2,
        ),
        (
            "netherlands:139",
            "eerste-divisie:6Nl8nagD",
            "Eerste Divisie",
            3,
        ),

        # ── PORTUGAL ─────────────────────────────
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

        # ── SCOTLAND ─────────────────────────────
        (
            "scotland:199",
            "premiership:tGwiyvJ1",
            "Scottish Premiership",
            2,
        ),

        # ── TURKEY ───────────────────────────────
        (
            "turkey:191",
            "super-lig:Opdcd08Q",
            "Super Lig",
            2,
        ),

        # ── BELGIUM ──────────────────────────────
        (
            "belgium:32",
            "jupiler-pro-league:dG2SqPrf",
            "Jupiler Pro League",
            2,
        ),

        # ── BRAZIL ───────────────────────────────
        (
            "brazil:39",
            "serie-a-betano:Yq4hUnzQ",
            "Brasileirao Serie A",
            2,
        ),
        (
            "brazil:39",
            "serie-b:vRtLP6rs",
            "Brasileirao Serie B",
            3,
        ),

        # ── ARGENTINA ────────────────────────────
        (
            "argentina:22",
            "liga-profesional:naYhNOaA",
            "Liga Profesional Argentina",
            2,
        ),

        # ── USA ──────────────────────────────────
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

        # ── MEXICO ───────────────────────────────
        (
            "mexico:128",
            "liga-mx:bm2Vlsfl",
            "Liga MX",
            2,
        ),

        # ── DENMARK ──────────────────────────────
        (
            "denmark:63",
            "superliga:O6W7GIaF",
            "Danish Superliga",
            2,
        ),

        # ── SWEDEN ───────────────────────────────
        (
            "sweden:181",
            "allsvenskan:nXxWpLmT",
            "Allsvenskan",
            2,
        ),

        # ── NORWAY ───────────────────────────────
        (
            "norway:145",
            "eliteserien:GOvB22xg",
            "Eliteserien",
            2,
        ),

        # ── SWITZERLAND ──────────────────────────
        (
            "switzerland:182",
            "super-league:KAjTCI1l",
            "Swiss Super League",
            2,
        ),

        # ── GREECE ───────────────────────────────
        (
            "greece:83",
            "super-league:d2pwJFHI",
            "Super League Greece",
            2,
        ),

        # ── RUSSIA ───────────────────────────────
        (
            "russia:158",
            "premier-league:YacqHHdS",
            "Russian Premier League",
            2,
        ),

        # ── UKRAINE ──────────────────────────────
        (
            "ukraine:195",
            "premier-league:Myjs3vp6",
            "Ukrainian Premier League",
            2,
        ),

        # ── SAUDI ARABIA ─────────────────────────
        (
            "saudi-arabia:165",
            "saudi-professional-league:tUxUbLR2",
            "Saudi Pro League",
            2,
        ),

        # ── JAPAN ────────────────────────────────
        (
            "japan:100",
            "j1-league:pAq4eRQ9",
            "J1 League",
            2,
        ),

        # ── SOUTH KOREA ──────────────────────────
        (
            "south-korea:106",
            "k-league-1:0IDCJLlH",
            "K League 1",
            2,
        ),

        # ── CHINA ────────────────────────────────
        (
            "china:52",
            "super-league:nc9yRmcn",
            "Chinese Super League",
            2,
        ),

        # ── POLAND ───────────────────────────────
        (
            "poland:154",
            "ekstraklasa:lrMHUHDc",
            "Ekstraklasa",
            2,
        ),

        # ── CROATIA ──────────────────────────────
        (
            "croatia:59",
            "hnl:nqMxclRN",
            "HNL Croatia",
            2,
        ),

        # ── SERBIA ───────────────────────────────
        (
            "serbia:167",
            "mozzart-bet-super-liga:jVhkb1QE",
            "Serbian Super Liga",
            2,
        ),

        # ── ROMANIA ──────────────────────────────
        (
            "romania:157",
            "superliga:GILi6JC9",
            "Romanian Superliga",
            2,
        ),

        # ── CZECH REPUBLIC ───────────────────────
        (
            "czech-republic:62",
            "chance-liga:hleea1wH",
            "Czech Chance Liga",
            2,
        ),

        # ── SOUTH AFRICA ─────────────────────────
        (
            "south-africa:175",
            "betway-premiership:WYFXQ1KH",
            "South African Premiership",
            3,
        ),

        # ── NIGERIA ──────────────────────────────
        (
            "nigeria:143",
            "npfl:0YfyoJfj",
            "Nigerian Premier League",
            3,
        ),

        # ── EGYPT ────────────────────────────────
        (
            "egypt:69",
            "premier-league:xbpjAGxq",
            "Egyptian Premier League",
            3,
        ),

        # ── MOROCCO ──────────────────────────────
        (
            "morocco:134",
            "botola-pro:SWk4muv7",
            "Botola Pro Morocco",
            3,
        ),

        # ── INDIA ────────────────────────────────
        (
            "india:93",
            "isl:rmioSrer",
            "Indian Super League",
            3,
        ),
    ]

    def __init__(self):
        self.api_key    = os.environ.get(
            "SPORTDB_API_KEY", ""
        )
        self.headers    = {
            "X-API-Key": self.api_key
        }
        self.tz         = pytz.timezone(
            "Europe/London"
        )
        self._last_call = 0

    def _get(
        self, endpoint: str, delay: float = 0.3
    ):
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
        Step 1: Global /live endpoint
        Step 2: All verified competition /live
        Step 3: All verified competition fixtures
        """
        if not self.api_key:
            print("   SportDB: No API key")
            return []

        all_matches = []
        seen        = set()

        def add(matches: list) -> int:
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

        # ── STEP 1: Global /live ──────────────────
        print(
            "   SportDB [1]: Global live matches..."
        )
        live = self._get(
            "/flashscore/football/live"
        )
        if live and isinstance(live, list):
            parsed = self._parse_matches(live)
            n      = add(parsed)
            print(f"   /live: {n} matches")
        time.sleep(0.5)

        # ── STEP 2 + 3: Verified competitions ─────
        print(
            "   SportDB [2]: Verified competitions..."
        )

        # Sort: tier 1 first
        sorted_comps = sorted(
            self.VERIFIED_COMPETITIONS,
            key=lambda x: x[3]
        )

        for country_path, comp_path, name, tier in \
                sorted_comps:

            comp_url  = (
                f"/flashscore/football"
                f"/{country_path}/{comp_path}"
            )
            comp_info = self._get(comp_url)

            if not comp_info or \
               not isinstance(comp_info, dict):
                continue

            total_added = 0

            # Live matches for this competition
            live_url = comp_info.get("live", "")
            if live_url:
                live_data = self._get(live_url)
                if live_data:
                    matches = (
                        live_data
                        if isinstance(live_data, list)
                        else self._extract_list(
                            live_data
                        )
                    )
                    parsed = self._parse_matches(
                        matches, name
                    )
                    total_added += add(parsed)

            # Fixtures for current season
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
                        todays  = self._filter_today(
                            matches
                        )
                        if todays:
                            parsed = self._parse_matches(
                                todays, name
                            )
                            total_added += add(parsed)

            if total_added > 0:
                print(
                    f"   {name}: +{total_added}"
                )

            time.sleep(0.25)

        print(
            f"   SportDB TOTAL: "
            f"{len(all_matches)} matches"
        )
        return all_matches

    def _extract_list(self, data) -> list:
        """Extract list from any response."""
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
        Parse using CONFIRMED field names:
        homeFirstName / awayFirstName
        tournamentName
        startDateTimeUtc
        eventStage
        eventId
        """
        out = []

        for m in matches:
            if not isinstance(m, dict):
                continue
            try:
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
                    "id": str(match_id),
                    "source": "sportdb_api",
                    "competition_name": str(
                        competition
                    ),
                    "competition_code": "",
                    "home_team": home,
                    "home_team_norm": normalise(home),
                    "home_team_id": m.get(
                        "homeEventParticipantId"
                    ),
                    "away_team": away,
                    "away_team_norm": normalise(away),
                    "away_team_id": m.get(
                        "awayEventParticipantId"
                    ),
                    "kickoff_uk": kickoff,
                    "kickoff_dt": None,
                    "status": status,
                    "match_links": m.get("links", {}),
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
