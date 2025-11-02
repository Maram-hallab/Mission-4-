# Mission 4: Mabrouka the Predictor

This folder contains the complete AI "brain" for our project, fulfilling Mission 4.

## 1. What It Is
This is an intelligent API server that combines a **Machine Learning model** (trained on past data) with **live data** (Weather, Time, and Plant Type) to make optimized watering decisions.

## 2. Our Result
By training on a real-world dataset (`datasetpump.xlsx`), our "base brain" achieved **99.83% accuracy**.

## 3. The "Smart Scheduler" Logic
Our server (`api_server.py`) is the central brain for the project. When it receives a request from the ESP32, it executes a 4-step logic:

1.  **Consults the "Past" (ML Model):** Uses the 99.83% accurate `pump_automation_model.joblib` to see if the soil is dry.
2.  **Consults the "Future" (Weather API):** If the soil is dry, it checks OpenWeatherMap. If rain is forecast, it **overrides** the decision to save water.
3.  **Optimizes for Efficiency (The Clock):** If no rain is forecast, it checks the time. For tough plants (tomatoes, onions), it **schedules** the watering for the evening (after 6 PM) to reduce evaporation.
4.  **Handles Urgency (The Plant):** For fragile plants (the "stubborn mint"), it **overrides** the schedule and waters immediately to prevent wilting.

This system directly addresses the prompt: it "learns from the past," "optimizes and avoids waste," and is smart enough to "water this evening."