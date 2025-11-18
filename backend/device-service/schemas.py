from pydantic import BaseModel
from typing import Optional

class DeviceBase(BaseModel):
    name: str
    max_consumption_value: int

class DeviceCreate(DeviceBase):
    user_id: int

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    max_consumption_value: Optional[int] = None
    user_id: Optional[int] = None
    
class DeviceResponse(DeviceBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True
