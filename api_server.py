import joblib
import numpy as np
import pandas as pd # Added to read your .xlsx file if needed for column names
from flask import Flask, request, jsonify
from datetime import datetime
import pytz  # For timezones
import requests  # For weather

# --- 1. CONFIGURATION ---
# PASTE YOUR KEY HERE
WEATHER_API_KEY = "YOUR_FREE_API_KEY_GOES_HERE" 
WEATHER_LOCATION = "Tunis,TN" # Farm's location
TUNISIA_TIMEZONE = pytz.timezone('Africa/Tunis')
EVENING_HOUR = 18 # 6 PM (18:00)

# --- 2. LOAD YOUR "BRAIN" ---
print("--- Loading AI 'brain' (pump_automation_model.joblib)... ---")
try:
    model = joblib.load('pump_automation_model.joblib')
    print("--- 'Brain' loaded successfully. ---")
except FileNotFoundError:
    print("--- FATAL ERROR: 'pump_automation_model.joblib' not found! ---")
    print("--- Make sure it's in the same folder as this script. ---")
    exit()

# --- 3. CREATE THE SERVER APP ---
app = Flask(__name__)

# --- 4. HELPER FUNCTIONS ---
def get_weather_forecast():
    """Calls OpenWeatherMap and returns True if rain is forecast."""
    try:
        url = (f"https://api.openweathermap.org/data/2.5/forecast"
               f"?q={WEATHER_LOCATION}&appid={WEATHER_API_KEY}&units=metric")
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Check the next 12 hours (4 entries of 3 hours each)
        for forecast in data['list'][:4]:
            if forecast['weather'][0]['main'] == 'Rain':
                print("--- Weather Check: Rain is forecast! ---")
                return True # It's going to rain!
        
        print("--- Weather Check: No rain forecast. ---")
        return False
    except Exception as e:
        print(f"--- Weather API Error: {e} ---")
        return False # Fail safe: assume no rain

def get_current_hour():
    """Gets the current hour in Tunisia (0-23)."""
    now = datetime.now(TUNISIA_TIMEZONE)
    return now.hour

# --- 5. THE MAIN "BRAIN" LOGIC ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from Teammate B's ESP32
        data = request.get_json()
        
        # Get sensor data
        # These names MUST match the columns in your Excel file
        features = [[
            data['soil_moisture'],
            data['temperature'],
            data['air_humidity']
        ]]
        
        # Get the specific plant
        plant_type = data.get('plant_type', 'unknown') # e.g., 'tomato', 'mint'

        # --- STEP 1: CONSULT THE "PAST" (ML MODEL) ---
        ai_decision = model.predict(features)[0] # 0 or 1
        
        if ai_decision == 0:
            print(f"[{plant_type}] AI Decision: 0 (Soil is moist)")
            return jsonify({'pump_action': 0, 'reason': 'Soil is already moist.'})

        # --- AI said "WATER", now we OPTIMIZE ---
        print(f"[{plant_type}] AI Decision: 1 (Soil is dry)")

        # --- STEP 2: CONSULT THE "FUTURE" (WEATHER) ---
        if get_weather_forecast():
            print("--- OVERRIDE: Rain is coming. ---")
            return jsonify({'pump_action': 0, 'reason': 'Soil is dry, but rain is forecast. Saving water!'})

        # --- STEP 3: CONSULT THE "CLOCK" & "PLANT" (EFFICIENCY) ---
        current_hour = get_current_hour()
        
        # Check for "Urgent" plants
        if plant_type == 'mint':
            print(f"--- URGENCY: '{plant_type}' is fragile. Watering NOW. ---")
            return jsonify({'pump_action': 1, 'reason': f'Soil is dry. Watering {plant_type} immediately!'})
        
        # Check for "Tough" plants (tomato, onion) and time
        if plant_type in ['tomato', 'onion']:
            if current_hour < EVENING_HOUR: # If it's before 6 PM
                print(f"--- SCHEDULING: '{plant_type}' can wait for evening. ---")
                return jsonify({'pump_action': 0, 'reason': f"Soil is dry, but it's too hot. Watering for {plant_type} is scheduled for this evening."})
            else: # It IS evening
                print(f"--- EFFICIENCY: It's evening. Watering {plant_type}. ---")
                return jsonify({'pump_action': 1, 'reason': f"Soil is dry. Watering {plant_type} now."})

        # Fallback for unknown plants
        return jsonify({'pump_action': 1, 'reason': 'Soil is dry. Watering now.'})

    except Exception as e:
        print(f"--- Main Error: {e} ---")
        return jsonify({'error': str(e)}), 400

# --- 6. START THE SERVER ---
if __name__ == '__main__':
    print("--- Starting 'Smart Scheduler' AI Brain Server... ---")
    app.run(host='0.0.0.0', port=5000)