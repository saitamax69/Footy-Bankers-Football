import os
import time
import json
from datetime import datetime
import pytz

from src.data.sportdb_api import SportDBApi
from src.data.football_data import FootballDataOrg
from src.data.team_names import normalise


class ResultChecker:
    """
    Checks actual results against our predictions.

    Strategy:
    1. Get ALL finished matches today from Flashscore
    2. Get finished matches from football-data.org
    3. Match predictions to results by team names
    4. Use fuzzy matching for name variations
    5. Evaluate if our pick was correct
    6. Log everything for accountability
    """

    def __init__(self):
        self.sportdb = SportDBApi()
        self.fd      = FootballDataOrg()
        self.tz      = pytz.timezone("Europe/London")

    def check(self, predictions: list) -> list:
        """
        Main method. Check all predictions.
        Returns list with correct/wrong added.
        """
        if not predictions:
            print("No predictions to check")
            return []

        print(
            f"\n🔍 Checking {len(predictions)} "
            f"predictions..."
        )

        # Step 1: Collect all finished matches
        print("\n   Getting finished matches...")
        finished = self._get_all_finished()
        print(
            f"   Found {len(finished)} "
            f"finished matches today"
        )

        if not finished:
            print(
                "   ⚠️  No finished matches found yet"
            )
            print(
                "   This is normal if games "
                "are still being played"
            )
            return []

        # Step 2: Match predictions to results
        results = []
        found   = 0
        missing = 0

        for pred in predictions:
            home = pred.get("home_team", "")
            away = pred.get("away_team", "")
            pick = pred.get("pick", "")

            if not home or not away:
                continue

            print(
                f"\n   Checking: {home} vs {away}"
            )

            # Find result by team name matching
            result = self._find_result(
                home, away, finished
            )

            if result:
                hg      = result["home_goals"]
                ag      = result["away_goals"]
                correct = self._evaluate(pick, hg, ag)

                print(
                    f"   Found: {hg}-{ag} → "
                    f"{'✅ CORRECT' if correct else '❌ WRONG'}"
                )

                results.append({
                    "home_team":    home,
                    "away_team":    away,
                    "competition":  pred.get(
                        "competition", ""
                    ),
                    "pick":         pick,
                    "pick_short":   pred.get(
                        "pick_short", pick
                    ),
                    "confidence":   pred.get(
                        "confidence", 0
                    ),
                    "tier":         pred.get("tier", ""),
                    "actual_score": f"{hg}-{ag}",
                    "home_goals":   hg,
                    "away_goals":   ag,
                    "correct":      correct,
                    "found":        True,
                    "match_data": {
                        "home_team":        home,
                        "away_team":        away,
                        "competition_name": pred.get(
                            "competition", ""
                        ),
                    },
                })
                found += 1

            else:
                print(
                    f"   Not found yet "
                    f"(may still be playing)"
                )
                results.append({
                    "home_team":    home,
                    "away_team":    away,
                    "competition":  pred.get(
                        "competition", ""
                    ),
                    "pick":         pick,
                    "pick_short":   pred.get(
                        "pick_short", pick
                    ),
                    "confidence":   pred.get(
                        "confidence", 0
                    ),
                    "tier":         pred.get("tier", ""),
                    "actual_score": "Pending",
                    "correct":      None,
                    "found":        False,
                    "match_data": {
                        "home_team":        home,
                        "away_team":        away,
                        "competition_name": pred.get(
                            "competition", ""
                        ),
                    },
                })
                missing += 1

        print(
            f"\n   Results: {found} found, "
            f"{missing} still pending"
        )

        # Only return results we actually found
        confirmed = [
            r for r in results if r.get("found")
        ]

        return confirmed

    def _get_all_finished(self) -> list:
        """
        Get ALL finished matches today
        from multiple sources.
        """
        all_finished = []
        seen         = set()

        # ── Source 1: Flashscore live endpoint ──
        # Contains finished (FINISHED eventStage)
        # and live matches
        try:
            print(
                "   Checking Flashscore live feed..."
            )
            live = self.sportdb._get(
                "/flashscore/football/live"
            )
            if live and isinstance(live, list):
                for m in live:
                    stage = str(
                        m.get("eventStage", "")
                    ).upper()
                    # Include FINISHED matches
                    if "FINISH" in stage or \
                       stage in ["4", "FT", "AET"]:
                        parsed = self._parse_result(m)
                        if parsed:
                            key = (
                                parsed["home_norm"],
                                parsed["away_norm"],
                            )
                            if key not in seen:
                                seen.add(key)
                                all_finished.append(
                                    parsed
                                )
                print(
                    f"   Flashscore live: "
                    f"{len(all_finished)} finished"
                )
        except Exception as e:
            print(f"   Flashscore live error: {e}")

        time.sleep(0.5)

        # ── Source 2: Competition results endpoints ──
        # Each competition has a results URL
        try:
            print(
                "   Checking competition results..."
            )
            comp_found = 0

            for country_path, comp_path, \
                    name, tier in \
                    self.sportdb.VERIFIED_COMPETITIONS[
                        :15
                    ]:

                comp_url = (
                    f"/flashscore/football"
                    f"/{country_path}/{comp_path}"
                )
                comp_info = self.sportdb._get(comp_url)

                if not comp_info or \
                   not isinstance(comp_info, dict):
                    continue

                seasons = comp_info.get("seasons", [])
                if not seasons:
                    continue

                results_url = seasons[0].get(
                    "results", ""
                )
                if not results_url:
                    continue

                results_data = self.sportdb._get(
                    results_url
                )
                if not results_data:
                    continue

                matches = self.sportdb._extract_list(
                    results_data
                )

                # Filter to today only
                todays = self.sportdb._filter_today(
                    matches
                )

                for m in todays:
                    parsed = self._parse_result(m)
                    if parsed:
                        key = (
                            parsed["home_norm"],
                            parsed["away_norm"],
                        )
                        if key not in seen:
                            seen.add(key)
                            all_finished.append(parsed)
                            comp_found += 1

                time.sleep(0.2)

            print(
                f"   Competition results: "
                f"+{comp_found} more"
            )

        except Exception as e:
            print(
                f"   Competition results error: {e}"
            )

        time.sleep(0.5)

        # ── Source 3: football-data.org ──
        # Covers top European leagues
        try:
            print(
                "   Checking football-data.org..."
            )
            today = datetime.now(self.tz).strftime(
                "%Y-%m-%d"
            )
            fd_matches = self.fd.get_todays_matches()
            fd_found   = 0

            for m in fd_matches:
                if m.get("status") != "FINISHED":
                    continue

                # Get the result
                match_id = m.get("id")
                if not match_id:
                    continue

                result = self.fd.get_result(match_id)
                if not result:
                    continue

                hg = result.get("home_goals")
                ag = result.get("away_goals")

                if hg is None or ag is None:
                    continue

                home = m.get("home_team", "")
                away = m.get("away_team", "")

                if not home or not away:
                    continue

                key = (
                    normalise(home),
                    normalise(away),
                )

                if key not in seen:
                    seen.add(key)
                    all_finished.append({
                        "home":        home,
                        "away":        away,
                        "home_norm":   normalise(home),
                        "away_norm":   normalise(away),
                        "home_goals":  int(hg),
                        "away_goals":  int(ag),
                        "competition": m.get(
                            "competition_name", ""
                        ),
                        "source":      "football_data",
                    })
                    fd_found += 1

                time.sleep(0.5)

            print(
                f"   football-data.org: "
                f"+{fd_found} more"
            )

        except Exception as e:
            print(
                f"   football-data.org error: {e}"
            )

        print(
            f"\n   Total finished matches: "
            f"{len(all_finished)}"
        )
        return all_finished

    def _parse_result(self, m: dict) -> dict:
        """
        Parse a match object into result format.
        Tries every known field name for scores.
        """
        if not isinstance(m, dict):
            return None

        # Team names
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
            return None
        if len(home) < 2 or len(away) < 2:
            return None

        # Scores - try every possible field name
        home_goals = (
            m.get("homeScore")
            or m.get("home_score")
            or m.get("homeGoals")
            or m.get("home_goals")
            or m.get("score", {}).get("home")
            if isinstance(m.get("score"), dict)
            else None
        )

        away_goals = (
            m.get("awayScore")
            or m.get("away_score")
            or m.get("awayGoals")
            or m.get("away_goals")
            or m.get("score", {}).get("away")
            if isinstance(m.get("score"), dict)
            else None
        )

        # Try nested score object
        if home_goals is None:
            score = m.get("score", {})
            if isinstance(score, dict):
                ft = (
                    score.get("fullTime")
                    or score.get("full_time")
                    or score
                )
                if isinstance(ft, dict):
                    home_goals = (
                        ft.get("home")
                        or ft.get("homeTeam")
                    )
                    away_goals = (
                        ft.get("away")
                        or ft.get("awayTeam")
                    )

        # If we still do not have scores skip
        if home_goals is None or away_goals is None:
            return None

        try:
            hg = int(str(home_goals).split(".")[0])
            ag = int(str(away_goals).split(".")[0])
        except (ValueError, TypeError):
            return None

        return {
            "home":       home,
            "away":       away,
            "home_norm":  normalise(home),
            "away_norm":  normalise(away),
            "home_goals": hg,
            "away_goals": ag,
            "source":     "sportdb",
        }

    def _find_result(
        self,
        home: str,
        away: str,
        finished: list,
    ) -> dict:
        """
        Find result for a prediction by team names.

        Uses multiple matching strategies:
        1. Exact normalised name match
        2. One team exact + other partial
        3. Both teams partial match
        """
        home_norm = normalise(home)
        away_norm = normalise(away)

        # Strategy 1: Both names exact match
        for f in finished:
            if (
                f["home_norm"] == home_norm
                and f["away_norm"] == away_norm
            ):
                return f

        # Strategy 2: Reversed (in case home/away swapped)
        for f in finished:
            if (
                f["home_norm"] == away_norm
                and f["away_norm"] == home_norm
            ):
                # Swap goals to correct orientation
                return {
                    **f,
                    "home_goals": f["away_goals"],
                    "away_goals": f["home_goals"],
                }

        # Strategy 3: Partial matching
        # Team names sometimes differ slightly
        # e.g. "Man City" vs "Manchester City"
        for f in finished:
            fh = f["home_norm"]
            fa = f["away_norm"]

            home_match = (
                home_norm in fh
                or fh in home_norm
                or self._similarity(
                    home_norm, fh
                ) > 0.8
            )
            away_match = (
                away_norm in fa
                or fa in away_norm
                or self._similarity(
                    away_norm, fa
                ) > 0.8
            )

            if home_match and away_match:
                return f

        return None

    def _similarity(
        self, a: str, b: str
    ) -> float:
        """
        Simple string similarity score.
        0 = completely different
        1 = identical
        """
        if not a or not b:
            return 0.0

        a = a.lower().strip()
        b = b.lower().strip()

        if a == b:
            return 1.0

        # Check if one contains the other
        if a in b or b in a:
            shorter = min(len(a), len(b))
            longer  = max(len(a), len(b))
            return shorter / longer

        # Count matching characters
        matches = sum(
            c in b for c in a
        )
        total = max(len(a), len(b))
        return matches / total if total else 0.0

    def _evaluate(
        self,
        pick: str,
        home_goals: int,
        away_goals: int,
    ) -> bool:
        """
        Evaluate if our pick was correct
        given the actual score.
        """
        pick  = pick.lower()
        total = home_goals + away_goals

        # Home win
        if "home win" in pick or (
            "win" in pick
            and "away" not in pick
            and not any(
                x in pick for x in [
                    "over", "under", "btts",
                    "both", "draw"
                ]
            )
        ):
            return home_goals > away_goals

        # Away win
        if "away win" in pick:
            return away_goals > home_goals

        # Draw
        if "draw" in pick:
            return home_goals == away_goals

        # Over 2.5
        if "over 2.5" in pick or "over2.5" in pick:
            return total > 2

        # Under 2.5
        if "under 2.5" in pick or "under2.5" in pick:
            return total < 3

        # Over 1.5
        if "over 1.5" in pick:
            return total > 1

        # Under 3.5
        if "under 3.5" in pick:
            return total < 4

        # BTTS
        if "btts" in pick or \
           "both teams" in pick or \
           "both to score" in pick:
            return home_goals > 0 and away_goals > 0

        # BTTS No
        if "btts no" in pick or \
           "both teams no" in pick:
            return not (
                home_goals > 0 and away_goals > 0
            )

        # Default: check if home win
        # (for picks like "City Win" without Home/Away)
        return home_goals > away_goals
