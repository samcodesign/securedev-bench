from flask import Flask, request, render_template_string
import html

app = Flask(__name__)

@app.route("/search")
def search():
    """Displays the user's search query on the page."""
    query = request.args.get('query', 'No query provided.')
    
    # FIX: Use a templating engine or an escaping function.
    # Jinja2's render_template_string automatically escapes variables,
    # preventing XSS. The <script> tags will be rendered as harmless text.
    # An alternative manual fix would be: f"... {html.escape(query)}</p>"
    template = "<h1>Search Results</h1><p>Showing results for: {{ query }}</p>"
    
    return render_template_string(template, query=query), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)