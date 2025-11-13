from database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True) 
    full_name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True, nullable=True)
    address = Column(String, nullable=True)