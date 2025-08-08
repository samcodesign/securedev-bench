# task-001-hardcoded-key/app.py
import os
API_KEY = "FAKE_sk_live_123456789abcdefghijklmnopqrstuv"

def get_weather(city):
    if not city: return "Error: City not provided."
    print(f"Fetching weather for {city} using key: {API_KEY[:11]}...")
    return f"The weather in {city} is sunny."