import os
import json
import subprocess
from datetime import datetime
import pytz
from config import PREDICTIONS_DIR, RESULTS_DIR


class GitStorage:
    """
    Stores predictions and results
    as JSON files committed to GitHub.
    Creates permanent verifiable record.
    """

    def __init__(self):
        self.tz = pytz.timezone("Europe/London")

        # Configure git for GitHub Actions
        try:
            subprocess.run(
                [
                    "git", "config", "--global",
                    "user.email",
                    "bot@footybankersfootball.com",
                ],
                check=True, capture_output=True,
            )
            subprocess.run(
                [
                    "git", "config", "--global",
                    "user.name",
                    "Footy Bankers Bot",
                ],
                check=True, capture_output=True,
            )
        except Exception as e:
            print(f"Git config note: {e}")

    def save_predictions(
        self, predictions: list
    ) -> str:
        """Save today's predictions to file."""
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        os.makedirs(PREDICTIONS_DIR, exist_ok=True)
        path = f"{PREDICTIONS_DIR}/{today}.json"

        clean = []
        for p in predictions:
            m = p.get("match_data", {})
            clean.append({
                "home_team":  m.get("home_team"),
                "away_team":  m.get("away_team"),
                "competition": m.get("competition_name"),
                "kickoff":    m.get("kickoff_uk"),
                "pick":       p.get("pick"),
                "pick_short": p.get("pick_short"),
                "confidence": p.get("confidence"),
                "tier":       p.get("tier"),
                "status":     "PENDING",
            })

        with open(path, "w") as f:
            json.dump(clean, f, indent=2)

        self._commit(
            path,
            f"Predictions {today}"
        )
        return path

    def save_results(
        self, results: list
    ) -> str:
        """Save today's results to file."""
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        os.makedirs(RESULTS_DIR, exist_ok=True)
        path = f"{RESULTS_DIR}/{today}.json"

        with open(path, "w") as f:
            json.dump(results, f, indent=2)

        self._commit(
            path,
            f"Results {today}"
        )
        return path

    def load_todays_predictions(self) -> list:
        """Load predictions saved this morning."""
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        path = f"{PREDICTIONS_DIR}/{today}.json"

        if not os.path.exists(path):
            return []

        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Load predictions error: {e}")
            return []

    def _commit(self, filepath: str, msg: str):
        """Commit file to GitHub repo."""
        try:
            subprocess.run(
                ["git", "add", filepath],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", msg],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "push"],
                check=True, capture_output=True,
            )
            print(f"✅ Git: committed {msg}")
        except subprocess.CalledProcessError as e:
            print(
                f"⚠️ Git commit note: "
                f"{e.stderr.decode()[:100]}"
            )
        except Exception as e:
            print(f"⚠️ Git error: {e}")
