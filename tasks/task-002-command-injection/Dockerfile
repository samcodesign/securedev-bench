FROM python:3.9-slim

RUN apt-get update && apt-get install -y iputils-ping

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use && to ensure the container fails if pytest fails
CMD ["/bin/sh", "-c", "python app.py & sleep 2; pytest --json-report --json-report-file=report.json && echo '--- Pytest finished ---'"]