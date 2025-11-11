from fastapi import FastAPI

app = FastAPI(title="Auth Service")

@app.get("/")
def read_root():
    return {"service": "auth-service", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}