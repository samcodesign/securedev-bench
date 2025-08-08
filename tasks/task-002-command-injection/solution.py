from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route("/api/ping")
def ping_host():
    host = request.args.get("host", "8.8.8.8")
    
    # FIX: Using subprocess.run with a list of arguments prevents injection
    # The shell does not interpret the 'host' variable.
    try:
        result = subprocess.run(
            ["ping", "-c", "1", host],
            capture_output=True, text=True, check=True, timeout=5
        )
        output = result.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        output = f"Error pinging host: {e}"

    return output, 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
    