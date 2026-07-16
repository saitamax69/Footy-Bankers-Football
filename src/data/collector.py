import time
from datetime import datetime
import pytz

from src.data.football_data import FootballDataOrg
from src.data.api_football import ApiFootball
from src.data.sports_db import TheSportsDB
from src.data.news import NewsCollector
from src.data.weather import WeatherChecker
from src.data.team_names import match_names


class DataCollector:
    """
    Master data collector.
    Merges all sources.
    Deduplicates.
    Enriches with form, news, weather.
    """

    def __init__(self):
        self.fd   = FootballDataOrg()
        self.af   = ApiFootball()
        self.sdb  = TheSportsDB()
        self.news = NewsCollector()
        self.wx   = WeatherChecker()
        self.tz   = pytz.timezone("Europe/London")

    def get_todays_matches(self) -> list:
        """
        Collect from all sources.
        Deduplicate by normalised team names.
        Return enriched match list.
        """
        print("\n📡 Collecting matches from all sources...")
        seen = set()
        all_matches = []

        # Source 1: football-data.org (primary)
        try:
            fd_matches = self.fd.get_todays_matches()
            for m in fd_matches:
                key = (
                    m["home_team_norm"],
                    m["away_team_norm"],
                )
                if key not in seen:
                    seen.add(key)
                    all_matches.append(m)
            print(
                f"   ✅ football-data.org: "
                f"{len(fd_matches)} matches"
            )
        except Exception as e:
            print(f"   ❌ football-data.org: {e}")

        # Source 2: API-Football (extra leagues)
        try:
            af_matches = self.af.get_todays_matches()
            added = 0
            for m in af_matches:
                key = (
                    m["home_team_norm"],
                    m["away_team_norm"],
                )
                if key not in seen:
                    seen.add(key)
                    all_matches.append(m)
                    added += 1
            print(
                f"   ✅ API-Football: +{added} new"
            )
        except Exception as e:
            print(f"   ❌ API-Football: {e}")

        # Source 3: TheSportsDB (gap filler)
        try:
            sdb_matches = self.sdb.get_todays_matches()
            added = 0
            for m in sdb_matches:
                key = (
                    m["home_team_norm"],
                    m["away_team_norm"],
                )
                if key not in seen:
                    seen.add(key)
                    all_matches.append(m)
                    added += 1
            print(
                f"   ✅ TheSportsDB: +{added} new"
            )
        except Exception as e:
            print(f"   ❌ TheSportsDB: {e}")

        print(
            f"\n   Total unique matches: {len(all_matches)}"
        )

        if not all_matches:
            return []

        return self._enrich(all_matches)

    def _enrich(self, matches: list) -> list:
        """Add form, H2H, news, weather to each match."""
        print("\n📊 Enriching match data...")
        all_news = self.news.get_all_news()
        enriched = []

        for i, m in enumerate(matches):
            try:
                home = m.get("home_team", "")
                away = m.get("away_team", "")
                source = m.get("source", "")

                print(
                    f"   Enriching {i+1}/{len(matches)}: "
                    f"{home} vs {away}"
                )

                # Form data (football-data.org only)
                home_form = {}
                away_form = {}
                h2h = {}

                if source == "football_data_org":
                    home_id = m.get("home_team_id")
                    away_id = m.get("away_team_id")
                    match_id = m.get("id")

                    if home_id:
                        home_form = self.fd.get_team_form(
                            home_id
                        )
                        time.sleep(1)

                    if away_id:
                        away_form = self.fd.get_team_form(
                            away_id
                        )
                        time.sleep(1)

                    if match_id:
                        h2h = self.fd.get_h2h(match_id)
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
                kickoff_str = m.get("kickoff_uk", "15:00")
                try:
                    kickoff_h = int(
                        kickoff_str.split(":")[0]
                    )
                except Exception:
                    kickoff_h = 15

                weather = self.wx.get_match_weather(
                    home, kickoff_h
                )

                m.update({
                    "home_form":          home_form,
                    "away_form":          away_form,
                    "h2h":               h2h,
                    "home_news_impact":  h_impact,
                    "home_news_note":    h_note,
                    "away_news_impact":  a_impact,
                    "away_news_note":    a_note,
                    "weather":           weather,
                })

                enriched.append(m)

            except Exception as e:
                print(f"   Enrichment error: {e}")
                enriched.append(m)

        print(f"\n   ✅ Enriched {len(enriched)} matches")
        return enriched
