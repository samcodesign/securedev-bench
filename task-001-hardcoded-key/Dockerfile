# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# The command to run when the container starts
# NEW: We now run pytest and then immediately list the files
# This will show us if report.json was created before the container exits.
CMD ["/bin/sh", "-c", "pytest --json-report --json-report-file=report.json; echo '--- File list after pytest ---'; ls -l"]