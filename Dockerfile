# Use the official lightweight Python image.
FROM python:3.13-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED=1

# Create and change to the app directory.
WORKDIR /app

# Copy application dependency manifests to the container image.
COPY requirements.txt requirements.txt

# Install dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy local code to the container image.
COPY . .

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 unityaid.wsgi:application
