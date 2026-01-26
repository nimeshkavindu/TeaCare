import httpx
from datetime import datetime

# --- HELPER: Condition Text Map ---
def get_condition_text(c: int) -> str:
    if c in [0]: return "Sunny"
    if c in [1, 2, 3]: return "Cloudy"
    if c in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "Rainy"
    return "Clear"

# --- HELPER: Professional Weather Analysis ---
def analyze_weather_risk(temp, humidity, rain, wind, condition):
    """
    Returns a professional assessment based on Tea Agronomy principles.
    """
    alerts = []
    
    # 1. Fungal Disease Risk (Blister Blight / Root Rot)
    if humidity > 85 and (condition in ["Rainy", "Cloudy"] or rain > 0.5):
        alerts.append({
            "title": "⚠️ Fungal Risk Alert",
            "message": "High humidity detected. Conditions are favorable for Blister Blight. Inspect tender leaves.",
            "type": "Alert",
            "risk": "High"
        })

    # 2. Pest Risk (Mites / Thrips)
    elif temp > 30 and humidity < 60:
        alerts.append({
            "title": "🕷️ Pest Risk Warning",
            "message": "High temperature and low humidity detected. Conditions favor Red Spider Mite activity. Monitor fields.",
            "type": "Alert", 
            "risk": "Medium"
        })

    # 3. Operational Safety (Spraying)
    if wind > 15:
        alerts.append({
            "title": "💨 High Wind Alert",
            "message": "Wind speeds > 15km/h. Spraying is NOT recommended due to chemical drift.",
            "type": "Info",
            "risk": "Medium"
        })
    elif rain > 0.0:
        alerts.append({
            "title": "🌧️ Spraying Advisory",
            "message": "Rainfall detected. Avoid spraying fertilizers/pesticides to prevent washout.",
            "type": "Info",
            "risk": "Low"
        })

    # 4. General Heavy Rain
    if rain > 20.0:
        alerts.append({
            "title": "🌧️ Heavy Rain Alert",
            "message": "Significant rainfall forecast. Ensure drainage channels are clear to prevent waterlogging.",
            "type": "Alert",
            "risk": "High"
        })

    # Default: Good Conditions
    if not alerts:
        alerts.append({
            "title": "✅ Optimal Conditions",
            "message": "Weather is favorable for routine plantation work.",
            "type": "Success",
            "risk": "Low"
        })

    return alerts

class WeatherService:
    async def get_forecast(self, lat: float, lng: float):
        """
        Fetches weather data, determines location name, and runs risk analysis.
        """
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        geo_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
        
        location_name = "Unknown Estate"
        
        async with httpx.AsyncClient() as client:
            # 1. Fetch Weather
            try:
                weather_resp = await client.get(weather_url)
                weather_data = weather_resp.json()
            except Exception as e:
                print(f"Weather API Error: {e}")
                raise e

            # 2. Fetch Location (Soft fail if error)
            try:
                geo_resp = await client.get(geo_url, headers={"User-Agent": "TeaCareApp/1.0"})
                if geo_resp.status_code == 200:
                    address = geo_resp.json().get("address", {})
                    city = address.get("city") or address.get("town") or address.get("village")
                    location_name = city if city else "Sri Lanka"
            except:
                pass

        # 3. Extract & Parse Data
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m", 0)
        humidity = current.get("relative_humidity_2m", 0)
        wind = current.get("wind_speed_10m", 0)
        rain = current.get("precipitation", 0)
        code = current.get("weather_code", 0)
        
        condition_text = get_condition_text(code)

        # 4. Run Analysis
        analysis = analyze_weather_risk(temp, humidity, rain, wind, condition_text)
        primary_alert = analysis[0]

        # 5. Format Daily Forecast
        daily = weather_data.get("daily", {})
        forecast_list = []
        if "time" in daily:
            for i in range(len(daily["time"])):
                forecast_list.append({
                    "date": daily["time"][i],
                    "max_temp": round(daily["temperature_2m_max"][i]),
                    "min_temp": round(daily["temperature_2m_min"][i]),
                    "rain_sum": daily["precipitation_sum"][i],
                    "condition": get_condition_text(daily["weather_code"][i])
                })

        # Return structured data
        return {
            "location": location_name, 
            "temperature": round(temp),
            "humidity": humidity,
            "wind_speed": wind,
            "condition": condition_text,
            "risk_level": primary_alert["risk"],
            "disease_forecast": primary_alert["title"],
            "advice": primary_alert["message"],
            "spraying_condition": "Unsafe" if wind > 15 or rain > 0 else "Safe",
            "daily_forecast": forecast_list,
            "primary_alert": primary_alert # Passed for Notification logic in endpoint
        }

weather_manager = WeatherService()