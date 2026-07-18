import json
import os
from datetime import datetime
import pytz
from config import ACCURACY_FILE, TIMEZONE


class AccuracyTracker:
    """Tracks prediction accuracy in JSON file."""

    def __init__(self):
        self.tz   = TIMEZONE
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(ACCURACY_FILE):
            try:
                with open(ACCURACY_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "overall_correct":  0,
            "overall_total":    0,
            "streak":           0,
            "best_streak":      0,
            "weekly_breakdown": [],
            "yesterday":        {},
        }

    def save(self):
        os.makedirs(
            os.path.dirname(ACCURACY_FILE),
            exist_ok=True,
        )
        with open(ACCURACY_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def update(self, results: list):
        correct = sum(
            1 for r in results if r.get("correct")
        )
        total = len(results)
        pct   = round(
            correct / total * 100, 1
        ) if total else 0

        now = datetime.now(self.tz)
        day = now.strftime("%A")

        self.data["overall_correct"] += correct
        self.data["overall_total"]   += total

        if correct == total and total > 0:
            self.data["streak"] += total
        elif correct > 0:
            self.data["streak"] = correct
        else:
            self.data["streak"] = 0

        if self.data["streak"] > self.data.get(
            "best_streak", 0
        ):
            self.data["best_streak"] = \
                self.data["streak"]

        entry = {
            "day":     day,
            "date":    now.strftime("%Y-%m-%d"),
            "correct": correct,
            "total":   total,
            "pct":     pct,
        }

        breakdown = self.data.get(
            "weekly_breakdown", []
        )
        breakdown.append(entry)
        self.data["weekly_breakdown"] = \
            breakdown[-14:]
        self.data["yesterday"] = entry
        self.save()

    @property
    def overall(self) -> str:
        c = self.data.get("overall_correct", 0)
        t = self.data.get("overall_total", 0)
        if t < 10:
            return "Building..."
        return f"{round(c/t*100, 1)}% ({c}/{t})"

    @property
    def streak(self) -> int:
        return self.data.get("streak", 0)

    @property
    def week_record(self) -> str:
        last7 = self.data.get(
            "weekly_breakdown", []
        )[-7:]
        if not last7:
            return ""
        c = sum(d.get("correct", 0) for d in last7)
        t = sum(d.get("total", 0) for d in last7)
        return f"{c}/{t}"

    def to_dict(self) -> dict:
        return {
            "overall":          self.overall,
            "streak":           self.streak,
            "best_streak":      self.data.get(
                "best_streak", 0
            ),
            "week_record":      self.week_record,
            "weekly_breakdown": self.data.get(
                "weekly_breakdown", []
            ),
            "yesterday":        self.data.get(
                "yesterday", {}
            ),
        }
