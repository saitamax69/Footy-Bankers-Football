from datetime import datetime
import pytz
from config import (
    BRAND_NAME,
    DISCLAIMER,
    TELEGRAM_LINK,
    AFFILIATE_LINK,
    FACEBOOK_PICKS,
)


class PostFormatter:
    """
    Formats predictions into posts.

    TELEGRAM:
    → Full predictions with affiliate link
    → 10-20 picks with full analysis
    → Stake link in every post (safe on Telegram)

    FACEBOOK:
    → Top 5 picks only
    → NO direct Stake/betting link (protects page)
    → Telegram link to drive traffic
    → Looks like media company not spam
    """

    def __init__(self, personality_engine):
        self.pe = personality_engine
        self.tz = pytz.timezone("Europe/London")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TELEGRAM POSTS
    # Full predictions + affiliate link
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def telegram_morning(
        self,
        predictions: list,
        accuracy: dict,
    ) -> str:
        """Full Telegram prediction post."""
        now      = datetime.now(self.tz)
        day      = now.strftime("%A")
        date     = now.strftime("%d %B %Y")
        time_str = now.strftime("%H:%M")

        bankers = [
            p for p in predictions
            if p.get("tier") == "BANKER"
        ]
        strong = [
            p for p in predictions
            if p.get("tier") == "STRONG"
        ]
        value = [
            p for p in predictions
            if p.get("tier") == "VALUE"
        ]
        avoids = [
            p for p in predictions
            if p.get("avoid")
        ]

        # Human opening paragraph
        opening = self.pe.write_opening(accuracy, day)

        msg  = "⚽ *FOOTY BANKERS FOOTBALL*\n"
        msg += (
            f"📅 {day} {date} │ {time_str} UK\n\n"
        )
        msg += f"_{self._e(opening)}_\n\n"

        # Stats bar
        streak  = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "")
        total   = len(predictions)

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 Picks today: *{total}*"

        if streak > 0:
            msg += f" │ 🔥 Streak: *{streak}*"

        if overall and overall != "Building...":
            msg += f" │ 📈 *{self._e(overall)}*"
        else:
            msg += " │ 📈 Building\\.\\.\\."

        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Banker picks section
        if bankers:
            msg += "🔒 *BANKER PICKS*\n\n"
            for i, p in enumerate(bankers, 1):
                msg += self._format_pick_tg(p, i)

        # Strong picks section
        if strong:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "💪 *STRONG PICKS*\n\n"
            start = len(bankers) + 1
            for i, p in enumerate(strong, start):
                msg += self._format_pick_tg(p, i)

        # Value picks section
        if value:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "🎲 *VALUE PICKS*\n\n"
            start = len(bankers) + len(strong) + 1
            for i, p in enumerate(value, start):
                msg += self._format_pick_tg(p, i)

        # Avoid section
        if avoids:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "⛔ *AVOID TODAY*\n\n"
            for p in avoids:
                m   = p.get("match_data", {})
                h   = self._e(m.get("home_team", ""))
                a   = self._e(m.get("away_team", ""))
                r   = self._e(
                    p.get("risk", "Too unpredictable")
                )
                msg += f"❌ *{h} vs {a}*\n"
                msg += f"_{r}_\n\n"

        # Affiliate link - safe on Telegram
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += (
            f"🎰 *Place your bets:*\n"
            f"[stake\\.com/\\?c\\=stakesoccer24]"
            f"({AFFILIATE_LINK})\n\n"
        )

        msg += f"_{self._e(DISCLAIMER)}_\n"
        msg += f"*{self._e(BRAND_NAME)}* ⚽🔒"

        return msg

    def telegram_results(
        self,
        results: list,
        accuracy: dict,
    ) -> str:
        """Evening results post for Telegram."""
        now  = datetime.now(self.tz)
        date = now.strftime("%A %d %B %Y")

        correct = [
            r for r in results if r.get("correct")
        ]
        n     = len(correct)
        total = len(results)
        pct   = (
            round(n / total * 100, 1)
            if total else 0
        )

        if pct >= 80:
            verdict = "BRILLIANT DAY 🔥"
        elif pct >= 65:
            verdict = "GOOD DAY ✅"
        elif pct >= 50:
            verdict = "DECENT DAY 👍"
        elif pct >= 35:
            verdict = "TOUGH DAY ⚠️"
        else:
            verdict = "BAD DAY ❌"

        msg  = "📊 *TODAY'S RESULTS*\n"
        msg += f"📅 {self._e(date)}\n\n"
        msg += f"*{self._e(verdict)}*\n"
        msg += (
            f"{n}/{total} correct "
            f"\\({pct}%\\)\n\n"
        )
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for r in results:
            m     = r.get("match_data", {})
            home  = self._e(m.get("home_team", ""))
            away  = self._e(m.get("away_team", ""))
            pick  = self._e(
                r.get("pick_short", r.get("pick", ""))
            )
            score = self._e(
                r.get("actual_score", "?\\-?")
            )
            ok    = r.get("correct", False)
            em    = "✅" if ok else "❌"

            msg += f"{em} *{home} vs {away}*\n"
            msg += f"   Pick: {pick}\n"
            msg += f"   Result: {score}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        streak  = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "")

        if overall and overall != "Building...":
            msg += (
                f"📈 Overall: "
                f"*{self._e(overall)}*\n"
            )
        if streak > 0:
            msg += (
                f"🔥 Streak: "
                f"*{streak} correct*\n"
            )

        msg += "\nSee you tomorrow 💪⚽\n\n"

        # Affiliate link in results - safe on Telegram
        msg += (
            f"🎰 [Place your bets]"
            f"({AFFILIATE_LINK})\n\n"
        )

        msg += f"_{self._e(DISCLAIMER)}_\n"
        msg += f"*{self._e(BRAND_NAME)}* ⚽🔒"

        return msg

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FACEBOOK POSTS
    # NO direct betting links - protects page
    # Drive traffic to Telegram instead
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def facebook_morning(
        self,
        predictions: list,
        accuracy: dict,
    ) -> str:
        """
        Clean Facebook morning post.

        IMPORTANT: No direct Stake/betting link here.
        Facebook will shadowban and eventually
        delete the page if we post betting links.

        Strategy: Drive people to Telegram.
        Telegram is where the Stake link lives.
        """
        now  = datetime.now(self.tz)
        day  = now.strftime("%A")
        date = now.strftime("%d %B %Y")

        top5    = predictions[:FACEBOOK_PICKS]
        streak  = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "")
        total   = len(predictions)

        msg = "⚽ Footy Bankers Football\n"
        msg += f"📅 {day} {date}\n\n"

        # Opening hook
        if streak > 5:
            msg += (
                f"🔥 {streak} correct in a row. "
                f"Today's picks 👇\n\n"
            )
        elif overall and overall != "Building...":
            msg += (
                f"📈 {overall} accuracy. "
                f"Here are today's top picks 🔒\n\n"
            )
        else:
            msg += "Today's top picks are in 🔒\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        emojis     = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣"]
        tier_icons = {
            "BANKER": "🔒",
            "STRONG": "💪",
            "VALUE":  "🎲",
        }

        for i, pred in enumerate(top5):
            m        = pred.get("match_data", {})
            home     = m.get("home_team", "Home")
            away     = m.get("away_team", "Away")
            comp     = m.get("competition_name", "")
            kick     = m.get("kickoff_uk", "TBC")
            pick     = pred.get("pick_short", "")
            conf     = pred.get("confidence", 0)
            tier     = pred.get("tier", "VALUE")
            icon     = tier_icons.get(tier, "⚽")
            is_major = pred.get("is_major", False)

            # World Cup badge
            major_tag = " 🌍 MAJOR" if is_major else ""

            msg += f"{emojis[i]} {icon} {pick}{major_tag}\n"
            msg += f"   {comp}\n"
            msg += f"   {home} vs {away}\n"
            msg += f"   ⏰ {kick} │ 📊 {conf}%\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        # Show accuracy if we have it
        if overall and overall != "Building...":
            msg += f"📈 Overall accuracy: {overall}\n"

        if streak > 3:
            msg += f"🔥 Current streak: {streak} correct\n"

        # Total picks teaser
        if total > FACEBOOK_PICKS:
            remaining = total - FACEBOOK_PICKS
            msg += (
                f"\n📊 Plus {remaining} more picks "
                f"on our Telegram 👇\n"
            )

        # Strong CTA to Telegram (where Stake link lives)
        msg += (
            f"\n💬 Full breakdown + all picks:\n"
            f"👉 {TELEGRAM_LINK}\n\n"
        )

        # Safe disclaimer only - no betting links
        msg += DISCLAIMER

        return msg

    def facebook_results(
        self,
        results: list,
        accuracy: dict,
    ) -> str:
        """
        Facebook results post.
        No direct betting link.
        Drive to Telegram for full analysis.
        """
        now  = datetime.now(self.tz)
        date = now.strftime("%A %d %B %Y")

        correct = [
            r for r in results if r.get("correct")
        ]
        n     = len(correct)
        total = len(results)
        pct   = (
            round(n / total * 100, 1)
            if total else 0
        )

        # Result verdict
        if pct >= 80:
            verdict = "Brilliant day 🔥"
            emoji   = "🔥"
        elif pct >= 65:
            verdict = "Good day"
            emoji   = "✅"
        elif pct >= 50:
            verdict = "Decent day"
            emoji   = "👍"
        elif pct >= 35:
            verdict = "Tough day"
            emoji   = "⚠️"
        else:
            verdict = "Difficult day"
            emoji   = "❌"

        msg  = "📊 Footy Bankers Football | Results\n"
        msg += f"📅 {date}\n\n"
        msg += f"{emoji} {verdict}: {n}/{total} correct ({pct}%)\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        # Show up to 5 results
        for r in results[:5]:
            m     = r.get("match_data", {})
            home  = m.get("home_team", "")
            away  = m.get("away_team", "")
            pick  = r.get("pick_short", "")
            score = r.get("actual_score", "?-?")
            ok    = r.get("correct", False)
            em    = "✅" if ok else "❌"

            msg += f"{em} {home} vs {away}\n"
            msg += f"   {pick} │ Score: {score}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        # Accuracy stats
        overall = accuracy.get("overall", "")
        streak  = accuracy.get("streak", 0)

        if overall and overall != "Building...":
            msg += f"📈 Overall accuracy: {overall}\n"

        if streak > 3:
            msg += f"🔥 Streak: {streak} correct\n"

        # Drive to Telegram
        msg += (
            f"\n📊 Full results + tomorrow's picks:\n"
            f"👉 {TELEGRAM_LINK}\n\n"
        )

        # Safe disclaimer only
        msg += DISCLAIMER

        return msg

    def no_fixtures_post(self) -> tuple:
        """Posts for days with no fixtures."""

        # Telegram - can have affiliate link
        tg = (
            "⚽ *FOOTY BANKERS FOOTBALL*\n\n"
            "_No major fixtures today\\._\n\n"
            "We will be back tomorrow with "
            "the full breakdown\\! 🔒\n\n"
            f"🎰 [Place your bets today]"
            f"({AFFILIATE_LINK})\n\n"
            f"_{self._e(DISCLAIMER)}_\n"
            f"*{self._e(BRAND_NAME)}* ⚽🔒"
        )

        # Facebook - no direct betting link
        fb = (
            f"⚽ Footy Bankers Football\n\n"
            f"No major fixtures today.\n\n"
            f"Back tomorrow with full picks 🔒\n\n"
            f"In the meantime check out our\n"
            f"full analysis on Telegram:\n"
            f"👉 {TELEGRAM_LINK}\n\n"
            f"{DISCLAIMER}"
        )

        return tg, fb

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HELPERS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _format_pick_tg(
        self, pred: dict, num: int
    ) -> str:
        """Format single pick for Telegram."""
        m        = pred.get("match_data", {})
        home     = m.get("home_team", "Home")
        away     = m.get("away_team", "Away")
        comp     = m.get("competition_name", "")
        kick     = m.get("kickoff_uk", "TBC")
        pick     = pred.get("pick_short", "")
        conf     = pred.get("confidence", 0)
        score    = pred.get("predicted_score", "")
        analysis = pred.get("human_analysis", "")
        risk     = pred.get("risk", "")
        is_major = pred.get("is_major", False)
        flag     = self._flag(
            m.get("competition_code", "")
        )

        # Major tournament badge
        major_badge = " 🌍" if is_major else ""

        text  = (
            f"{flag} {self._e(comp)}"
            f"{major_badge} │ "
            f"{self._e(kick)}\n"
        )
        text += (
            f"*{self._e(home)} vs "
            f"{self._e(away)}*\n"
        )
        text += f"✅ *{self._e(pick)}*\n"
        text += f"📊 Confidence: {conf}%\n"

        if score:
            safe_score = score.replace("-", "\\-")
            text += f"🎯 Score: {safe_score}\n"

        if analysis:
            text += f"\n_{self._e(analysis)}_\n"

        if risk:
            text += f"⚠️ _{self._e(risk)}_\n"

        text += "\n"
        return text

    def _e(self, text: str) -> str:
        """Escape MarkdownV2 special characters."""
        if not text:
            return ""
        text = str(text)
        special = [
            "_", "*", "[", "]", "(", ")", "~",
            "`", ">", "#", "+", "-", "=", "|",
            "{", "}", ".", "!",
        ]
        for c in special:
            text = text.replace(c, f"\\{c}")
        return text

    def _flag(self, code: str) -> str:
        """Competition flag emoji."""
        flags = {
            "PL":  "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "PD":  "🇪🇸",
            "BL1": "🇩🇪",
            "SA":  "🇮🇹",
            "FL1": "🇫🇷",
            "CL":  "🏆",
            "WC":  "🌍",
            "EC":  "🇪🇺",
            "EL":  "🟠",
            "ELC": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "PPL": "🇵🇹",
            "DED": "🇳🇱",
            "BSA": "🇧🇷",
            "MLS": "🇺🇸",
            "FAC": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "COL": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        }
        return flags.get(code, "⚽")
