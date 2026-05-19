"""Weather Tool - Get weather for a location."""

import json
import requests
from tools.registry import registry


def weather(loc: str) -> str:
    """Get weather for location."""
    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={loc}&count=1"
        ).json()
        if not geo.get("results"):
            return json.dumps({"error": f"{loc} not found."})
        res = geo["results"][0]
        w = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={res['latitude']}&longitude={res['longitude']}&current_weather=true&hourly=temperature_2m&forecast_hours=25&temperature_unit=fahrenheit&timezone=auto"
        ).json()
        now = w["current_weather"]["temperature"]
        future = w["hourly"]["temperature_2m"][-1]
        return json.dumps(
            {
                "location": res["name"],
                "current_temp_f": now,
                "forecast_24h_f": future,
                "latitude": res["latitude"],
                "longitude": res["longitude"],
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


WEATHER_SCHEMA = {
    "name": "weather",
    "description": "Get weather for a location. Returns current temperature and 24-hour forecast.",
    "parameters": {
        "type": "object",
        "properties": {"loc": {"type": "string", "description": "The location name"}},
        "required": ["loc"],
    },
}

registry.register(
    name="weather",
    toolset="weather",
    schema=WEATHER_SCHEMA,
    handler=lambda args, **kw: weather(loc=args.get("loc", "")),
    check_fn=None,
    emoji="☀️",
)
