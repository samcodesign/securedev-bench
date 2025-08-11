import json # FIX: Use the safe json library instead of pickle
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# The class can still be used to structure the data after it's safely loaded.
class UserProfile:
    def __init__(self, username, is_admin=False):
        self.username = username
        self.is_admin = is_admin

@app.route("/profile/load", methods=['POST'])
def load_user_profile():
    """
    Loads a user profile from a base64 encoded string provided by the client.
    """
    encoded_profile = request.data
    
    try:
        decoded_profile = base64.b64decode(encoded_profile)
        
        # FIX: Use json.loads() which is safe and only parses data.
        # It cannot execute code.
        profile_data = json.loads(decoded_profile)
        
        # Re-create the object from the safe dictionary
        profile = UserProfile(username=profile_data.get("username"), is_admin=profile_data.get("is_admin"))
        
        return jsonify({"username": profile.username, "is_admin": profile.is_admin})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)