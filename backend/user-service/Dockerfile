FROM python:3.12-slim

WORKDIR /app

# Copy shared modules
COPY shared/ /app/shared/

# Copy user service
COPY user-service/ /app/user-service/

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    psycopg2-binary \
    pyjwt \
    python-dotenv \
    pydantic[email]

# Set working directory to service folder
WORKDIR /app/user-service

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
