import requests

def test_ping_functionality():
    """
    Tests if the ping endpoint works with a legitimate host.
    """
    host_to_test = "1.1.1.1"
    response = requests.get(f"http://127.0.0.1:5001/api/ping?host={host_to_test}", timeout=10)
    
    # Check 1: The request was successful
    assert response.status_code == 200
    
    # Check 2: The output contains reliable text from the ping command
    # This is much more robust than checking for "pinging..."
    assert "packets transmitted" in response.text.lower()
    
    # Check 3: The output mentions the host we pinged
    assert host_to_test in response.text