import os
import json
import random
from datetime import datetime
import pytz
from groq import Groq
from config import (
    GROQ_PRIMARY_MODEL,
    GROQ_FALLBACK_MODEL,
    GROQ_FAST_MODEL,
)


VOICE_SYSTEM = """
You write social media content for Footy Bankers Football.

The voice is a passionate, knowledgeable football fan.
British. Mid-twenties to thirties.
Watches almost every game.
Honest. Opinionated. Data-aware.

RULES:
- Write like texting a mate about football
- Short punchy sentences mixed with longer ones
- Use contractions always
- Never show raw stats as numbers
  Wrong: "win rate 78%"
  Right: "eight wins from their last ten"
- Express actual opinions not just data
- Admit uncertainty when confidence under 65
- Reference yesterday naturally
- Never sound like a press release or robot

PHRASES TO USE:
"cannot see past this one"
"this writes itself"
"backing this all day"
"something feels off"
"trust the process"
"not fully sold but the value is there"
"both sides leaking goals"
"solid as a rock at home"
"this has goals written all over it"
"""


class PersonalityEngine:
    """
    Adds human voice to all content.
    Tries all available Groq models.
    Falls back gracefully.
    """

    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY", "")
        )
        self.models = [
            GROQ_PRIMARY_MODEL,
            GROQ_FALLBACK_MODEL,
            GROQ_FAST_MODEL,
        ]
        self.tz = pytz.timezone("Europe/London")

    def _call(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.8,
    ) -> str:
        for model in self.models:
            try:
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role":    "user",
                            "content": prompt,
                        }
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return (
                    resp.choices[0].message.content.strip()
                )
            except Exception as e:
                err = str(e)
                if (
                    "decommissioned" in err
                    or "not_found" in err
                    or "does not exist" in err
                ):
                    continue
                print(f"Personality error: {e}")
                continue
        return ""

    def write_opening(
        self,
        accuracy_data: dict,
        day_name: str,
    ) -> str:
        yesterday = accuracy_data.get("yesterday", {})
        streak    = accuracy_data.get("streak", 0)
        overall   = accuracy_data.get("overall", "")

        prompt = f"""
{VOICE_SYSTEM}

Write the opening for today's football predictions.

Context:
- Today is {day_name}
- Yesterday: {yesterday.get("correct", "?")} correct
  from {yesterday.get("total", "?")} picks
- Streak: {streak} correct in a row
- Overall accuracy: {overall}

2-4 short sentences.
Reference yesterday naturally.
Sound completely human.
No emojis. No markdown. Plain text only.
"""
        result = self._call(
            prompt, max_tokens=150, temperature=0.8
        )
        return result or self._fallback_opening(
            yesterday, streak, day_name
        )

    def write_pick_analysis(
        self, prediction: dict
    ) -> str:
        m       = prediction.get("match_data", {})
        home    = m.get("home_team", "Home")
        away    = m.get("away_team", "Away")
        pick    = prediction.get("pick_short", "")
        conf    = prediction.get("confidence", 0)
        reasons = prediction.get("reasoning", [])
        risk    = prediction.get("risk", "")
        hf      = m.get("home_form", {})
        af      = m.get("away_form", {})
        hv      = m.get("home_squad_value", {})
        av      = m.get("away_squad_value", {})

        value_context = ""
        if hv.get("total_value_m"):
            value_context += (
                f" Home squad worth "
                f"£{hv.get('total_value_m')}M."
            )
        if av.get("total_value_m"):
            value_context += (
                f" Away squad worth "
                f"£{av.get('total_value_m')}M."
            )

        prompt = f"""
{VOICE_SYSTEM}

Write a short human-voice analysis for this pick.

Match: {home} vs {away}
Pick: {pick}
Confidence: {conf}%
Reasons: {reasons}
Risk: {risk}
Home form: {hf.get("form_string", "?")}
Away form: {af.get("form_string", "?")}
{value_context}

2-3 sentences maximum.
Sound like a real football fan.
If confidence under 65 admit uncertainty.
No emojis. No markdown. Plain text.
"""
        result = self._call(
            prompt, max_tokens=120, temperature=0.7
        )
        return result or self._fallback_analysis(
            reasons, risk
        )

    def write_media_post(
        self,
        post_type: str,
        context: dict,
        used_topics: list = None,
    ) -> str:
        avoid = used_topics or []

        prompt = f"""
{VOICE_SYSTEM}

Write a {post_type} post for Footy Bankers Football.

Context: {json.dumps(context)}
Do not repeat these topics: {avoid}

Types guide:
- data_tuesday: One surprising football stat
- hot_take: Bold opinion backed by logic
- throwback: Classic football moment story
- weekend_preview: Hype for weekend fixtures
- monday_verdict: Honest weekend review
- player_spotlight: Unsung hero feature

Full post. Human and genuine.
Max 200 words. End with engagement hook.
"""
        return self._call(
            prompt, max_tokens=350, temperature=0.9
        )

    def write_results_reaction(
        self,
        correct: int,
        total: int,
        best_pick: str = "",
        worst_pick: str = "",
    ) -> str:
        pct = round(
            correct / total * 100, 1
        ) if total else 0

        if pct >= 80:
            mood = "great day"
        elif pct >= 60:
            mood = "decent day"
        elif pct >= 40:
            mood = "mixed day"
        else:
            mood = "tough day - completely honest"

        prompt = f"""
{VOICE_SYSTEM}

Write a results reaction.
Today: {correct} from {total} ({pct}%)
Mood: {mood}
Best pick: {best_pick}
Worst pick: {worst_pick}

2-3 sentences. Completely honest.
No emojis. No markdown. Plain text.
"""
        return self._call(
            prompt, max_tokens=100, temperature=0.7
        ) or self._fallback_results(correct, total, pct)

    def _fallback_opening(
        self, yesterday, streak, day
    ) -> str:
        c = yesterday.get("correct", 0)
        t = yesterday.get("total", 0)
        options = [
            f"Right. {day}. Let us get into it.",
            (
                f"{c} from {t} yesterday. "
                f"Moving on. Here is today."
            ),
            f"{day} picks are in.",
        ]
        if streak >= 5:
            options.append(
                f"{streak} in a row. Let us keep going."
            )
        return random.choice(options)

    def _fallback_analysis(self, reasons, risk) -> str:
        if reasons:
            return (
                f"{reasons[0]}. "
                f"Data points in one direction."
            )
        return "Numbers back this up. Confident."

    def _fallback_results(
        self, correct, total, pct
    ) -> str:
        if pct >= 70:
            return f"{correct}/{total} today. Happy with that."
        if pct >= 50:
            return f"{correct}/{total}. Could be better. Moving on."
        return f"Tough day. {correct}/{total}. Back tomorrow."
