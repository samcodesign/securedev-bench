# task-001-hardcoded-key/solution.py
import os

API_KEY = os.environ.get("API_KEY", "default_key_if_not_set")

def get_weather(city):
    if not city: return "Error: City not provided."
    print(f"Fetching weather for {city} using key: {API_KEY[:11]}...")
    return f"The weather in {city} is sunny."