import os
import sys
import time
import random
import asyncio
from datetime import datetime
import pytz

from src.data.collector import DataCollector
from src.ai.predictor import FootballPredictor
from src.ai.personality import PersonalityEngine
from src.ai.formatter import PostFormatter
from src.posting.telegram import TelegramPoster
from src.posting.facebook import FacebookPoster
from src.tracking.accuracy import AccuracyTracker
from src.tracking.storage import GitStorage
from src.content.results import ResultChecker
from config import (
    TELEGRAM_MAX_PICKS,
    FACEBOOK_PICKS,
    DELAY_MIN,
    DELAY_MAX,
    TIMEZONE,
    BRAND_NAME,
)


class FootyBankersBot:

    def __init__(self):
        self.tz        = TIMEZONE
        self.collector = DataCollector()
        self.predictor = FootballPredictor()
        self.persona   = PersonalityEngine()
        self.accuracy  = AccuracyTracker()
        self.storage   = GitStorage()
        self.checker   = ResultChecker()
        self.telegram  = TelegramPoster()
        self.facebook  = FacebookPoster()
        self.formatter = PostFormatter(self.persona)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MORNING WORKFLOW
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def run_morning(self):
        now = datetime.now(self.tz)
        print("\n" + "="*50)
        print(f"  {BRAND_NAME}")
        print(f"  MORNING WORKFLOW")
        print(
            f"  {now.strftime('%A %d %B %Y %H:%M')}"
        )
        print("="*50)

        # Human-like random delay
        delay = random.randint(DELAY_MIN, DELAY_MAX)
        print(f"\n⏳ Delay: {delay} minutes...")
        time.sleep(delay * 60)

        # Check Facebook token expiry
        fb_warn = self.facebook.token_warning()
        if fb_warn:
            self.telegram.post(fb_warn)

        # Step 1: Collect matches
        print("\n📡 Step 1: Collecting matches...")
        matches = self.collector.get_todays_matches()

        if not matches:
            print("⚠️  No matches found today")
            tg, fb = self.formatter.no_fixtures_post()
            self.telegram.post(tg)
            self.facebook.post(fb)
            return

        print(f"   Found: {len(matches)} matches")

        # Step 2: AI predictions
        to_analyse = matches[:TELEGRAM_MAX_PICKS]
        print(
            f"\n🤖 Step 2: Analysing "
            f"{len(to_analyse)} matches..."
        )
        all_preds = self.predictor.analyse_all(
            to_analyse
        )

        if not all_preds:
            print("⚠️  No confident predictions today")
            tg, fb = self.formatter.no_fixtures_post()
            self.telegram.post(tg)
            self.facebook.post(fb)
            return

        # Rank predictions
        ranked   = self.predictor.rank_predictions(
            all_preds
        )
        tg_picks = ranked[:TELEGRAM_MAX_PICKS]
        fb_picks = ranked[:FACEBOOK_PICKS]

        print(
            f"   Predictions: "
            f"{len(tg_picks)} for Telegram, "
            f"{len(fb_picks)} for Facebook"
        )

        # Step 3: Add human voice
        print("\n✍️  Step 3: Adding human voice...")
        for pred in tg_picks:
            pred["human_analysis"] = (
                self.persona.write_pick_analysis(pred)
            )

        # Step 4: Format posts
        print("\n📝 Step 4: Formatting posts...")
        acc_data = self.accuracy.to_dict()
        tg_text  = self.formatter.telegram_morning(
            tg_picks, acc_data
        )
        fb_text  = self.formatter.facebook_morning(
            fb_picks, acc_data
        )

        # Step 5: Post to platforms
        print("\n📤 Step 5: Posting...")
        tg_ok = self.telegram.post(tg_text)
        fb_ok = self.facebook.post(fb_text)

        # Step 6: Save predictions for result checking
        if tg_ok or fb_ok:
            self.storage.save_predictions(tg_picks)

        # Summary
        majors  = [
            p for p in tg_picks
            if p.get("is_major")
        ]
        bankers = [
            p for p in tg_picks
            if p.get("tier") == "BANKER"
        ]

        print("\n" + "="*50)
        print("MORNING COMPLETE")
        print(
            f"Telegram:         "
            f"{'✅' if tg_ok else '❌'}"
        )
        print(
            f"Facebook:         "
            f"{'✅' if fb_ok else '❌'}"
        )
        print(f"Total picks:      {len(tg_picks)}")
        print(
            f"Major tournament: {len(majors)}"
        )
        print(f"Banker picks:     {len(bankers)}")
        print("="*50)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EVENING WORKFLOW
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def run_evening(self):
        now = datetime.now(self.tz)
        print("\n" + "="*50)
        print(f"  {BRAND_NAME}")
        print(f"  EVENING WORKFLOW")
        print(
            f"  {now.strftime('%A %d %B %Y %H:%M')}"
        )
        print("="*50)

        # Load todays predictions
        print("\n📂 Loading todays predictions...")
        predictions = (
            self.storage.load_todays_predictions()
        )

        if not predictions:
            print(
                "⚠️  No predictions found for today"
            )
            print(
                "   This means either:"
            )
            print(
                "   1. Morning workflow did not run"
            )
            print(
                "   2. Predictions file was not saved"
            )
            print(
                "   3. Git push failed this morning"
            )
            return

        print(
            f"   Loaded {len(predictions)} "
            f"predictions to check"
        )

        # Check results
        print("\n🔍 Checking results...")
        results = self.checker.check(predictions)

        if not results:
            print(
                "⚠️  No results found yet"
            )
            print(
                "   Possible reasons:"
            )
            print(
                "   1. Games are still being played"
            )
            print(
                "   2. Late kickoff times (check back later)"
            )
            print(
                "   3. API not returning finished matches"
            )

            # Post a "still checking" message
            self._post_pending_message(predictions)
            return

        # Show what we found
        correct = sum(
            1 for r in results if r.get("correct")
        )
        total   = len(results)
        pct     = round(
            correct / total * 100, 1
        ) if total else 0

        print(
            f"\n   Results found: {total}"
        )
        print(
            f"   Correct: {correct}/{total} ({pct}%)"
        )

        # Update accuracy
        print("\n📊 Updating accuracy...")
        self.accuracy.update(results)
        acc_data = self.accuracy.to_dict()

        # Save results to GitHub
        self.storage.save_results(results)

        # Format and post
        print("\n📤 Posting results...")
        tg_text = self.formatter.telegram_results(
            results, acc_data
        )
        fb_text = self.formatter.facebook_results(
            results, acc_data
        )

        tg_ok = self.telegram.post(tg_text)
        fb_ok = self.facebook.post(fb_text)

        print("\n" + "="*50)
        print("EVENING COMPLETE")
        print(
            f"Results:   {correct}/{total} "
            f"({pct}%)"
        )
        print(
            f"Telegram:  "
            f"{'✅' if tg_ok else '❌'}"
        )
        print(
            f"Facebook:  "
            f"{'✅' if fb_ok else '❌'}"
        )
        print(
            f"Streak:    "
            f"{self.accuracy.streak} correct"
        )
        print(
            f"Overall:   {self.accuracy.overall}"
        )
        print("="*50)

    def _post_pending_message(
        self, predictions: list
    ):
        """
        Post when results are not available yet.
        Some games finish very late.
        """
        count = len(predictions)
        tg    = (
            "⏳ *RESULTS PENDING*\n\n"
            f"We have {count} picks from today "
            f"still being checked\\.\n\n"
            f"Some games may still be in progress\\.\n\n"
            f"We will post the final results "
            f"when all games are confirmed\\.\n\n"
            f"*{self._e(BRAND_NAME)}* ⚽🔒"
        )
        self.telegram.post(tg)

    def _e(self, text: str) -> str:
        """Escape MarkdownV2."""
        if not text:
            return ""
        text = str(text)
        for c in [
            "_", "*", "[", "]", "(", ")", "~",
            "`", ">", "#", "+", "-", "=", "|",
            "{", "}", ".", "!",
        ]:
            text = text.replace(c, f"\\{c}")
        return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    mode = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "morning"
    )
    bot = FootyBankersBot()

    if mode == "morning":
        bot.run_morning()
    elif mode == "evening":
        bot.run_evening()
    else:
        print(f"Unknown mode: {mode}")
        print("Use: python main.py morning")
        print("     python main.py evening")
