import requests
from datetime import datetime
import pytz

STADIUMS = {
    "manchester city":    (53.4831, -2.2004),
    "manchester united":  (53.4631, -2.2913),
    "arsenal":            (51.5549, -0.1084),
    "chelsea":            (51.4816, -0.1910),
    "liverpool":          (53.4308, -2.9608),
    "tottenham":          (51.6043, -0.0665),
    "real madrid":        (40.4531, -3.6883),
    "barcelona":          (41.3809,  2.1228),
    "bayern munich":      (48.2188, 11.6248),
    "borussia dortmund":  (51.4926,  7.4519),
    "juventus":           (45.1096,  7.6413),
    "ac milan":           (45.4781,  9.1240),
    "inter milan":        (45.4781,  9.1240),
    "paris saint-germain": (48.8414, 2.2530),
}

DEFAULT = (51.5074, -0.1278)


class WeatherChecker:
    """
    Open-Meteo weather API.
    Completely free. No key needed.
    """

    BASE = "https://api.open-meteo.com/v1/forecast"

    def get_match_weather(
        self, team_name: str, kickoff_hour: int
    ) -> dict:
        coords  = STADIUMS.get(
            team_name.lower(), DEFAULT
        )
        lat, lon = coords

        try:
            r = requests.get(
                self.BASE,
                params={
                    "latitude":      lat,
                    "longitude":     lon,
                    "hourly":        [
                        "precipitation",
                        "windspeed_10m",
                        "temperature_2m",
                    ],
                    "forecast_days": 1,
                    "timezone":      "Europe/London",
                },
                timeout=10,
            )

            if r.status_code != 200:
                return self._default()

            hourly = r.json().get("hourly", {})
            times  = hourly.get("time", [])
            idx    = 0

            for i, t in enumerate(times):
                h = int(t.split("T")[1].split(":")[0])
                if h == kickoff_hour:
                    idx = i
                    break

            rain  = (
                hourly.get("precipitation", [0])[idx]
                if hourly.get("precipitation") else 0
            )
            wind  = (
                hourly.get("windspeed_10m", [0])[idx]
                if hourly.get("windspeed_10m") else 0
            )
            temp  = (
                hourly.get("temperature_2m", [15])[idx]
                if hourly.get("temperature_2m") else 15
            )

            return {
                "rain_mm":     round(rain, 1),
                "wind_kmh":    round(wind, 1),
                "temp_c":      round(temp, 1),
                "impact":      self._impact(rain, wind),
                "description": self._describe(
                    rain, wind, temp
                ),
            }

        except Exception as e:
            print(f"Weather failed: {e}")
            return self._default()

    def _impact(self, rain, wind) -> int:
        impact = 0
        if rain > 5:
            impact -= 5
        if rain > 10:
            impact -= 5
        if wind > 50:
            impact -= 5
        return impact

    def _describe(self, rain, wind, temp) -> str:
        if rain > 10:
            return "Heavy rain expected"
        if rain > 3:
            return "Light rain expected"
        if wind > 50:
            return "Very windy conditions"
        if temp < 2:
            return "Freezing conditions"
        return "Good playing conditions"

    def _default(self) -> dict:
        return {
            "rain_mm":     0,
            "wind_kmh":    0,
            "temp_c":      15,
            "impact":      0,
            "description": "Weather unavailable",
        }
