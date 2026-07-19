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
    MAJOR_TOURNAMENTS,
)


SYSTEM_PROMPT = """
You are an expert football analyst with 20 years
of experience covering all global competitions.

Your knowledge includes:
- FIFA World Cup history and current tournament
- UEFA Champions League, Europa League
- All top European leagues
- International tournaments worldwide
- Team strengths, weaknesses, tactics
- Current form and player situations

RULES:
- World Cup and major tournament matches always get a prediction
- Use your knowledge even when local form data is missing
- Never say you cannot predict a match
- Respond in valid JSON only
- Maximum confidence: 87
- Minimum confidence for normal matches: 55
- For World Cup/UCL finals: always provide a pick
"""


class FootballPredictor:
    """
    AI prediction engine.
    Major tournament aware.
    Uses multiple Groq models as fallback.
    """

    def __init__(self):
        self.client   = Groq(
            api_key=os.environ.get("GROQ_API_KEY", "")
        )
        self.primary  = GROQ_PRIMARY_MODEL
        self.fallback = GROQ_FALLBACK_MODEL
        self.fast     = GROQ_FAST_MODEL

    def is_major(self, match: dict) -> bool:
        """Check if match is a major tournament."""
        comp = (
            match.get("competition_name", "")
            + " "
            + match.get("competition_code", "")
        ).lower()
        return any(t in comp for t in MAJOR_TOURNAMENTS)

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

                # Lower threshold for major tournaments
                min_conf = (
                    45 if is_major_match
                    else MIN_CONFIDENCE
                )

                if conf < min_conf:
                    return None

                result["tier"]       = self._tier(conf)
                result["match_data"] = match
                result["is_major"]   = is_major_match
                return result

            except json.JSONDecodeError:
                print(f"   JSON error with {model}")
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
        Major tournaments always included.
        Regular matches filtered by confidence.
        """
        predictions  = []
        major_preds  = []

        for i, m in enumerate(matches):
            home      = m.get("home_team", "?")
            away      = m.get("away_team", "?")
            comp      = m.get("competition_name", "?")
            is_maj    = self.is_major(m)
            maj_label = "🌍 MAJOR" if is_maj else ""

            print(
                f"   🤖 [{i+1}/{len(matches)}] "
                f"{home} vs {away} "
                f"({comp}) {maj_label}"
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

        # Major tournament picks ALWAYS come first
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

        major_instruction = ""
        if is_major:
            major_instruction = f"""
IMPORTANT: This is a MAJOR TOURNAMENT match
({comp}).
You MUST provide a prediction.
Use your expert knowledge of these teams
and this competition even if form data
is limited or missing.
This is a high-profile match that followers
expect to see covered.
"""

        return f"""
{major_instruction}
Analyse this football match:

MATCH: {home} vs {away}
COMPETITION: {comp}

HOME TEAM ({home}):
Form last 10: {hf.get("form_string", "Unknown")}
Win rate: {hf.get("win_rate", "Unknown")}%
Goals scored avg: {hf.get("goals_for_avg", "Unknown")}
Goals conceded avg: {hf.get("goals_against_avg", "Unknown")}
News: {m.get("home_news_note", "Nothing significant")}

AWAY TEAM ({away}):
Form last 10: {af.get("form_string", "Unknown")}
Win rate: {af.get("win_rate", "Unknown")}%
Goals scored avg: {af.get("goals_for_avg", "Unknown")}
Goals conceded avg: {af.get("goals_against_avg", "Unknown")}
News: {m.get("away_news_note", "Nothing significant")}

HEAD TO HEAD:
Home wins: {h2h.get("home_wins", "Unknown")}
Away wins: {h2h.get("away_wins", "Unknown")}
Draws: {h2h.get("draws", "Unknown")}
Average goals: {h2h.get("avg_goals", "Unknown")}

CONDITIONS:
Weather: {wx.get("description", "Normal conditions")}
Weather impact: {wx.get("impact", 0)}

Respond in this exact JSON format:
{{
  "pick": "Home Win" or "Away Win" or "Draw" or "Over 2.5" or "Under 2.5" or "BTTS",
  "pick_short": "use actual team name e.g. France Win",
  "confidence": 72,
  "reasoning": [
    "reason 1",
    "reason 2",
    "reason 3"
  ],
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
