from datetime import datetime
import pytz
from config import (
    BRAND_NAME,
    DISCLAIMER,
    FACEBOOK_PICKS,
)


class PostFormatter:
    """
    Formats predictions into
    Telegram and Facebook posts.
    """

    def __init__(self, personality_engine):
        self.pe = personality_engine
        self.tz = pytz.timezone("Europe/London")

    def telegram_morning(
        self,
        predictions: list,
        accuracy: dict,
    ) -> str:
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

        opening = self.pe.write_opening(accuracy, day)
        streak  = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "Building...")
        weekly  = accuracy.get("weekly_breakdown", [])

        msg = (
            f"⚽ *FOOTY BANKERS FOOTBALL*\n"
            f"📅 {self._e(day)} {self._e(date)} "
            f"│ {self._e(time_str)} UK\n\n"
            f"_{self._e(opening)}_\n\n"
        )

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += (
            f"📊 Picks: *{len(predictions)}*"
        )
        if streak > 0:
            msg += f" │ 🔥 Streak: *{streak}*"
        if overall:
            msg += f" │ 📈 *{self._e(overall)}*"
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if bankers:
            msg += "🔒 *BANKER PICKS*\n\n"
            for i, p in enumerate(bankers, 1):
                msg += self._pick_tg(p, i, True)

        if strong:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "💪 *STRONG PICKS*\n\n"
            s = len(bankers) + 1
            for i, p in enumerate(strong, s):
                msg += self._pick_tg(p, i, True)

        if value:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "🎲 *VALUE PICKS*\n\n"
            s = len(bankers) + len(strong) + 1
            for i, p in enumerate(value, s):
                msg += self._pick_tg(p, i, False)

        if avoids:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "⛔ *AVOIDING TODAY*\n\n"
            for p in avoids:
                m = p.get("match_data", {})
                h = self._e(m.get("home_team", "?"))
                a = self._e(m.get("away_team", "?"))
                r = self._e(
                    p.get("risk", "Unpredictable")
                )
                msg += f"❌ *{h} vs {a}*\n"
                msg += f"   _{r}_\n\n"

        if weekly:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += "📈 *RECENT RECORD*\n\n"
            for d in weekly[-5:]:
                pct = d.get("pct", 0)
                em  = (
                    "🔥" if pct >= 75
                    else "✅" if pct >= 55
                    else "⚠️"
                )
                c  = d.get("correct", 0)
                t  = d.get("total", 0)
                dy = self._e(d.get("day", ""))
                msg += f"{em} {dy}: {c}/{t}\n"

        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"_{self._e(DISCLAIMER)}_\n"
        msg += f"*{self._e(BRAND_NAME)}* ⚽🔒"

        return msg

    def facebook_morning(
        self,
        predictions: list,
        accuracy: dict,
    ) -> str:
        now    = datetime.now(self.tz)
        day    = now.strftime("%A")
        date   = now.strftime("%d %B %Y")
        top5   = predictions[:FACEBOOK_PICKS]
        streak = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "")

        if streak > 3:
            intro = (
                f"{streak} correct in a row. "
                f"Here are today's top five."
            )
        elif overall:
            intro = "Today's top five picks."
        else:
            intro = (
                "Building our track record. "
                "Here are today's picks."
            )

        msg  = f"⚽ Footy Bankers Football\n"
        msg += f"📅 {day} {date}\n\n"
        msg += intro + "\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"
        ]
        icons  = {
            "BANKER": "🔒",
            "STRONG": "💪",
            "VALUE":  "🎲",
        }

        for i, pred in enumerate(top5):
            m    = pred.get("match_data", {})
            home = m.get("home_team", "Home")
            away = m.get("away_team", "Away")
            comp = m.get("competition_name", "Football")
            kick = m.get("kickoff_uk", "TBC")
            pick = pred.get("pick_short", "")
            conf = pred.get("confidence", 0)
            tier = pred.get("tier", "VALUE")
            icon = icons.get(tier, "⚽")
            flag = self._flag(
                m.get("competition_code", "")
            )

            msg += f"{emojis[i]} {icon} {pick}\n"
            msg += f"   {flag} {comp}\n"
            msg += f"   {home} vs {away}\n"
            msg += f"   ⏰ {kick} │ 📊 {conf}%\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        if overall:
            msg += f"📈 Accuracy: {overall}\n"
        if streak > 3:
            msg += f"🔥 Streak: {streak} correct\n"

        msg += (
            f"\n💬 Full breakdown + all picks:\n"
            f"👉 Telegram: t.me/FootyBankersFootball\n\n"
        )
        msg += DISCLAIMER

        return msg

    def telegram_results(
        self, results: list, accuracy: dict
    ) -> str:
        now  = datetime.now(self.tz)
        date = now.strftime("%A %d %B %Y")

        correct = [
            r for r in results if r.get("correct")
        ]
        n     = len(correct)
        total = len(results)
        pct   = round(
            n / total * 100, 1
        ) if total else 0

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

        msg  = f"📊 *TODAY'S RESULTS*\n"
        msg += f"📅 {self._e(date)}\n\n"
        msg += f"*{verdict}*\n"
        msg += (
            f"{n}/{total} correct "
            f"\\({pct}%\\)\n\n"
        )
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for r in results:
            m    = r.get("match_data", {})
            home = self._e(m.get("home_team", "Home"))
            away = self._e(m.get("away_team", "Away"))
            pick = self._e(
                r.get("pick_short", r.get("pick", ""))
            )
            score = self._e(
                r.get("actual_score", "?-?")
            )
            em = "✅" if r.get("correct") else "❌"

            msg += f"{em} *{home} vs {away}*\n"
            msg += f"   Pick: {pick}\n"
            msg += f"   Result: {score}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        streak  = accuracy.get("streak", 0)
        overall = accuracy.get("overall", "")

        if overall:
            msg += (
                f"📈 Overall: "
                f"*{self._e(overall)}*\n"
            )
        if streak > 0:
            msg += f"🔥 Streak: *{streak}*\n"

        msg += "\nSee you tomorrow 💪⚽\n\n"
        msg += f"_{self._e(DISCLAIMER)}_\n"
        msg += f"*{self._e(BRAND_NAME)}* ⚽🔒"

        return msg

    def facebook_results(
        self, results: list, accuracy: dict
    ) -> str:
        now  = datetime.now(self.tz)
        date = now.strftime("%A %d %B %Y")

        correct = [
            r for r in results if r.get("correct")
        ]
        n     = len(correct)
        total = len(results)
        pct   = round(
            n / total * 100, 1
        ) if total else 0

        msg  = f"📊 Footy Bankers Football | Results\n"
        msg += f"📅 {date}\n\n"
        msg += f"Today: {n}/{total} ({pct}%)\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        for r in results[:5]:
            m    = r.get("match_data", {})
            home = m.get("home_team", "Home")
            away = m.get("away_team", "Away")
            pick = r.get("pick_short", "")
            score = r.get("actual_score", "?-?")
            em   = "✅" if r.get("correct") else "❌"
            msg += f"{em} {home} vs {away}\n"
            msg += (
                f"   Pick: {pick} │ "
                f"Score: {score}\n\n"
            )

        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

        overall = accuracy.get("overall", "")
        streak  = accuracy.get("streak", 0)

        if overall:
            msg += f"📈 Accuracy: {overall}\n"
        if streak > 3:
            msg += f"🔥 Streak: {streak} correct\n"

        msg += (
            f"\nFull analysis on Telegram:\n"
            f"t.me/FootyBankersFootball\n\n"
        )
        msg += DISCLAIMER
        return msg

    def no_fixtures_post(self) -> tuple:
        tg = (
            "⚽ *FOOTY BANKERS FOOTBALL*\n\n"
            "_No major fixtures today\\._\n\n"
            "Back tomorrow with the full "
            "breakdown\\! 🔒\n\n"
            f"_{self._e(DISCLAIMER)}_\n"
            f"*{self._e(BRAND_NAME)}* ⚽🔒"
        )
        fb = (
            "⚽ Footy Bankers Football\n\n"
            "No major fixtures today.\n\n"
            "Back tomorrow with the full picks.\n\n"
            f"Telegram: t.me/FootyBankersFootball\n\n"
            f"{DISCLAIMER}"
        )
        return tg, fb

    def _pick_tg(
        self, pred: dict, num: int, full: bool
    ) -> str:
        m    = pred.get("match_data", {})
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
        hv = m.get("home_squad_value", {})
        av = m.get("away_squad_value", {})

        text = (
            f"{flag} {self._e(comp)} "
            f"│ {self._e(kick)}\n"
            f"*{self._e(home)} vs {self._e(away)}*\n"
            f"✅ *{self._e(pick)}*\n"
            f"📊 Confidence: {conf}%\n"
        )

        if score:
            text += f"🎯 Score: {self._e(score)}\n"

        if (
            hv.get("total_value_m")
            and av.get("total_value_m")
        ):
            text += (
                f"💰 Squad values: "
                f"£{hv.get('total_value_m')}M vs "
                f"£{av.get('total_value_m')}M\n"
            )

        if full and analysis:
            text += f"\n_{self._e(analysis)}_\n"

        if risk:
            text += (
                f"⚠️ Risk: _{self._e(risk)}_\n"
            )

        text += "\n"
        return text

    def _e(self, text: str) -> str:
        """Escape MarkdownV2 special chars."""
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

    def _flag(self, code: str) -> str:
        flags = {
            "PL":  "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "PD":  "🇪🇸",
            "BL1": "🇩🇪",
            "SA":  "🇮🇹",
            "FL1": "🇫🇷",
            "CL":  "🏆",
            "EL":  "🟠",
            "ELC": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "PPL": "🇵🇹",
            "DED": "🇳🇱",
            "BSA": "🇧🇷",
            "WC":  "🌍",
            "EC":  "🇪🇺",
            "MLS": "🇺🇸",
        }
        return flags.get(code, "⚽")
