import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr
from shared.types import RoleEnum

load_dotenv(Path(__file__).parent.parent / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8002")
DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://device-service:8003")

app = FastAPI(title="API Gateway", version="1.0.0")
security = HTTPBearer()

# schemas

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: RoleEnum = RoleEnum.CLIENT
    email: EmailStr
    full_name: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

class DeviceCreateRequest(BaseModel):
    name: str
    max_consumption_value: int
    user_id: int

class DeviceUpdateRequest(BaseModel):
    name: Optional[str] = None
    max_consumption_value: Optional[int] = None
    user_id: Optional[int] = None


# helper functions

def validate_token(token: str) -> dict:
    """Validate JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    return validate_token(token)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role"""
    if current_user.get("role") != RoleEnum.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def call_service(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make HTTP call to a microservice"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, timeout=10.0, **kwargs)
            response.raise_for_status()
            return {"status_code": response.status_code, "data": response.json()}
        except httpx.HTTPStatusError as e:
            return {"status_code": e.response.status_code, "error": e.response.text}
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/")
def root():
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "description": "Orchestrates all microservices with centralized auth and data consistency",
        "endpoints": {
            "auth": "/api/auth/*",
            "users": "/api/users/*",
            "devices": "/api/devices/*"
        }
    }

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "api-gateway"}

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    """
    Orchestrated registration: Creates user in auth-service AND user-service
    to maintain database consistency
    """
    # Step 1: Register in auth-service
    auth_result = await call_service(
        "POST",
        f"{AUTH_SERVICE_URL}/register",
        json={
            "username": data.username,
            "password": data.password,
            "role": data.role.value
        }
    )
    
    if auth_result.get("status_code") != 201:
        raise HTTPException(
            status_code=auth_result.get("status_code", 500),
            detail=auth_result.get("error", "Registration failed")
        )
    
    auth_data = auth_result["data"]
    user_id = auth_data.get("user_id")
    
    # Step 2: Create user profile in user-service with the SAME user_id
    user_result = await call_service(
        "POST",
        f"{USER_SERVICE_URL}/users",
        json={
            "id": user_id,  # Same ID from auth database
            "full_name": data.full_name,
            "email": data.email,
            "phone_number": None,
            "address": None
        },
        headers={"Authorization": f"Bearer {auth_data['access_token']}"}
    )
    
    # If user profile creation fails, we should rollback (future enhancement: use transactions)
    if user_result.get("status_code") not in [200, 201]:
        # Log error but still return auth token since user exists in auth DB
        print(f"Warning: User profile creation failed for user_id {user_id}")
    
    return auth_data


@app.post("/api/auth/login")
async def login(data: LoginRequest):
    """Forward login to auth-service"""
    result = await call_service(
        "POST",
        f"{AUTH_SERVICE_URL}/login",
        json=data.dict()
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Login failed")
        )
    
    return result["data"]


# endpoints

@app.get("/api/users")
async def get_all_users(current_user: dict = Depends(require_admin)):
    """Get all users (admin only)"""
    result = await call_service(
        "GET",
        f"{USER_SERVICE_URL}/users"
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Failed to fetch users")
        )
    
    return result["data"]


@app.get("/api/users/{user_id}")
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get user by ID"""
    # Check authorization: admin or own profile
    if current_user.get("role") != RoleEnum.ADMIN.value and current_user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await call_service(
        "GET",
        f"{USER_SERVICE_URL}/users/{user_id}"
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "User not found")
        )
    
    return result["data"]


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, data: UserUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    # Check authorization: admin or own profile
    if current_user.get("role") != RoleEnum.ADMIN.value and current_user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await call_service(
        "PUT",
        f"{USER_SERVICE_URL}/users/{user_id}",
        json=data.dict(exclude_none=True)
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Update failed")
        )
    
    return result["data"]


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Orchestrated deletion: Deletes user from all services
    Cascade: devices -> user profile -> auth
    """
    # Check authorization: admin or own account
    if current_user.get("role") != RoleEnum.ADMIN.value and current_user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Step 1: Get and delete all user's devices
    devices_result = await call_service(
        "GET",
        f"{DEVICE_SERVICE_URL}/devices/user/{user_id}"
    )
    
    if devices_result.get("status_code") == 200:
        devices = devices_result["data"]
        for device in devices:
            await call_service(
                "DELETE",
                f"{DEVICE_SERVICE_URL}/devices/{device['id']}"
            )
    
    # Step 2: Delete user profile
    await call_service(
        "DELETE",
        f"{USER_SERVICE_URL}/users/{user_id}"
    )
    
    # Note: We don't delete from auth-service to preserve audit trail
    # In production, you might want to add a "deleted" flag instead
    
    return {"message": "User and all associated data deleted successfully", "id": user_id}


# ============= DEVICE ENDPOINTS =============

@app.post("/api/devices")
async def create_device(data: DeviceCreateRequest, current_user: dict = Depends(require_admin)):
    """Create device (admin only)"""
    result = await call_service(
        "POST",
        f"{DEVICE_SERVICE_URL}/devices",
        json=data.dict()
    )
    
    if result.get("status_code") != 201:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Device creation failed")
        )
    
    return result["data"]


@app.get("/api/devices")
async def get_all_devices(current_user: dict = Depends(require_admin)):
    """Get all devices (admin only)"""
    result = await call_service(
        "GET",
        f"{DEVICE_SERVICE_URL}/devices"
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Failed to fetch devices")
        )
    
    return result["data"]


@app.get("/api/devices/{device_id}")
async def get_device(device_id: int, current_user: dict = Depends(get_current_user)):
    """Get device by ID"""
    result = await call_service(
        "GET",
        f"{DEVICE_SERVICE_URL}/devices/{device_id}"
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Device not found")
        )
    
    device = result["data"]
    
    # Check authorization: admin or device owner
    if current_user.get("role") != RoleEnum.ADMIN.value and current_user.get("user_id") != device.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return device


@app.get("/api/devices/user/{user_id}")
async def get_user_devices(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get devices for a specific user"""
    # Check authorization: admin or own devices
    if current_user.get("role") != RoleEnum.ADMIN.value and current_user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await call_service(
        "GET",
        f"{DEVICE_SERVICE_URL}/devices/user/{user_id}"
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Failed to fetch devices")
        )
    
    return result["data"]


@app.put("/api/devices/{device_id}")
async def update_device(device_id: int, data: DeviceUpdateRequest, current_user: dict = Depends(require_admin)):
    """Update device (admin only)"""
    result = await call_service(
        "PUT",
        f"{DEVICE_SERVICE_URL}/devices/{device_id}",
        json=data.dict(exclude_none=True)
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Update failed")
        )
    
    return result["data"]


@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: int, current_user: dict = Depends(require_admin)):
    """Delete device (admin only)"""
    result = await call_service(
        "DELETE",
        f"{DEVICE_SERVICE_URL}/devices/{device_id}"
    )
    
    if result.get("status_code") != 200:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail=result.get("error", "Deletion failed")
        )
    
    return result["data"]
