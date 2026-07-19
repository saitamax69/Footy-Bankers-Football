import time
from datetime import datetime
import pytz

from src.data.football_data import FootballDataOrg
from src.data.sports_db import TheSportsDB
from src.data.sportdb_api import SportDBApi
from src.data.news import NewsCollector
from src.data.weather import WeatherChecker
from config import MAJOR_TOURNAMENTS


class DataCollector:
    """
    Master data collector.

    Priority order:
    1. SportDB/Flashscore FIRST
       Covers everything: World Cup, UCL, all leagues
    2. football-data.org
       Top European leagues when in season
    3. TheSportsDB
       Free backup for extra coverage

    Flashscore must be first so we never
    miss major tournaments like World Cup.
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
        Flashscore first.
        Deduplicate.
        Prioritise major tournaments.
        Enrich and return.
        """
        print("\n📡 Collecting matches...")
        seen        = set()
        all_matches = []

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # SOURCE 1: SportDB Flashscore (PRIORITY)
        # Covers World Cup, UCL, everything
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n   [1/3] SportDB Flashscore...")
        try:
            if self.sportdb.api_key:
                flash = self.sportdb.get_todays_matches(
                    max_countries=30
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
                print(
                    "   ⚠️  No SPORTDB_API_KEY set"
                )
        except Exception as e:
            print(f"   ❌ Flashscore error: {e}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # SOURCE 2: football-data.org
        # Top European leagues
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
                f"   ✅ football-data.org: "
                f"+{added} new"
            )
        except Exception as e:
            print(f"   ❌ football-data.org: {e}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # SOURCE 3: TheSportsDB (free backup)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
            print(
                f"   ✅ TheSportsDB: +{added} new"
            )
        except Exception as e:
            print(f"   ❌ TheSportsDB: {e}")

        total = len(all_matches)
        print(f"\n   📊 Total: {total} unique matches")

        if not all_matches:
            print("   ⚠️  No matches found today")
            return []

        # Sort major tournaments to the top
        all_matches = self._sort_by_priority(
            all_matches
        )

        # Enrich with form, news, weather
        return self._enrich(all_matches)

    def _sort_by_priority(
        self, matches: list
    ) -> list:
        """
        Sort matches so major tournaments
        are analysed first.
        World Cup > UCL > Top 5 leagues > Rest
        """

        def priority(m):
            comp = (
                m.get("competition_name", "")
                + " " +
                m.get("competition_code", "")
            ).lower()

            # World Cup always first
            if any(
                t in comp for t in [
                    "world cup", "worldcup",
                    "fifa world cup",
                ]
            ):
                return 0

            # UCL/Europa/Continental
            if any(
                t in comp for t in [
                    "champions league",
                    "europa league",
                    "conference league",
                    "copa america",
                    "euros", "euro ",
                    "afcon", "africa cup",
                ]
            ):
                return 1

            # Top 5 leagues
            if any(
                t in comp for t in [
                    "premier league", "la liga",
                    "bundesliga", "serie a",
                    "ligue 1",
                ]
            ):
                return 2

            # Other European/big leagues
            if any(
                t in comp for t in [
                    "eredivisie", "primeira liga",
                    "championship", "scottish",
                    "turkish", "brasileirao",
                    "mls",
                ]
            ):
                return 3

            # Everything else
            return 4

        return sorted(matches, key=priority)

    def _enrich(self, matches: list) -> list:
        """
        Add form, H2H, news, weather.
        Only enrich top 25 to save API calls.
        Rest get basic data.
        """
        print("\n📊 Enriching match data...")
        all_news  = self.news.get_all_news()
        enriched  = []
        top_25    = matches[:25]
        the_rest  = matches[25:]

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
                        h2h = self.fd.get_h2h(match_id)
                        time.sleep(1)

                # News impact for both teams
                h_impact, h_note = \
                    self.news.get_news_impact(
                        home, all_news
                    )
                a_impact, a_note = \
                    self.news.get_news_impact(
                        away, all_news
                    )

                # Weather at kickoff time
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

        # Add rest without full enrichment
        for m in the_rest:
            m.update({
                "home_form":        {},
                "away_form":        {},
                "h2h":             {},
                "home_news_impact": 0,
                "home_news_note":   "No data available",
                "away_news_impact": 0,
                "away_news_note":   "No data available",
                "weather": {
                    "description": "Unknown",
                    "impact":      0,
                },
            })
            enriched.append(m)

        print(
            f"\n   ✅ Enriched: "
            f"{len(enriched)} matches ready"
        )
        return enriched
