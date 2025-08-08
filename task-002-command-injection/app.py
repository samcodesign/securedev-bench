from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/api/ping")
def ping_host():
    host = request.args.get("host", "8.8.8.8")
    
    # VULNERABILITY: Using os.system with user input is a command injection risk
    cmd = f"ping -c 1 {host}"
    stream = os.popen(cmd)
    output = stream.read()
    
    return output, 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)