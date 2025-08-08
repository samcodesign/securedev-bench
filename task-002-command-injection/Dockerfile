FROM python:3.9-slim

# --- NEW ---
# Install the 'ping' command, as the 'slim' image doesn't include it by default.
# 'apt-get update' refreshes the package lists.
# 'apt-get install -y' installs the package without asking for confirmation.
RUN apt-get update && apt-get install -y iputils-ping

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the Flask app in the background, then run pytest
CMD ["/bin/sh", "-c", "python app.py & sleep 2; pytest --json-report --json-report-file=report.json"]