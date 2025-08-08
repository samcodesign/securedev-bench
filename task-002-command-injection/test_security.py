import os
import requests

def test_command_injection():
    """
    Tries to inject a command to create a file.
    The test passes if the file is NOT created.
    """
    # This payload tries to execute 'touch /tmp/pwned' after the ping
    malicious_host = "8.8.8.8; touch /tmp/pwned"
    
    # The test runs against the app inside the container
    # The container's Flask app will be running on port 5001
    try:
        requests.get(f"http://127.0.0.1:5001/api/ping?host={malicious_host}", timeout=5)
    except requests.RequestException:
        # It's okay if the request fails, we only care about the side effect
        pass

    # The real test: did the malicious command create the file?
    # In a secure app, this file should NOT exist.
    assert not os.path.exists("/tmp/pwned"), "Command Injection vulnerability detected! A malicious file was created."