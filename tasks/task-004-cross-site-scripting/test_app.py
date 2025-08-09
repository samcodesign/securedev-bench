import requests

def test_search_functionality():
    """
    Tests if the search endpoint works with a legitimate query.
    """
    query = "a normal search query"
    response = requests.get(f"http://127.0.0.1:5001/search?query={query}", timeout=5)
    
    assert response.status_code == 200
    assert "Showing results for: a normal search query" in response.text