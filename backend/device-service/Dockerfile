FROM python:3.12-slim

WORKDIR /app

# Copy shared modules
COPY shared/ /app/shared/

# Copy device service
COPY device-service/ /app/device-service/

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    psycopg2-binary \
    pyjwt \
    python-dotenv

# Set working directory to service folder
WORKDIR /app/device-service

# Expose port
EXPOSE 8003

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
