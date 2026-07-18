from src.data.football_data import FootballDataOrg
from src.data.team_names import normalise


class ResultChecker:
    """
    Checks actual results against predictions.
    """

    def __init__(self):
        self.fd = FootballDataOrg()

    def check(self, predictions: list) -> list:
        results   = []
        finished  = self._get_finished()

        for pred in predictions:
            home = pred.get("home_team", "")
            away = pred.get("away_team", "")
            pick = pred.get("pick", "")

            result = self._find(home, away, finished)
            if not result:
                print(
                    f"⏳ Not finished yet: "
                    f"{home} vs {away}"
                )
                continue

            hg = result.get("home_goals", 0) or 0
            ag = result.get("away_goals", 0) or 0

            results.append({
                "home_team":    home,
                "away_team":    away,
                "pick":         pick,
                "pick_short":   pred.get(
                    "pick_short", pick
                ),
                "actual_score": f"{hg}-{ag}",
                "correct":      self._eval(
                    pick, hg, ag
                ),
                "match_data": {
                    "home_team":        home,
                    "away_team":        away,
                    "competition_name": pred.get(
                        "competition", ""
                    ),
                },
            })

        return results

    def _get_finished(self) -> list:
        try:
            return self.fd.get_todays_matches()
        except Exception:
            return []

    def _find(
        self, home: str, away: str, matches: list
    ) -> dict:
        home_norm = normalise(home)
        away_norm = normalise(away)

        for m in matches:
            mh = m.get("home_team_norm", "")
            ma = m.get("away_team_norm", "")
            if (
                mh == home_norm
                and ma == away_norm
                and m.get("status") == "FINISHED"
            ):
                try:
                    return self.fd.get_result(m["id"])
                except Exception:
                    pass
        return {}

    def _eval(
        self, pick: str, hg: int, ag: int
    ) -> bool:
        p     = pick.lower()
        total = hg + ag

        if "home win" in p or (
            "win" in p
            and "away" not in p
            and not any(
                x in p
                for x in ["over", "under", "btts"]
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
        if "btts" in p or "both teams" in p:
            return hg > 0 and ag > 0
        return False
