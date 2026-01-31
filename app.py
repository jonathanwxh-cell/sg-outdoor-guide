"""
Singapore Weather & Outdoor Activity Dashboard
Real-time data from data.gov.sg APIs
Features: Exercise safety, laundry forecast, activity suggestions
"""
from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import pytz

app = Flask(__name__)

# API endpoints
WEATHER_API = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
PSI_API = "https://api.data.gov.sg/v1/environment/psi"
WEATHER_24H_API = "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast"
UV_API = "https://api.data.gov.sg/v1/environment/uv-index"
TEMP_API = "https://api.data.gov.sg/v1/environment/air-temperature"
HUMIDITY_API = "https://api.data.gov.sg/v1/environment/relative-humidity"

def calculate_heat_index(temp_c, humidity):
    """Calculate 'feels like' temperature using heat index formula"""
    # Convert to Fahrenheit for the standard formula
    temp_f = (temp_c * 9/5) + 32
    
    # Simple formula for lower temps
    if temp_f < 80:
        hi_f = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity * 0.094))
    else:
        # Rothfusz regression formula
        hi_f = (-42.379 + 
                2.04901523 * temp_f + 
                10.14333127 * humidity - 
                0.22475541 * temp_f * humidity - 
                0.00683783 * temp_f**2 - 
                0.05481717 * humidity**2 + 
                0.00122874 * temp_f**2 * humidity + 
                0.00085282 * temp_f * humidity**2 - 
                0.00000199 * temp_f**2 * humidity**2)
        
        # Adjustments
        if humidity < 13 and 80 <= temp_f <= 112:
            adj = ((13 - humidity) / 4) * ((17 - abs(temp_f - 95)) / 17)**0.5
            hi_f -= adj
        elif humidity > 85 and 80 <= temp_f <= 87:
            adj = ((humidity - 85) / 10) * ((87 - temp_f) / 5)
            hi_f += adj
    
    # Convert back to Celsius
    hi_c = (hi_f - 32) * 5/9
    return round(hi_c, 1)

def get_feels_like_verdict(feels_like):
    """Get advice based on feels-like temperature"""
    if feels_like >= 40:
        return {"level": "Extreme", "color": "#9C27B0", "emoji": "🥵", "advice": "Dangerous heat - stay indoors with AC"}
    elif feels_like >= 35:
        return {"level": "Very Hot", "color": "#F44336", "emoji": "🔥", "advice": "Limit outdoor activity, hydrate constantly"}
    elif feels_like >= 32:
        return {"level": "Hot", "color": "#FF9800", "emoji": "☀️", "advice": "Take breaks in shade, drink water"}
    elif feels_like >= 28:
        return {"level": "Warm", "color": "#FFEB3B", "emoji": "🌤️", "advice": "Comfortable for most activities"}
    else:
        return {"level": "Pleasant", "color": "#4CAF50", "emoji": "😊", "advice": "Great conditions!"}

def get_psi_level(psi_value):
    """Return PSI level description and color"""
    if psi_value <= 50:
        return {"level": "Good", "color": "#4CAF50", "emoji": "😊", "exercise_ok": True}
    elif psi_value <= 100:
        return {"level": "Moderate", "color": "#FFEB3B", "emoji": "😐", "exercise_ok": True}
    elif psi_value <= 200:
        return {"level": "Unhealthy", "color": "#FF9800", "emoji": "😷", "exercise_ok": False}
    elif psi_value <= 300:
        return {"level": "Very Unhealthy", "color": "#F44336", "emoji": "🤢", "exercise_ok": False}
    else:
        return {"level": "Hazardous", "color": "#9C27B0", "emoji": "☠️", "exercise_ok": False}

def get_uv_level(uv_value):
    """Return UV level info"""
    if uv_value <= 2:
        return {"level": "Low", "color": "#4CAF50", "advice": "Safe to be outside"}
    elif uv_value <= 5:
        return {"level": "Moderate", "color": "#FFEB3B", "advice": "Wear sunscreen"}
    elif uv_value <= 7:
        return {"level": "High", "color": "#FF9800", "advice": "Seek shade midday"}
    elif uv_value <= 10:
        return {"level": "Very High", "color": "#F44336", "advice": "Avoid sun 10am-4pm"}
    else:
        return {"level": "Extreme", "color": "#9C27B0", "advice": "Stay indoors midday"}

def calculate_exercise_score(psi, uv, temp, humidity):
    """Calculate exercise safety score 0-100"""
    score = 100
    
    # PSI impact (most important)
    if psi > 100:
        score -= 50
    elif psi > 75:
        score -= 30
    elif psi > 50:
        score -= 15
    
    # UV impact
    if uv > 10:
        score -= 25
    elif uv > 7:
        score -= 15
    elif uv > 5:
        score -= 10
    
    # Temperature impact (ideal 20-26°C)
    if temp > 34:
        score -= 30
    elif temp > 32:
        score -= 20
    elif temp > 30:
        score -= 10
    elif temp < 20:
        score -= 5
    
    # Humidity impact (ideal < 70%)
    if humidity > 90:
        score -= 20
    elif humidity > 80:
        score -= 10
    elif humidity > 70:
        score -= 5
    
    return max(0, min(100, score))

def get_exercise_verdict(score):
    """Get exercise recommendation"""
    if score >= 70:
        return {"verdict": "GO!", "color": "#4CAF50", "emoji": "🏃", "advice": "Great conditions for outdoor exercise!"}
    elif score >= 50:
        return {"verdict": "CAUTION", "color": "#FFEB3B", "emoji": "⚠️", "advice": "Exercise possible but stay hydrated, avoid midday"}
    else:
        return {"verdict": "AVOID", "color": "#F44336", "emoji": "🛑", "advice": "Consider indoor exercise or wait for better conditions"}

def get_laundry_forecast(weather_forecasts, humidity):
    """Determine if it's good to hang laundry"""
    rain_keywords = ["rain", "shower", "thunder", "storm"]
    
    rain_expected = any(
        any(kw in f.get("forecast", "").lower() for kw in rain_keywords) 
        for f in weather_forecasts[:10]  # Check first 10 areas
    )
    
    if rain_expected:
        return {"verdict": "NO", "color": "#F44336", "emoji": "🌧️", "advice": "Rain expected - dry indoors"}
    elif humidity > 85:
        return {"verdict": "SLOW", "color": "#FFEB3B", "emoji": "💧", "advice": "High humidity - clothes will dry slowly"}
    else:
        return {"verdict": "YES", "color": "#4CAF50", "emoji": "👕", "advice": "Good drying conditions!"}

def get_activity_suggestions(psi, uv, temp, rain_expected):
    """Suggest activities based on conditions"""
    suggestions = []
    
    if rain_expected:
        suggestions.append({"activity": "Visit a museum", "emoji": "🏛️"})
        suggestions.append({"activity": "Shopping mall exploration", "emoji": "🛍️"})
        suggestions.append({"activity": "Indoor rock climbing", "emoji": "🧗"})
        suggestions.append({"activity": "Café hopping", "emoji": "☕"})
    elif psi > 100:
        suggestions.append({"activity": "Stay indoors", "emoji": "🏠"})
        suggestions.append({"activity": "Gym workout", "emoji": "🏋️"})
        suggestions.append({"activity": "Movie marathon", "emoji": "🎬"})
    elif uv > 7 or temp > 32:
        suggestions.append({"activity": "Swimming", "emoji": "🏊"})
        suggestions.append({"activity": "Early morning jog (before 8am)", "emoji": "🌅"})
        suggestions.append({"activity": "Evening park walk (after 6pm)", "emoji": "🌆"})
        suggestions.append({"activity": "Air-con hawker centre lunch", "emoji": "🍜"})
    else:
        suggestions.append({"activity": "Park run or jog", "emoji": "🏃"})
        suggestions.append({"activity": "Cycling at ECP", "emoji": "🚴"})
        suggestions.append({"activity": "Gardens by the Bay", "emoji": "🌺"})
        suggestions.append({"activity": "Outdoor photography", "emoji": "📸"})
    
    return suggestions[:4]

def get_weather_emoji(forecast):
    """Return emoji for weather condition"""
    forecast_lower = forecast.lower()
    if "thunder" in forecast_lower:
        return "⛈️"
    elif "heavy rain" in forecast_lower or "heavy showers" in forecast_lower:
        return "🌧️"
    elif "rain" in forecast_lower or "showers" in forecast_lower:
        return "🌦️"
    elif "cloudy" in forecast_lower:
        return "☁️"
    elif "partly cloudy" in forecast_lower:
        return "⛅"
    elif "fair" in forecast_lower or "sunny" in forecast_lower:
        return "☀️"
    elif "hazy" in forecast_lower:
        return "🌫️"
    elif "windy" in forecast_lower:
        return "💨"
    else:
        return "🌤️"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dashboard")
def api_dashboard():
    """Combined dashboard data with all smart features"""
    try:
        # Fetch all data
        psi_data = requests.get(PSI_API, timeout=10).json()
        weather_data = requests.get(WEATHER_API, timeout=10).json()
        uv_data = requests.get(UV_API, timeout=10).json()
        temp_data = requests.get(TEMP_API, timeout=10).json()
        humidity_data = requests.get(HUMIDITY_API, timeout=10).json()
        forecast_24h = requests.get(WEATHER_24H_API, timeout=10).json()
        
        # Process PSI
        psi_value = 50  # default
        psi_regions = []
        if psi_data.get("items"):
            readings = psi_data["items"][0].get("readings", {})
            psi_readings = readings.get("psi_twenty_four_hourly", {})
            pm25_readings = readings.get("pm25_twenty_four_hourly", {})
            
            for region_key, display_name in {"north": "North", "south": "South", "east": "East", "west": "West", "central": "Central"}.items():
                psi_val = psi_readings.get(region_key, 0)
                level_info = get_psi_level(psi_val)
                psi_regions.append({
                    "region": display_name,
                    "psi": psi_val,
                    "pm25": pm25_readings.get(region_key, 0),
                    **level_info
                })
            psi_value = sum(r["psi"] for r in psi_regions) / len(psi_regions) if psi_regions else 50
        
        # Process UV
        uv_value = 0
        if uv_data.get("items") and uv_data["items"][0].get("index"):
            uv_value = uv_data["items"][0]["index"][0].get("value", 0)
        uv_info = get_uv_level(uv_value)
        
        # Process Temperature & Humidity
        temp_value = 28
        humidity_value = 80
        if temp_data.get("items") and temp_data["items"][0].get("readings"):
            temps = [r["value"] for r in temp_data["items"][0]["readings"]]
            temp_value = sum(temps) / len(temps) if temps else 28
        if humidity_data.get("items") and humidity_data["items"][0].get("readings"):
            humids = [r["value"] for r in humidity_data["items"][0]["readings"]]
            humidity_value = sum(humids) / len(humids) if humids else 80
        
        # Process Weather forecasts
        forecasts = []
        rain_expected = False
        rain_keywords = ["rain", "shower", "thunder", "storm"]
        if weather_data.get("items"):
            for f in weather_data["items"][0].get("forecasts", []):
                forecast_text = f["forecast"]
                forecasts.append({
                    "area": f["area"],
                    "forecast": forecast_text,
                    "emoji": get_weather_emoji(forecast_text)
                })
                if any(kw in forecast_text.lower() for kw in rain_keywords):
                    rain_expected = True
        
        # Calculate feels-like temperature
        feels_like = calculate_heat_index(temp_value, humidity_value)
        feels_like_info = get_feels_like_verdict(feels_like)
        
        # Calculate smart scores
        exercise_score = calculate_exercise_score(psi_value, uv_value, temp_value, humidity_value)
        exercise_verdict = get_exercise_verdict(exercise_score)
        laundry = get_laundry_forecast(forecasts, humidity_value)
        activities = get_activity_suggestions(psi_value, uv_value, temp_value, rain_expected)
        
        # 24h outlook
        outlook_24h = {}
        if forecast_24h.get("items"):
            item = forecast_24h["items"][0]
            outlook_24h = {
                "general": item.get("general", {}),
                "periods": item.get("periods", [])
            }
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now(pytz.timezone('Asia/Singapore')).strftime("%Y-%m-%d %H:%M:%S"),
            "current": {
                "temperature": round(temp_value, 1),
                "humidity": round(humidity_value, 1),
                "uv_index": uv_value,
                "uv_info": uv_info,
                "avg_psi": round(psi_value),
                "feels_like": feels_like,
                "feels_like_info": feels_like_info
            },
            "psi_regions": psi_regions,
            "exercise": {
                "score": exercise_score,
                **exercise_verdict
            },
            "laundry": laundry,
            "activities": activities,
            "rain_expected": rain_expected,
            "forecasts": sorted(forecasts, key=lambda x: x["area"]),
            "outlook_24h": outlook_24h
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/weather")
def api_weather():
    try:
        response = requests.get(WEATHER_API, timeout=10)
        data = response.json()
        
        area_metadata = {area["name"]: area["label_location"] for area in data.get("area_metadata", [])}
        
        forecasts = []
        if data.get("items"):
            item = data["items"][0]
            valid_period = item.get("valid_period", {})
            
            for forecast in item.get("forecasts", []):
                area_name = forecast["area"]
                weather = forecast["forecast"]
                location = area_metadata.get(area_name, {})
                
                forecasts.append({
                    "area": area_name,
                    "forecast": weather,
                    "emoji": get_weather_emoji(weather),
                    "lat": location.get("latitude"),
                    "lng": location.get("longitude")
                })
        
        forecasts.sort(key=lambda x: x["area"])
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now(pytz.timezone('Asia/Singapore')).strftime("%Y-%m-%d %H:%M:%S"),
            "forecasts": forecasts,
            "valid_period": valid_period
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/psi")
def api_psi():
    try:
        response = requests.get(PSI_API, timeout=10)
        data = response.json()
        
        regions = []
        if data.get("items"):
            item = data["items"][0]
            readings = item.get("readings", {})
            psi_readings = readings.get("psi_twenty_four_hourly", {})
            pm25_readings = readings.get("pm25_twenty_four_hourly", {})
            
            region_names = {"north": "North", "south": "South", "east": "East", "west": "West", "central": "Central"}
            
            for region_key, display_name in region_names.items():
                psi_value = psi_readings.get(region_key, 0)
                pm25_value = pm25_readings.get(region_key, 0)
                level_info = get_psi_level(psi_value)
                
                regions.append({
                    "region": display_name,
                    "psi": psi_value,
                    "pm25": pm25_value,
                    "level": level_info["level"],
                    "color": level_info["color"],
                    "emoji": level_info["emoji"]
                })
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now(pytz.timezone('Asia/Singapore')).strftime("%Y-%m-%d %H:%M:%S"),
            "regions": regions
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=False)
