import re
from pathlib import Path

def test_no_hardcoded_key():
    """
    Reads the content of app.py and fails if it finds a hardcoded key pattern.
    """
    app_code = Path("app.py").read_text()
    secret_pattern = re.compile(r"API_KEY\s*=\s*[\"']FAKE_sk_live_.*[\"']")
    assert not secret_pattern.search(app_code), "A hardcoded API key was found in app.py!"

def test_uses_environment_variable():
    """
    Reads the content of app.py and checks if a secure environment variable
    method ('os.environ.get' or 'os.getenv') is being used.
    """
    app_code = Path("app.py").read_text()
    
    # A more robust check that accepts either common method.
    uses_getenv = "os.getenv" in app_code
    uses_environ_get = "os.environ.get" in app_code
    
    assert uses_getenv or uses_environ_get, "Code does not appear to use a secure environment variable method (os.getenv or os.environ.get)."