FROM python:3.12-slim

WORKDIR /app

# Copy shared modules first
COPY shared/ /app/shared/

# Copy gateway service
COPY gateway-service/ /app/gateway-service/

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    httpx \
    pyjwt \
    python-dotenv \
    pydantic[email]

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "gateway-service.main:app", "--host", "0.0.0.0", "--port", "8000"]
