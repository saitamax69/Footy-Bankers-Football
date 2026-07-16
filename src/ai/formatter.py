from datetime import datetime
import pytz
from config import (
    BRAND_NAME, BRAND_SHORT, DISCLAIMER,
    TELEGRAM_HANDLE, LEAGUES, FACEBOOK_PICKS,
)


class PostFormatter:
    """
    Formats predictions into
    Telegram and Facebook posts.
    Uses human-voice analysis.
    """

    def __init__(self, personality_engine):
        self.pe = personality_engine
        self.tz = pytz.timezone("Europe/London")

    def telegram_morning(
        self,
        predictions: list,
        accuracy: dict,
    ) -> str:
        """Full Telegram prediction post."""
        now = datetime.now(self.tz)
        day = now.strftime("%A")
        date = now.strftime("%d %B %Y")
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

        # Human opening
        opening = self.pe.write_opening(accuracy, day)

        msg = f"⚽ *FOOTY BANKERS FOOTBALL*\n"
        msg += f"📅 {day} {date} │ {time_str} UK\n\n"
        msg += f"_{self._escape(opening)}_\n\n"

        # Stats bar
        streak = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "Building...")
        week = accuracy.get("week_record", "")

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 Picks today: *{len(predictions)}*"

        if streak > 0:
            msg += f" │ 🔥 Streak: *{streak}*"
        if overall:
            msg += f" │ 📈 *{overall}*"

        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Banker picks
        if bankers:
            msg += "🔒 *THE BANKER PICKS*\n\n"
            for i, p in enumerate(bankers, 1):
                msg += self._format_pick_tg(p, i, True)

        # Strong picks
        if strong:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "💪 *STRONG PICKS*\n\n"
            start = len(bankers) + 1
            for i, p in enumerate(strong, start):
                msg += self._format_pick_tg(p, i, True)

        # Value picks
        if value:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "🎲 *VALUE PICKS*\n\n"
            start = len(bankers) + len(strong) + 1
            for i, p in enumerate(value, start):
                msg += self._format_pick_tg(
                    p, i, False
                )

        # Avoid list
        if avoids:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "⛔ *AVOIDING TODAY*\n\n"
            for p in avoids:
                m = p.get("match_data", {})
                h = m.get("home_team", "?")
                a = m.get("away_team", "?")
                risk = p.get("risk", "Too unpredictable")
                safe = self._escape(f"{h} vs {a}")
                safe_r = self._escape(risk)
                msg += f"❌ *{safe}*\n"
                msg += f"   {safe_r}\n\n"

        # Weekly accuracy
        weekly = accuracy.get("weekly_breakdown", [])
        if weekly:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "📈 *RECENT RECORD*\n\n"
            for d in weekly[-5:]:
                pct = d.get("pct", 0)
                em = "🔥" if pct >= 75 else (
                    "✅" if pct >= 55 else "⚠️"
                )
                c = d.get("correct", 0)
                t = d.get("total", 0)
                dy = self._escape(d.get("day", ""))
                msg += f"{em} {dy}: {c}/{t}\n"

        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"_{DISCLAIMER}_\n"
        msg += f"*{BRAND_NAME}* ⚽🔒"

        return msg

    def facebook_morning(
        self,
        predictions: list,
        accuracy: dict,
    ) -> str:
        """Clean Facebook top 5 post."""
        now = datetime.now(self.tz)
        day = now.strftime("%A")
        date = now.strftime("%d %B %Y")

        top5 = predictions[:FACEBOOK_PICKS]

        streak = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "")

        lines = []

        if overall:
            if streak > 0:
                lines.append(
                    f"{streak} correct in a row. "
                    f"Here are today's top five."
                )
            else:
                lines.append(
                    "Today's top five picks."
                )
        else:
            lines.append(
                "Building our track record. "
                "Here are today's picks."
            )

        msg = f"⚽ Footy Bankers Football\n"
        msg += f"📅 {day} {date}\n\n"
        msg += lines[0] + "\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"
        ]
        tier_icons = {
            "BANKER": "🔒",
            "STRONG": "💪",
            "VALUE":  "🎲",
        }

        for i, pred in enumerate(top5):
            m = pred.get("match_data", {})
            home = m.get("home_team", "Home")
            away = m.get("away_team", "Away")
            comp = m.get("competition_name", "Football")
            kick = m.get("kickoff_uk", "TBC")
            pick = pred.get("pick_short", "")
            conf = pred.get("confidence", 0)
            tier = pred.get("tier", "VALUE")
            icon = tier_icons.get(tier, "⚽")
            flag = self._flag(
                m.get("competition_code", "")
            )

            msg += f"{emojis[i]} {icon} {pick}\n"
            msg += f"   {flag} {comp}\n"
            msg += f"   {home} vs {away}\n"
            msg += f"   ⏰ {kick} │ 📊 {conf}%\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        if overall:
            msg += f"📈 Overall accuracy: {overall}\n"

        if streak > 3:
            msg += f"🔥 Current streak: {streak} correct\n"

        msg += (
            f"\n💬 Full breakdown + all picks:\n"
            f"👉 Telegram: t.me/FootyBankersFootball\n\n"
        )
        msg += DISCLAIMER

        return msg

    def telegram_results(
        self,
        results: list,
        accuracy: dict,
    ) -> str:
        """Evening results post for Telegram."""
        now = datetime.now(self.tz)
        date = now.strftime("%A %d %B %Y")

        correct = [r for r in results if r.get("correct")]
        n = len(correct)
        total = len(results)
        pct = round(n / total * 100, 1) if total else 0

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

        msg = f"📊 *TODAY'S RESULTS*\n"
        msg += f"📅 {self._escape(date)}\n\n"
        msg += f"*{verdict}*\n"
        msg += f"{n}/{total} correct "
        msg += f"\\({pct}%\\)\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for r in results:
            m = r.get("match_data", {})
            home = self._escape(
                m.get("home_team", "Home")
            )
            away = self._escape(
                m.get("away_team", "Away")
            )
            pick = self._escape(
                r.get("pick_short", r.get("pick", ""))
            )
            score = self._escape(
                r.get("actual_score", "?-?")
            )
            ok = r.get("correct", False)
            em = "✅" if ok else "❌"

            msg += f"{em} *{home} vs {away}*\n"
            msg += f"   Pick: {pick}\n"
            msg += f"   Result: {score}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        streak = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "")

        if overall:
            msg += f"📈 Overall accuracy: *{overall}*\n"
        if streak > 0:
            msg += (
                f"🔥 Current streak: "
                f"*{streak} correct*\n"
            )

        msg += "\nSee you tomorrow 💪⚽\n\n"
        msg += f"_{DISCLAIMER}_\n"
        msg += f"*{BRAND_NAME}* ⚽🔒"

        return msg

    def facebook_results(
        self,
        results: list,
        accuracy: dict,
    ) -> str:
        """Evening results post for Facebook."""
        now = datetime.now(self.tz)
        date = now.strftime("%A %d %B %Y")

        correct = [r for r in results if r.get("correct")]
        n = len(correct)
        total = len(results)
        pct = round(n / total * 100, 1) if total else 0

        msg = f"📊 Footy Bankers Football | Results\n"
        msg += f"📅 {date}\n\n"
        msg += f"Today: {n}/{total} correct ({pct}%)\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        for r in results[:5]:
            m = r.get("match_data", {})
            home = m.get("home_team", "Home")
            away = m.get("away_team", "Away")
            pick = r.get("pick_short", "")
            score = r.get("actual_score", "?-?")
            ok = r.get("correct", False)
            em = "✅" if ok else "❌"

            msg += f"{em} {home} vs {away}\n"
            msg += f"   Pick: {pick} │ Score: {score}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        overall = accuracy.get("overall", "")
        streak = accuracy.get("streak", 0)

        if overall:
            msg += f"📈 Overall accuracy: {overall}\n"
        if streak > 3:
            msg += f"🔥 Streak: {streak} correct\n"

        msg += (
            f"\nFull analysis on Telegram:\n"
            f"t.me/FootyBankersFootball\n\n"
        )
        msg += DISCLAIMER

        return msg

    def no_fixtures_post(self) -> tuple:
        """Posts for days with no fixtures."""
        tg = (
            "⚽ *FOOTY BANKERS FOOTBALL*\n\n"
            "_No major fixtures today\\._\n\n"
            "We will be back tomorrow with the "
            "full breakdown\\. In the meantime "
            "check out the form tables and stats "
            "from the week\\.\n\n"
            f"_{DISCLAIMER}_\n"
            f"*{BRAND_NAME}* ⚽🔒"
        )
        fb = (
            "⚽ Footy Bankers Football\n\n"
            "No major fixtures today.\n\n"
            "Back tomorrow with the full picks.\n\n"
            f"Telegram for all analysis:\n"
            f"t.me/FootyBankersFootball\n\n"
            f"{DISCLAIMER}"
        )
        return tg, fb

    def _format_pick_tg(
        self, pred: dict, num: int, full: bool
    ) -> str:
        """Format one pick for Telegram."""
        m = pred.get("match_data", {})
        home = m.get("home_team", "Home")
        away = m.get("away_team", "Away")
        comp = m.get("competition_name", "Football")
        kick = m.get("kickoff_uk", "TBC")
        pick = pred.get("pick_short", "")
        conf = pred.get("confidence", 0)
        score = pred.get("predicted_score", "")
        analysis = pred.get("human_analysis", "")
        risk = pred.get("risk", "")
        flag = self._flag(
            m.get("competition_code", "")
        )

        safe_home = self._escape(home)
        safe_away = self._escape(away)
        safe_comp = self._escape(comp)
        safe_pick = self._escape(pick)
        safe_kick = self._escape(kick)

        text = (
            f"{flag} {safe_comp} │ {safe_kick}\n"
            f"*{safe_home} vs {safe_away}*\n"
            f"✅ *{safe_pick}*\n"
            f"📊 Confidence: {conf}%\n"
        )

        if score:
            text += f"🎯 Score: {self._escape(score)}\n"

        if full and analysis:
            safe_a = self._escape(analysis)
            text += f"\n_{safe_a}_\n"

        if risk:
            safe_r = self._escape(risk)
            text += f"⚠️ Risk: _{safe_r}_\n"

        text += "\n"
        return text

    def _escape(self, text: str) -> str:
        """Escape MarkdownV2 special characters."""
        if not text:
            return ""
        chars = [
            "_", "*", "[", "]", "(", ")", "~",
            "`", ">", "#", "+", "-", "=", "|",
            "{", "}", ".", "!",
        ]
        for c in chars:
            text = text.replace(c, f"\\{c}")
        return text

    def _flag(self, code: str) -> str:
        flags = {
            "PL":   "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "PD":   "🇪🇸",
            "BL1":  "🇩🇪",
            "SA":   "🇮🇹",
            "FL1":  "🇫🇷",
            "CL":   "🏆",
            "EL":   "🟠",
            "ELC":  "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "PPL":  "🇵🇹",
            "DED":  "🇳🇱",
            "BSA":  "🇧🇷",
            "WC":   "🌍",
            "EC":   "🇪🇺",
            "FAC":  "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "MLS":  "🇺🇸",
        }
        return flags.get(code, "⚽")
