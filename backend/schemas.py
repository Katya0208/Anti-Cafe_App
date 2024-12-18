from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    role_id: int
    role_name: str

    class Config:
        orm_mode = True

from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class BookingCreate(BaseModel):
    resource_id: int
    start_time: datetime
    end_time: datetime
    status: str

class Booking(BaseModel):
    booking_id: int
    user_id: int
    resource_id: int
    start_time: datetime
    end_time: datetime
    status: str

