FROM python:3.9-slim

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add a compile check for robustness against AI syntax errors
# Run the Flask app in the background, then run pytest
CMD ["/bin/sh", "-c", "python -m py_compile app.py && python app.py & sleep 2; pytest --json-report --json-report-file=report.json && echo '--- Pytest finished ---'"]