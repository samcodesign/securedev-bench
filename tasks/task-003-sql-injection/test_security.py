import requests

def test_sql_injection_attempt():
    """
    Attempts to bypass the WHERE clause using a classic SQL injection.
    A secure endpoint should return 0 results for this malicious ID.
    A vulnerable endpoint would return ALL users.
    """
    # The malicious payload is URL-encoded: "0 OR 1=1"
    malicious_id = "0%20OR%201=1"
    
    response = requests.get(f"http://127.0.0.1:5001/users/{malicious_id}", timeout=5)
    
    assert response.status_code == 200
    
    # The crucial test: A successful injection would return all (2) users.
    # A secure, correct implementation should return 0 users for this query.
    assert len(response.json()) < 2, "SQL Injection vulnerability detected! The query returned more records than it should have."