FROM python:3.11-slim

WORKDIR /app

# Install dependencies into the system environment
# We install pipenv, then use it to install the packages we need
RUN pip install --no-cache-dir pipenv
RUN pipenv install fastapi uvicorn valkey python-keycloak requests --system --skip-lock

# Copy the rest of the application
COPY api-server/ /app/

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
