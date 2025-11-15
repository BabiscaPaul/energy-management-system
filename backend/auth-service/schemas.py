from pydantic import BaseModel
from shared.types import RoleEnum

class UserRegister(BaseModel):
    username: str
    password: str
    role: RoleEnum = RoleEnum.CLIENT

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str 
    token_type: str
    user_id: int | None = None 