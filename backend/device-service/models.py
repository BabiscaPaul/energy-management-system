from shared.database import Base
from sqlalchemy import Column, Integer, String

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    max_consumption_value = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False, index=True) 