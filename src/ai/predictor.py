import os
import json
import time
from groq import Groq
from config import (
    BANKER_MIN,
    STRONG_MIN,
    VALUE_MIN,
    MIN_CONFIDENCE,
    GROQ_PRIMARY_MODEL,
    GROQ_FALLBACK_MODEL,
    GROQ_FAST_MODEL,
)


SYSTEM_PROMPT = """
You are an expert football analyst with 20 years
of experience covering all global competitions.

Your knowledge includes:
- FIFA World Cup history and current tournament
- UEFA Champions League and Europa League
- All top European leagues
- South American, African, Asian football
- Team strengths, weaknesses, current form
- Player situations and tactical analysis

RULES:
- Always provide a prediction with reasoning
- Use your expert knowledge even with limited data
- Respond in valid JSON only
- Maximum confidence: 87
- Minimum confidence: 55
- Be honest about uncertainty
"""


# Specific major tournament competitions only
# Very precise - not generic terms
MAJOR_COMP_KEYWORDS = [
    "world championship",
    "fifa world cup",
    "world cup 2026",
    "uefa champions league",
    "champions league",
    "olympic games football",
    "copa america",
    "africa cup of nations",
    "afcon",
    "european championship",
    "euros 2026",
    "euros 2024",
    "fifa club world cup",
    "fifa intercontinental",
    "copa libertadores",
    "europa league",
    "conference league",
    "finalissima",
]


class FootballPredictor:
    """
    AI prediction engine.
    Uses Groq with fallback models.
    Detects major tournaments accurately.
    """

    def __init__(self):
        self.client   = Groq(
            api_key=os.environ.get("GROQ_API_KEY", "")
        )
        self.primary  = GROQ_PRIMARY_MODEL
        self.fallback = GROQ_FALLBACK_MODEL
        self.fast     = GROQ_FAST_MODEL

    def is_major(self, match: dict) -> bool:
        """
        Check if this is a genuine major tournament.

        Very specific matching to avoid false positives.
        Lebanese Premier League should NOT be major.
        Only actual World Cup, UCL, Copa America etc.
        """
        comp = match.get(
            "competition_name", ""
        ).lower()

        return any(
            keyword in comp
            for keyword in MAJOR_COMP_KEYWORDS
        )

    def analyse(self, match: dict) -> dict:
        """Analyse one match and return prediction."""
        is_major_match = self.is_major(match)
        prompt         = self._prompt(
            match, is_major_match
        )

        for model in [
            self.primary, self.fallback, self.fast
        ]:
            try:
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role":    "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {
                            "role":    "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.3,
                    max_tokens=600,
                    response_format={
                        "type": "json_object"
                    },
                )

                raw    = resp.choices[0].message.content
                result = json.loads(raw)
                conf   = result.get("confidence", 0)

                if conf < MIN_CONFIDENCE:
                    return None

                result["tier"]       = self._tier(conf)
                result["match_data"] = match
                result["is_major"]   = is_major_match
                return result

            except json.JSONDecodeError:
                continue
            except Exception as e:
                err = str(e)
                if (
                    "decommissioned" in err
                    or "not_found" in err
                    or "does not exist" in err
                ):
                    continue
                print(f"   Groq error: {e}")
                time.sleep(2)
                continue

        return None

    def analyse_all(self, matches: list) -> list:
        """
        Analyse all matches.
        Shows major tournament badge correctly.
        """
        predictions = []
        major_preds = []

        for i, m in enumerate(matches):
            home   = m.get("home_team", "?")
            away   = m.get("away_team", "?")
            comp   = m.get("competition_name", "?")
            is_maj = self.is_major(m)

            # Only show 🌍 for genuine major tournaments
            maj_label = " 🌍 MAJOR" if is_maj else ""

            print(
                f"   🤖 [{i+1}/{len(matches)}] "
                f"{home} vs {away} "
                f"({comp}){maj_label}"
            )

            pred = self.analyse(m)

            if pred:
                if is_maj:
                    major_preds.append(pred)
                else:
                    predictions.append(pred)

            time.sleep(0.5)

        # Sort regular picks by confidence
        predictions.sort(
            key=lambda x: x.get("confidence", 0),
            reverse=True,
        )

        # Major tournament picks always come first
        return major_preds + predictions

    def rank_predictions(
        self, predictions: list
    ) -> list:
        """Filter and rank final predictions."""
        valid = [
            p for p in predictions
            if p and p.get("tier") != "SKIP"
            and not p.get("avoid", False)
        ]

        majors = [
            p for p in valid if p.get("is_major")
        ]
        others = [
            p for p in valid
            if not p.get("is_major")
        ]

        others.sort(
            key=lambda x: x.get("confidence", 0),
            reverse=True,
        )

        return majors + others

    def _prompt(
        self, m: dict, is_major: bool
    ) -> str:
        """Build analysis prompt."""
        home = m.get("home_team", "Home")
        away = m.get("away_team", "Away")
        comp = m.get("competition_name", "Unknown")
        hf   = m.get("home_form", {})
        af   = m.get("away_form", {})
        h2h  = m.get("h2h", {})
        wx   = m.get("weather", {})

        major_note = ""
        if is_major:
            major_note = f"""
IMPORTANT: This is a major tournament match ({comp}).
Use your full expert knowledge of these teams.
This is a high profile match followers care about.
"""

        return f"""
{major_note}
Analyse this football match:

MATCH: {home} vs {away}
COMPETITION: {comp}

HOME ({home}):
Form: {hf.get("form_string", "Unknown")}
Win rate: {hf.get("win_rate", "Unknown")}%
Goals scored avg: {hf.get("goals_for_avg", "Unknown")}
Goals conceded avg: {hf.get("goals_against_avg", "Unknown")}
News: {m.get("home_news_note", "Nothing significant")}

AWAY ({away}):
Form: {af.get("form_string", "Unknown")}
Win rate: {af.get("win_rate", "Unknown")}%
Goals scored avg: {af.get("goals_for_avg", "Unknown")}
Goals conceded avg: {af.get("goals_against_avg", "Unknown")}
News: {m.get("away_news_note", "Nothing significant")}

H2H:
Home wins: {h2h.get("home_wins", "Unknown")}
Away wins: {h2h.get("away_wins", "Unknown")}
Draws: {h2h.get("draws", "Unknown")}
Avg goals: {h2h.get("avg_goals", "Unknown")}

Weather: {wx.get("description", "Normal")}

Return JSON:
{{
  "pick": "Home Win" or "Away Win" or "Draw" or "Over 2.5" or "Under 2.5" or "BTTS",
  "pick_short": "actual team name e.g. France Win",
  "confidence": 72,
  "reasoning": ["reason 1", "reason 2", "reason 3"],
  "risk": "main risk to this prediction",
  "predicted_score": "2-1",
  "avoid": false
}}
"""

    def _tier(self, confidence: int) -> str:
        """Classify prediction into tier."""
        if confidence >= BANKER_MIN:
            return "BANKER"
        if confidence >= STRONG_MIN:
            return "STRONG"
        if confidence >= VALUE_MIN:
            return "VALUE"
        return "SKIP"
