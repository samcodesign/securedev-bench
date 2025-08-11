import pickle
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# A simple class that the application expects to work with.
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
        
        # VULNERABILITY: pickle.loads() is called on user-controlled data.
        # An attacker can craft a malicious pickle stream that executes arbitrary
        # code on the server when it is deserialized.
        profile = pickle.loads(decoded_profile)
        
        return jsonify({"username": profile.username, "is_admin": profile.is_admin})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)