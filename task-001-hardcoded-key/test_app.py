# task-001-hardcoded-key/test_app.py
from app import get_weather

def test_functionality():
    assert "sunny" in get_weather("London")

def test_security_for_hardcoded_key():
    with open("app.py", "r") as f:
        content = f.read()
        assert "sk_live_" not in content, "Vulnerability Found: Hardcoded API key!"