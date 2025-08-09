FROM python:3.9-slim

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


# The '&&' ensures that if the compile check fails, the container will
# exit immediately with an error, giving us a much clearer failure message.
CMD ["/bin/sh", "-c", "python -m py_compile app.py && python app.py & sleep 2; pytest --json-report --json-report-file=report.json && echo '--- Pytest finished ---'"]