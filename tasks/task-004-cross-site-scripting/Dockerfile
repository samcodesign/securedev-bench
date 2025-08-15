FROM python:3.9-slim

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# --- THIS IS THE FIX ---
# Add a dedicated step to compile-check the app.py file.
# If the AI has produced a SyntaxError, the 'docker build' process
# will fail here with a clear and immediate error message.
RUN python -m py_compile app.py

# The CMD is now simpler, as the syntax check has already passed.
# Use && to ensure the container fails if pytest fails.
CMD ["/bin/sh", "-c", "python app.py & sleep 2; pytest --json-report --json-report-file=report.json && echo '--- Pytest finished ---'"]