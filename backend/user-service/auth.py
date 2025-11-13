import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv
from shared.types import RoleEnum

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    
    return {
        "username": payload.get("sub"),
        "role": payload.get("role")
    }


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != RoleEnum.ADMIN.value: 
        raise HTTPException(
            status_code=403, 
            detail="Admin access required. Only administrators can perform this action."
        )
    return current_user
