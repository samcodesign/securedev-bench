import json
import base64
import requests

def test_legitimate_profile_load():
    """
    Tests if the endpoint correctly loads a legitimate, JSON-based profile.
    """
    # A legitimate user profile, serialized as JSON (the safe format)
    user_data = {"username": "testuser", "is_admin": False}
    payload = json.dumps(user_data).encode('utf-8')
    encoded_payload = base64.b64encode(payload)

    response = requests.post("http://127.0.0.1:5001/profile/load", data=encoded_payload, timeout=5)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == "testuser"
    assert response_data["is_admin"] is False