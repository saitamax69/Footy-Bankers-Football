import os
import json
import time
from groq import Groq
from config import (
    BANKER_MIN, STRONG_MIN, VALUE_MIN,
    MIN_CONFIDENCE,
)


SYSTEM_PROMPT = """
You are an expert football analyst.
You have watched football your whole life.
You analyse matches using form, head to head,
goals data, injuries, and conditions.

You always respond in valid JSON only.
Never add text outside the JSON.
Be honest about uncertainty.
Maximum confidence you ever give: 87
Minimum to recommend: 55
"""


class FootballPredictor:
    """
    AI prediction engine using Groq.
    Single model. Fast. Free.
    """

    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY", "")
        )
        self.model = "llama-3.1-70b-versatile"
        self.fallback = "mixtral-8x7b-32768"

    def analyse(self, match: dict) -> dict:
        """Analyse one match and return prediction."""
        prompt = self._build_prompt(match)

        for model in [self.model, self.fallback]:
            try:
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.3,
                    max_tokens=600,
                    response_format={"type": "json_object"},
                )

                raw = resp.choices[0].message.content
                result = json.loads(raw)

                conf = result.get("confidence", 0)
                if conf < MIN_CONFIDENCE:
                    return None

                result["tier"]       = self._tier(conf)
                result["match_data"] = match
                return result

            except json.JSONDecodeError:
                print(f"JSON error with {model}")
                continue
            except Exception as e:
                print(f"Groq error ({model}): {e}")
                time.sleep(2)
                continue

        return None

    def analyse_all(self, matches: list) -> list:
        """Analyse all matches. Return valid predictions."""
        results = []
        for i, m in enumerate(matches):
            home = m.get("home_team", "?")
            away = m.get("away_team", "?")
            print(
                f"   🤖 Analysing {i+1}/{len(matches)}: "
                f"{home} vs {away}"
            )

            pred = self.analyse(m)
            if pred:
                results.append(pred)

            time.sleep(0.5)

        results.sort(
            key=lambda x: x.get("confidence", 0),
            reverse=True,
        )
        return results

    def _build_prompt(self, m: dict) -> str:
        home = m.get("home_team", "Home Team")
        away = m.get("away_team", "Away Team")
        comp = m.get("competition_name", "Unknown")
        hf   = m.get("home_form", {})
        af   = m.get("away_form", {})
        h2h  = m.get("h2h", {})
        wx   = m.get("weather", {})

        return f"""
Analyse this football match and predict the outcome.

MATCH: {home} vs {away}
COMPETITION: {comp}

HOME TEAM - {home}:
Form string: {hf.get('form_string', 'Unknown')}
Win rate: {hf.get('win_rate', 'Unknown')}%
Goals scored avg: {hf.get('goals_for_avg', 'Unknown')}
Goals conceded avg: {hf.get('goals_against_avg', 'Unknown')}
Points per game: {hf.get('ppg', 'Unknown')}
News impact: {m.get('home_news_note', 'Nothing major')}

AWAY TEAM - {away}:
Form string: {af.get('form_string', 'Unknown')}
Win rate: {af.get('win_rate', 'Unknown')}%
Goals scored avg: {af.get('goals_for_avg', 'Unknown')}
Goals conceded avg: {af.get('goals_against_avg', 'Unknown')}
Points per game: {af.get('ppg', 'Unknown')}
News impact: {m.get('away_news_note', 'Nothing major')}

HEAD TO HEAD:
Home wins: {h2h.get('home_wins', 'Unknown')}
Away wins: {h2h.get('away_wins', 'Unknown')}
Draws: {h2h.get('draws', 'Unknown')}
Average goals: {h2h.get('avg_goals', 'Unknown')}

CONDITIONS:
Weather: {wx.get('description', 'Normal')}
Weather impact: {wx.get('impact', 0)}

Respond in this exact JSON:
{{
  "pick": "Home Win" or "Away Win" or "Draw" or "Over 2.5" or "Under 2.5" or "BTTS",
  "pick_short": "use actual team name e.g. City Win",
  "confidence": 68,
  "reasoning": ["reason 1", "reason 2", "reason 3"],
  "risk": "main risk to this pick",
  "predicted_score": "2-1",
  "avoid": false
}}
"""

    def _tier(self, confidence: int) -> str:
        if confidence >= BANKER_MIN:
            return "BANKER"
        if confidence >= STRONG_MIN:
            return "STRONG"
        if confidence >= VALUE_MIN:
            return "VALUE"
        return "SKIP"
