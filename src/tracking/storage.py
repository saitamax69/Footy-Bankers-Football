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
    """

    def __init__(self):
        self.tz = pytz.timezone("Europe/London")
        self._configure_git()

    def _configure_git(self):
        """Configure git for GitHub Actions."""
        try:
            # Set identity
            subprocess.run(
                [
                    "git", "config", "--global",
                    "user.email",
                    "bot@footybankersfootball.com",
                ],
                capture_output=True,
            )
            subprocess.run(
                [
                    "git", "config", "--global",
                    "user.name",
                    "FootyBankers Bot",
                ],
                capture_output=True,
            )

            # Set remote URL with token for push auth
            token = os.environ.get("GH_TOKEN", "")
            repo  = os.environ.get(
                "GITHUB_REPOSITORY", ""
            )

            if token and repo:
                remote_url = (
                    f"https://x-access-token:{token}"
                    f"@github.com/{repo}"
                )
                subprocess.run(
                    [
                        "git", "remote", "set-url",
                        "origin", remote_url,
                    ],
                    capture_output=True,
                )
                print("Git configured with token auth")

        except Exception as e:
            print(f"Git config note: {e}")

    def save_predictions(
        self, predictions: list
    ) -> str:
        """Save todays predictions."""
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
                "is_major":   p.get("is_major", False),
                "status":     "PENDING",
            })

        with open(path, "w") as f:
            json.dump(clean, f, indent=2)

        self._commit(path, f"Predictions {today}")
        return path

    def save_results(self, results: list) -> str:
        """Save todays results."""
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        os.makedirs(RESULTS_DIR, exist_ok=True)
        path = f"{RESULTS_DIR}/{today}.json"

        with open(path, "w") as f:
            json.dump(results, f, indent=2)

        self._commit(path, f"Results {today}")
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
        """Commit and push file to GitHub."""
        try:
            subprocess.run(
                ["git", "add", filepath],
                check=True,
                capture_output=True,
            )

            result = subprocess.run(
                ["git", "commit", "-m", msg],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                if "nothing to commit" in result.stdout:
                    print(f"Git: Nothing new to commit")
                    return
                print(f"Git commit issue: {result.stderr}")
                return

            push_result = subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True,
            )

            if push_result.returncode == 0:
                print(f"✅ Git: committed {msg}")
            else:
                print(
                    f"⚠️ Git push failed: "
                    f"{push_result.stderr[:100]}"
                )
                print(
                    "Note: Data saved locally, "
                    "push failed. Check GH_TOKEN."
                )

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git error: {e}")
        except Exception as e:
            print(f"⚠️ Git error: {e}")
