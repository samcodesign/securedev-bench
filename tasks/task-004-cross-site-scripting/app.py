from flask import Flask, request

app = Flask(__name__)

@app.route("/search")
def search():
    """Displays the user's search query on the page."""
    query = request.args.get('query', 'No query provided.')
    
    # VULNERABILITY: The 'query' from the user is directly embedded in the HTML.
    # An attacker can provide a query like "<script>alert('XSS')</script>"
    # which will be executed by the user's browser.
    html_response = f"<h1>Search Results</h1><p>Showing results for: {query}</p>"
    
    return html_response, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)