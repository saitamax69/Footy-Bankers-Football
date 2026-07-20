import os
import json
import subprocess
from datetime import datetime
import pytz
from config import PREDICTIONS_DIR, RESULTS_DIR


class GitStorage:
    """
    Stores predictions and results as JSON files.
    Commits to GitHub for public verification.

    This creates an immutable public record
    of every prediction we have ever made.
    """

    def __init__(self):
        self.tz = pytz.timezone("Europe/London")
        self._configure_git()

    def _configure_git(self):
        """Configure git with token authentication."""
        try:
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
                print("Git: configured with token")
            else:
                print(
                    "Git: no token found, "
                    "push may fail"
                )

        except Exception as e:
            print(f"Git config error: {e}")

    def save_predictions(
        self, predictions: list
    ) -> str:
        """Save todays predictions to JSON file."""
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        os.makedirs(PREDICTIONS_DIR, exist_ok=True)
        path = f"{PREDICTIONS_DIR}/{today}.json"

        clean = []
        for p in predictions:
            m = p.get("match_data", {})
            clean.append({
                "home_team":   m.get("home_team"),
                "away_team":   m.get("away_team"),
                "competition": m.get(
                    "competition_name", ""
                ),
                "kickoff":     m.get("kickoff_uk"),
                "pick":        p.get("pick"),
                "pick_short":  p.get("pick_short"),
                "confidence":  p.get("confidence"),
                "tier":        p.get("tier"),
                "is_major":    p.get(
                    "is_major", False
                ),
                "status":      "PENDING",
                "posted_at":   datetime.now(
                    self.tz
                ).isoformat(),
            })

        with open(path, "w") as f:
            json.dump(clean, f, indent=2)

        print(
            f"💾 Saved {len(clean)} predictions "
            f"to {path}"
        )
        self._commit(
            path, f"Predictions {today}"
        )
        return path

    def save_results(self, results: list) -> str:
        """Save todays results to JSON file."""
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        os.makedirs(RESULTS_DIR, exist_ok=True)
        path = f"{RESULTS_DIR}/{today}.json"

        # Save clean version
        clean = []
        for r in results:
            clean.append({
                "home_team":    r.get("home_team"),
                "away_team":    r.get("away_team"),
                "competition":  r.get("competition"),
                "pick":         r.get("pick"),
                "pick_short":   r.get("pick_short"),
                "confidence":   r.get("confidence"),
                "tier":         r.get("tier"),
                "actual_score": r.get("actual_score"),
                "correct":      r.get("correct"),
                "checked_at":   datetime.now(
                    self.tz
                ).isoformat(),
            })

        with open(path, "w") as f:
            json.dump(clean, f, indent=2)

        print(
            f"💾 Saved {len(clean)} results "
            f"to {path}"
        )
        self._commit(path, f"Results {today}")
        return path

    def load_todays_predictions(self) -> list:
        """Load predictions saved this morning."""
        today = datetime.now(self.tz).strftime(
            "%Y-%m-%d"
        )
        path = f"{PREDICTIONS_DIR}/{today}.json"

        if not os.path.exists(path):
            print(
                f"No predictions file found: {path}"
            )
            return []

        try:
            with open(path, "r") as f:
                data = json.load(f)
                print(
                    f"Loaded {len(data)} predictions"
                )
                return data
        except Exception as e:
            print(
                f"Error loading predictions: {e}"
            )
            return []

    def load_results_for_date(
        self, date: str = None
    ) -> list:
        """Load results for a specific date."""
        if not date:
            date = datetime.now(self.tz).strftime(
                "%Y-%m-%d"
            )
        path = f"{RESULTS_DIR}/{date}.json"

        if not os.path.exists(path):
            return []

        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def get_all_time_stats(self) -> dict:
        """
        Read all saved results and compute
        all-time statistics.
        Used for weekly review posts.
        """
        total   = 0
        correct = 0

        if not os.path.exists(RESULTS_DIR):
            return {"total": 0, "correct": 0}

        for fname in os.listdir(RESULTS_DIR):
            if not fname.endswith(".json"):
                continue
            try:
                with open(
                    f"{RESULTS_DIR}/{fname}", "r"
                ) as f:
                    results = json.load(f)
                    for r in results:
                        if r.get("correct") is None:
                            continue
                        total += 1
                        if r.get("correct"):
                            correct += 1
            except Exception:
                continue

        return {
            "total":   total,
            "correct": correct,
            "pct":     round(
                correct / total * 100, 1
            ) if total else 0,
        }

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
                stderr = result.stderr.lower()
                if "nothing to commit" in stderr or \
                   "nothing to commit" in \
                   result.stdout.lower():
                    print("Git: nothing new to commit")
                    return
                print(
                    f"Git commit issue: "
                    f"{result.stderr[:100]}"
                )
                return

            push = subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True,
            )

            if push.returncode == 0:
                print(f"✅ Git: committed {msg}")
            else:
                print(
                    f"⚠️  Git push failed: "
                    f"{push.stderr[:100]}"
                )
                print(
                    "Note: Data saved locally. "
                    "Check GH_TOKEN has repo scope."
                )

        except subprocess.CalledProcessError as e:
            print(f"Git error: {e}")
        except Exception as e:
            print(f"Git error: {e}")
