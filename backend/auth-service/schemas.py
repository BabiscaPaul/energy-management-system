from pydantic import BaseModel
from models import RoleEnum

class UserRegister(BaseModel):
    username: str
    password: str
    role: RoleEnum = RoleEnum.CLIENT # defaults to client

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str 
    token_type: str