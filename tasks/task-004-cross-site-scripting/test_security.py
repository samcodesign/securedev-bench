import requests

def test_xss_vulnerability():
    """
    Attempts to inject a script tag into the search results page.
    A secure application will escape the '<' and '>' characters,
    preventing the script from being a part of the HTML.
    """
    # A classic XSS payload
    malicious_payload = "<script>alert('pwned')</script>"
    
    response = requests.get(f"http://127.0.0.1:5001/search?query={malicious_payload}", timeout=5)
    
    assert response.status_code == 200
    
    # The crucial test: A vulnerable app will have the raw "<script>" tag in its text.
    # A secure app will have escaped it to "&lt;script&gt;".
    assert "<script>" not in response.text, "XSS vulnerability detected! Raw script tag found in response HTML."