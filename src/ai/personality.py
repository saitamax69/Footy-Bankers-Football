import os
import json
import random
from datetime import datetime
import pytz
from groq import Groq


VOICE_SYSTEM = """
You write social media content for Footy Bankers Football.

The voice is a passionate, knowledgeable football fan.
British. Mid-twenties to thirties.
Watches almost every game.
Has been following football his whole life.
Honest. Opinionated. Data-aware.

RULES:
- Write like texting a mate about football
- Short punchy sentences. Mix with longer ones.
- Use contractions always (cannot, I am, we are)
- Never show raw numbers as stats
  Wrong: "win rate 78%"
  Right: "eight wins from their last ten"
- Express actual opinions not just data
- Admit uncertainty when confidence is under 65
- Reference yesterday's results naturally
- Vary your language every day
- Never sound like a press release
- Never sound like a robot

PHRASES TO USE NATURALLY:
"cannot see past this one"
"this writes itself"
"been saying this for weeks"
"backing this all day"
"something feels off about this game"
"trust the process"
"this one really jumps out"
"not fully sold but the value is there"
"form says one thing, gut says another"
"both sides have been leaking goals"
"solid as a rock at home"
"""


class PersonalityEngine:
    """
    Adds human voice to all content.
    References yesterday.
    Varies style daily.
    """

    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY", "")
        )
        self.model = "llama-3.1-70b-versatile"
        self.tz = pytz.timezone("Europe/London")

    def write_opening(
        self,
        accuracy_data: dict,
        day_name: str,
    ) -> str:
        """
        Write the human opening paragraph
        for today's predictions post.
        """
        yesterday = accuracy_data.get(
            "yesterday", {}
        )
        streak = accuracy_data.get("streak", 0)
        overall = accuracy_data.get("overall", "")

        prompt = f"""
{VOICE_SYSTEM}

Write the opening paragraph for today's 
football predictions post.

Context:
- Today is {day_name}
- Yesterday: {yesterday.get('correct', '?')} correct 
  from {yesterday.get('total', '?')} picks
- Current streak: {streak} correct in a row
- Overall accuracy: {overall}

Write 2-4 short sentences max.
Reference yesterday naturally.
Build excitement for today.
Sound completely human.
No emojis in this section.
No markdown.
Just natural text.

Example style:
"Right. Tuesday. Four from five yesterday 
which I am happy with. The Chelsea pick 
let me down but City came in exactly 
as expected. Fresh day today. Here is 
what I am looking at."
"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"Opening write failed: {e}")
            return self._fallback_opening(
                yesterday, streak, day_name
            )

    def write_pick_analysis(
        self, prediction: dict
    ) -> str:
        """
        Convert raw AI prediction into
        human-voice analysis text.
        """
        m = prediction.get("match_data", {})
        home = m.get("home_team", "Home")
        away = m.get("away_team", "Away")
        pick = prediction.get("pick_short", "")
        conf = prediction.get("confidence", 0)
        reasons = prediction.get("reasoning", [])
        risk = prediction.get("risk", "")
        hf = m.get("home_form", {})
        af = m.get("away_form", {})

        prompt = f"""
{VOICE_SYSTEM}

Write a short human-voice analysis 
for this football prediction.

Match: {home} vs {away}
Our pick: {pick}
Confidence: {conf}%
AI reasons: {reasons}
Main risk: {risk}
Home form: {hf.get('form_string', '?')}
Away form: {af.get('form_string', '?')}
Home win rate: {hf.get('win_rate', '?')}%
Away win rate: {af.get('win_rate', '?')}%

Write 2-3 sentences maximum.
Sound like a real football fan.
Mention the most important factor.
If confidence under 65 admit some uncertainty.
No emojis. No markdown. Pure text.
"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=120,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return self._fallback_analysis(
                reasons, risk
            )

    def write_media_post(
        self,
        post_type: str,
        context: dict,
        used_topics: list = None,
    ) -> str:
        """
        Generate media-company style post.
        post_type: data_tuesday, hot_take,
                   throwback, weekend_preview, etc.
        """
        avoid_topics = used_topics or []

        prompt = f"""
{VOICE_SYSTEM}

Write a {post_type} post for Footy Bankers Football.

Context: {json.dumps(context)}
Do not repeat these topics: {avoid_topics}

Post types:
- data_tuesday: Share one surprising football stat
- hot_take: Bold opinion backed by logic
- throwback: Historical football moment
- weekend_preview: Hype for weekend fixtures
- monday_verdict: Honest weekend review
- player_spotlight: Unsung hero feature

Write the full post.
Sound human and genuine.
Mix short and long sentences.
End with something that invites engagement.
No fake positivity.
Max 200 words.
"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"Media post failed: {e}")
            return ""

    def _fallback_opening(
        self, yesterday: dict, streak: int, day: str
    ) -> str:
        correct = yesterday.get("correct", 0)
        total = yesterday.get("total", 0)
        options = [
            f"Right. {day}. Let's get into it.",
            f"{day} picks are in. Here's what I like today.",
            f"Morning. {correct} from {total} yesterday. "
            f"Moving on. Here's today.",
        ]
        return random.choice(options)

    def _fallback_analysis(
        self, reasons: list, risk: str
    ) -> str:
        if reasons:
            return reasons[0]
        return "The data points clearly in one direction here."
