import time
from datetime import datetime
import pytz

from src.data.football_data import FootballDataOrg
from src.data.sportdb_api import SportDBApi
from src.data.sports_db import TheSportsDB
from src.data.news import NewsCollector
from src.data.weather import WeatherChecker


class DataCollector:
    """
    Master data collector.

    Priority order:
    1. football-data.org (top leagues, best quality)
    2. SportDB/Flashscore (every league on earth)
    3. TheSportsDB (free backup)

    Deduplicates, enriches, returns clean list.
    """

    def __init__(self):
        self.fd      = FootballDataOrg()
        self.sportdb = SportDBApi()
        self.sdb     = TheSportsDB()
        self.news    = NewsCollector()
        self.wx      = WeatherChecker()
        self.tz      = pytz.timezone("Europe/London")

    def get_todays_matches(self) -> list:
        print(
            "\n📡 Collecting from all data sources..."
        )
        seen        = set()
        all_matches = []

        # Source 1: football-data.org
        try:
            matches = self.fd.get_todays_matches()
            added   = 0
            for m in matches:
                key = (
                    m["home_team_norm"],
                    m["away_team_norm"],
                )
                if key not in seen:
                    seen.add(key)
                    all_matches.append(m)
                    added += 1
            print(
                f"   ✅ football-data.org: "
                f"{added} matches"
            )
        except Exception as e:
            print(f"   ❌ football-data.org: {e}")

        # Source 2: SportDB / Flashscore
        try:
            if self.sportdb.api_key:
                matches = \
                    self.sportdb.get_todays_matches()
                added = 0
                for m in matches:
                    key = (
                        m.get("home_team_norm", ""),
                        m.get("away_team_norm", ""),
                    )
                    if key[0] and key not in seen:
                        seen.add(key)
                        all_matches.append(m)
                        added += 1
                print(
                    f"   ✅ SportDB/Flashscore: "
                    f"+{added} new"
                )
            else:
                print("   ⚠️  SportDB: No key set")
        except Exception as e:
            print(f"   ❌ SportDB: {e}")

        # Source 3: TheSportsDB (free backup)
        try:
            matches = self.sdb.get_todays_matches()
            added   = 0
            for m in matches:
                if not m.get("home_team"):
                    continue
                key = (
                    m.get("home_team_norm", ""),
                    m.get("away_team_norm", ""),
                )
                if key[0] and key not in seen:
                    seen.add(key)
                    all_matches.append(m)
                    added += 1
            print(
                f"   ✅ TheSportsDB: +{added} new"
            )
        except Exception as e:
            print(f"   ❌ TheSportsDB: {e}")

        total = len(all_matches)
        print(f"\n   Total unique matches: {total}")

        if not all_matches:
            return []

        return self._enrich(all_matches)

    def get_live_scores(self) -> list:
        """Live scores for result checking."""
        try:
            if self.sportdb.api_key:
                live = self.sportdb.get_live_scores()
                if live:
                    return live
        except Exception as e:
            print(f"Live scores error: {e}")
        return []

    def _enrich(self, matches: list) -> list:
        print("\n📊 Enriching match data...")
        all_news = self.news.get_all_news()
        enriched = []

        for i, m in enumerate(matches):
            try:
                home   = m.get("home_team", "")
                away   = m.get("away_team", "")
                source = m.get("source", "")

                print(
                    f"   [{i+1}/{len(matches)}] "
                    f"{home} vs {away}"
                )

                home_form = {}
                away_form = {}
                h2h       = {}

                if source == "football_data_org":
                    home_id  = m.get("home_team_id")
                    away_id  = m.get("away_team_id")
                    match_id = m.get("id")

                    if home_id:
                        home_form = \
                            self.fd.get_team_form(home_id)
                        time.sleep(1)
                    if away_id:
                        away_form = \
                            self.fd.get_team_form(away_id)
                        time.sleep(1)
                    if match_id:
                        h2h = self.fd.get_h2h(match_id)
                        time.sleep(1)

                h_impact, h_note = \
                    self.news.get_news_impact(
                        home, all_news
                    )
                a_impact, a_note = \
                    self.news.get_news_impact(
                        away, all_news
                    )

                kickoff_str = m.get(
                    "kickoff_uk", "15:00"
                )
                try:
                    kickoff_h = int(
                        kickoff_str.split(":")[0]
                    )
                except Exception:
                    kickoff_h = 15

                weather = self.wx.get_match_weather(
                    home, kickoff_h
                )

                home_value = {}
                away_value = {}

                if (
                    source == "sportdb_api"
                    and self.sportdb.api_key
                ):
                    try:
                        home_value = \
                            self.sportdb.get_squad_value(
                                home
                            )
                        away_value = \
                            self.sportdb.get_squad_value(
                                away
                            )
                    except Exception:
                        pass

                m.update({
                    "home_form":        home_form,
                    "away_form":        away_form,
                    "h2h":             h2h,
                    "home_news_impact": h_impact,
                    "home_news_note":   h_note,
                    "away_news_impact": a_impact,
                    "away_news_note":   a_note,
                    "weather":          weather,
                    "home_squad_value": home_value,
                    "away_squad_value": away_value,
                })

                enriched.append(m)

            except Exception as e:
                print(f"   Enrichment error: {e}")
                enriched.append(m)

        print(
            f"\n   ✅ Enriched {len(enriched)} matches"
        )
        return enriched
