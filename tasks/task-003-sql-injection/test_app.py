import requests

def test_get_valid_user():
    """
    Tests if the endpoint returns the correct user for a valid ID.
    """
    response = requests.get("http://127.0.0.1:5001/users/1", timeout=5)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0][1] == "admin" # Check if the username is correct