from src.data.football_data import FootballDataOrg


class ResultChecker:
    """
    Checks actual results against predictions.
    Cross-references two sources.
    """

    def __init__(self):
        self.fd = FootballDataOrg()

    def check(self, predictions: list) -> list:
        """
        Match predictions to results.
        Return updated list with correct field.
        """
        results = []

        for pred in predictions:
            home = pred.get("home_team", "")
            away = pred.get("away_team", "")
            pick = pred.get("pick", "")

            result = self._find_result(home, away)

            if not result:
                print(
                    f"⏳ Result not yet available: "
                    f"{home} vs {away}"
                )
                continue

            hg = result.get("home_goals", 0)
            ag = result.get("away_goals", 0)

            correct = self._evaluate(pick, hg, ag)

            results.append({
                "home_team":    home,
                "away_team":    away,
                "pick":         pick,
                "pick_short":   pred.get("pick_short", pick),
                "actual_score": f"{hg}-{ag}",
                "correct":      correct,
                "match_data": {
                    "home_team": home,
                    "away_team": away,
                    "competition_name": pred.get(
                        "competition", ""
                    ),
                },
            })

        return results

    def _find_result(
        self, home: str, away: str
    ) -> dict:
        """Find result from API."""
        try:
            todays = self.fd.get_todays_matches()
            for m in todays:
                if (
                    m.get("home_team_norm") == home
                    or m.get("home_team") == home
                ) and (
                    m.get("away_team_norm") == away
                    or m.get("away_team") == away
                ):
                    if m.get("status") == "FINISHED":
                        return self.fd.get_result(
                            m["id"]
                        )
        except Exception as e:
            print(f"Result lookup error: {e}")
        return {}

    def _evaluate(
        self, pick: str, hg: int, ag: int
    ) -> bool:
        """Evaluate if pick was correct."""
        p = pick.lower()
        total = hg + ag

        if "home win" in p or (
            "win" in p and "away" not in p
            and not any(
                x in p for x in [
                    "over", "under", "btts"
                ]
            )
        ):
            return hg > ag

        if "away win" in p:
            return ag > hg

        if "draw" in p:
            return hg == ag

        if "over 2.5" in p:
            return total > 2

        if "under 2.5" in p:
            return total < 3

        if "btts" in p or "both teams to score" in p:
            return hg > 0 and ag > 0

        return False
