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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MORNING WORKFLOW
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        print(
            f"\n🤖 Step 2: Analysing "
            f"{min(len(matches), TELEGRAM_MAX_PICKS)} "
            f"matches..."
        )
        all_preds = self.predictor.analyse_all(
            matches[:TELEGRAM_MAX_PICKS]
        )

        if not all_preds:
            print("⚠️  No confident predictions today")
            tg, fb = self.formatter.no_fixtures_post()
            self.telegram.post(tg)
            self.facebook.post(fb)
            return

        # Rank predictions
        ranked = self.predictor.rank_predictions(
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
            pred["human_analysis"] = \
                self.persona.write_pick_analysis(pred)

        # Step 4: Format posts
        print("\n📝 Step 4: Formatting posts...")
        acc_data = self.accuracy.to_dict()

        tg_text = self.formatter.telegram_morning(
            tg_picks, acc_data
        )
        fb_text = self.formatter.facebook_morning(
            fb_picks, acc_data
        )

        # Step 5: Post to platforms
        print("\n📤 Step 5: Posting...")
        tg_ok = self.telegram.post(tg_text)
        fb_ok = self.facebook.post(fb_text)

        # Step 6: Save predictions
        if tg_ok or fb_ok:
            self.storage.save_predictions(tg_picks)
            print("💾 Predictions saved to GitHub")

        # Summary
        majors = [
            p for p in tg_picks
            if p.get("is_major")
        ]
        bankers = [
            p for p in tg_picks
            if p.get("tier") == "BANKER"
        ]

        print("\n" + "="*50)
        print("MORNING COMPLETE")
        print(f"Telegram:  {'✅' if tg_ok else '❌'}")
        print(f"Facebook:  {'✅' if fb_ok else '❌'}")
        print(f"Total picks:    {len(tg_picks)}")
        print(f"Major tournament: {len(majors)}")
        print(f"Banker picks:   {len(bankers)}")
        print("="*50)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EVENING WORKFLOW
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        predictions = \
            self.storage.load_todays_predictions()

        if not predictions:
            print("No predictions to check tonight")
            return

        print(
            f"\n🔍 Checking "
            f"{len(predictions)} predictions..."
        )

        # Check results
        results = self.checker.check(predictions)

        if not results:
            print("Results not yet available")
            return

        # Update accuracy
        self.accuracy.update(results)
        acc_data = self.accuracy.to_dict()

        # Save results
        self.storage.save_results(results)

        # Format and post
        tg_text = self.formatter.telegram_results(
            results, acc_data
        )
        fb_text = self.formatter.facebook_results(
            results, acc_data
        )

        tg_ok = self.telegram.post(tg_text)
        fb_ok = self.facebook.post(fb_text)

        correct = sum(
            1 for r in results if r.get("correct")
        )

        print("\n" + "="*50)
        print("EVENING COMPLETE")
        print(
            f"Results: {correct}/{len(results)} correct"
        )
        print(f"Telegram:  {'✅' if tg_ok else '❌'}")
        print(f"Facebook:  {'✅' if fb_ok else '❌'}")
        print("="*50)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
