import time
from datetime import datetime
import pytz

from src.data.football_data import FootballDataOrg
from src.data.sports_db import TheSportsDB
from src.data.sportdb_api import SportDBApi
from src.data.news import NewsCollector
from src.data.weather import WeatherChecker
from config import TOP_COMPETITIONS


class DataCollector:
    """
    Master data collector.

    Priority order:
    1. SportDB Flashscore FIRST (covers everything)
    2. football-data.org (top European leagues)
    3. TheSportsDB (free backup)

    Matches sorted by importance before analysis.
    World Cup > UCL > Top leagues > Rest
    """

    def __init__(self):
        self.sportdb = SportDBApi()
        self.fd      = FootballDataOrg()
        self.sdb     = TheSportsDB()
        self.news    = NewsCollector()
        self.wx      = WeatherChecker()
        self.tz      = pytz.timezone("Europe/London")

    def get_todays_matches(self) -> list:
        """
        Collect from all sources.
        Deduplicate by team names.
        Sort by competition importance.
        Enrich top 25 with stats and news.
        """
        print("\n📡 Collecting matches...")
        seen        = set()
        all_matches = []

        # ── SOURCE 1: SportDB Flashscore ──────────
        print("\n   [1/3] SportDB Flashscore...")
        try:
            if self.sportdb.api_key:
                flash = self.sportdb.get_todays_matches(
                    max_countries=20
                )
                added = 0
                for m in flash:
                    hn = m.get("home_team_norm", "")
                    an = m.get("away_team_norm", "")
                    if not hn or not an:
                        continue
                    key = (hn, an)
                    if key not in seen:
                        seen.add(key)
                        all_matches.append(m)
                        added += 1
                print(
                    f"   ✅ Flashscore: {added} matches"
                )
            else:
                print("   ⚠️  No SPORTDB_API_KEY")
        except Exception as e:
            print(f"   ❌ Flashscore: {e}")

        # ── SOURCE 2: football-data.org ───────────
        print("\n   [2/3] football-data.org...")
        try:
            fd_matches = self.fd.get_todays_matches()
            added = 0
            for m in fd_matches:
                hn = m.get("home_team_norm", "")
                an = m.get("away_team_norm", "")
                if not hn or not an:
                    continue
                key = (hn, an)
                if key not in seen:
                    seen.add(key)
                    all_matches.append(m)
                    added += 1
            print(
                f"   ✅ football-data.org: +{added}"
            )
        except Exception as e:
            print(f"   ❌ football-data.org: {e}")

        # ── SOURCE 3: TheSportsDB ─────────────────
        print("\n   [3/3] TheSportsDB...")
        try:
            sdb_m = self.sdb.get_todays_matches()
            added = 0
            for m in sdb_m:
                if not m.get("home_team"):
                    continue
                hn = m.get("home_team_norm", "")
                an = m.get("away_team_norm", "")
                if not hn or not an:
                    continue
                key = (hn, an)
                if key not in seen:
                    seen.add(key)
                    all_matches.append(m)
                    added += 1
            print(f"   ✅ TheSportsDB: +{added}")
        except Exception as e:
            print(f"   ❌ TheSportsDB: {e}")

        total = len(all_matches)
        print(f"\n   📊 Total: {total} unique matches")

        if not all_matches:
            print("   ⚠️  No matches found today")
            return []

        # Sort by competition importance
        all_matches = self._sort_by_priority(
            all_matches
        )

        # Log top 5 after sorting
        print("\n   Top matches after sorting:")
        for m in all_matches[:5]:
            print(
                f"   → {m.get('home_team')} vs "
                f"{m.get('away_team')} "
                f"({m.get('competition_name', '')})"
            )

        return self._enrich(all_matches)

    def _sort_by_priority(
        self, matches: list
    ) -> list:
        """
        Sort matches by competition importance.

        Priority levels:
        0 = World Cup / World Championship
        1 = Olympics / FIFA Club World Cup
        2 = UEFA Champions League / Europa
        3 = Continental (Copa America, AFCON)
        4 = Top 5 European leagues
        5 = Other major leagues (MLS, Brasileirao)
        6 = Secondary leagues
        7 = Everything else
        """

        def priority(m):
            comp    = m.get(
                "competition_name", ""
            ).lower()
            country = m.get("country", "").lower()

            # Level 0: World Cup
            if any(t in comp for t in [
                "world championship",
                "fifa world cup",
                "world cup 2026",
                "world cup final",
            ]):
                return 0

            # Level 1: Olympics and major FIFA events
            if any(t in comp for t in [
                "olympic games",
                "fifa club world cup",
                "fifa intercontinental",
            ]):
                return 1

            # Level 2: UEFA club competitions
            if any(t in comp for t in [
                "champions league",
                "europa league",
                "conference league",
            ]):
                return 2

            # Level 3: Continental national team comps
            if any(t in comp for t in [
                "copa america",
                "africa cup of nations",
                "afcon",
                "european championship",
                "copa libertadores",
                "finalissima",
            ]):
                return 3

            # Level 4: England Premier League
            # Must check country to avoid
            # Lebanese/Egyptian "Premier League"
            if "premier league" in comp:
                if (
                    "england" in country
                    or "english" in comp
                    or m.get("competition_code") == "PL"
                ):
                    return 4
                # Any other "Premier League" = lower
                return 6

            # Level 4: Other major European leagues
            if any(t in comp for t in [
                "laliga",
                "la liga",
                "bundesliga",
                "serie a",
                "ligue 1",
            ]):
                # Verify it is the main one
                if "bundesliga" in comp:
                    if "germany" in country or \
                       "german" in comp:
                        return 4
                    return 6
                if "serie a" in comp:
                    if "italy" in country or \
                       "italian" in comp or \
                       "brazil" not in country:
                        return 4
                    return 6
                if "ligue 1" in comp:
                    if "france" in country or \
                       "french" in comp:
                        return 4
                    return 6
                return 4

            # Level 5: Other notable leagues
            if any(t in comp for t in [
                "eredivisie",
                "primeira liga",
                "liga portugal",
                "scottish premiership",
                "super lig",
                "jupiler pro",
                "brasileirao",
                "liga profesional",
                "liga mx",
                "mls",
                "danish superliga",
                "allsvenskan",
                "eliteserien",
                "ekstraklasa",
                "super league",
                "j1 league",
                "k league",
                "saudi professional",
                "chinese super",
                "hnl",
            ]):
                return 5

            # Level 6: Secondary domestic leagues
            if any(t in comp for t in [
                "championship",
                "serie b",
                "ligue 2",
                "2. bundesliga",
                "segunda",
                "liga 2",
                "division",
            ]):
                return 6

            # Level 7: Everything else
            # (lower Argentine divisions, women's etc)
            return 7

        return sorted(matches, key=priority)

    def _enrich(self, matches: list) -> list:
        """
        Add form, H2H, news, weather.
        Only enrich top 25 to save API calls.
        """
        print("\n📊 Enriching match data...")
        all_news = self.news.get_all_news()
        enriched = []
        top_25   = matches[:25]
        the_rest = matches[25:]

        for i, m in enumerate(top_25):
            try:
                home   = m.get("home_team", "")
                away   = m.get("away_team", "")
                source = m.get("source", "")
                comp   = m.get("competition_name", "")

                print(
                    f"   [{i+1}/{len(top_25)}] "
                    f"{home} vs {away} ({comp})"
                )

                # Form and H2H from football-data.org
                home_form = {}
                away_form = {}
                h2h       = {}

                if source == "football_data_org":
                    home_id  = m.get("home_team_id")
                    away_id  = m.get("away_team_id")
                    match_id = m.get("id")

                    if home_id:
                        home_form = \
                            self.fd.get_team_form(
                                home_id
                            )
                        time.sleep(1)

                    if away_id:
                        away_form = \
                            self.fd.get_team_form(
                                away_id
                            )
                        time.sleep(1)

                    if match_id:
                        h2h = self.fd.get_h2h(
                            match_id
                        )
                        time.sleep(1)

                # News impact
                h_impact, h_note = \
                    self.news.get_news_impact(
                        home, all_news
                    )
                a_impact, a_note = \
                    self.news.get_news_impact(
                        away, all_news
                    )

                # Weather
                kick = m.get("kickoff_uk", "15:00")
                try:
                    kh = int(kick.split(":")[0])
                except Exception:
                    kh = 15

                weather = self.wx.get_match_weather(
                    home, kh
                )

                m.update({
                    "home_form":        home_form,
                    "away_form":        away_form,
                    "h2h":             h2h,
                    "home_news_impact": h_impact,
                    "home_news_note":   h_note,
                    "away_news_impact": a_impact,
                    "away_news_note":   a_note,
                    "weather":          weather,
                })

                enriched.append(m)

            except Exception as e:
                print(f"   Enrichment error: {e}")
                enriched.append(m)
                continue

        # Add rest without enrichment
        for m in the_rest:
            m.update({
                "home_form":        {},
                "away_form":        {},
                "h2h":             {},
                "home_news_impact": 0,
                "home_news_note":   "No data",
                "away_news_impact": 0,
                "away_news_note":   "No data",
                "weather": {
                    "description": "Unknown",
                    "impact":      0,
                },
            })
            enriched.append(m)

        print(
            f"\n   ✅ Ready: {len(enriched)} matches"
        )
        return enriched
