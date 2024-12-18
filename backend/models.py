# backend/models.py

from typing import Optional
from pydantic import BaseModel
from datetime import datetime
class User(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    role_id: int
    role_name: str

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Booking(BaseModel):
    booking_id: int
    user_id: int
    resource_id: int
    start_time: datetime
    end_time: datetime
    status: str  # 'active', 'completed', 'cancelled'

    class Config:
        orm_mode = True

class BookingCreate(BaseModel):
    user_id: int
    resource_id: int
    start_time: datetime
    end_time: datetime
    status: str = "active"  # По умолчанию статус 'active'

class Resource(BaseModel):
    resource_id: Optional[int] = None  # ID ресурса, может отсутствовать при создании
    name: str  # Название ресурса
    description: Optional[str] = None  # Описание ресурса
    hourly_rate: float

    class Config:
        orm_mode = True

class ResourceCreate(BaseModel):
    name: str
    description: Optional[str]
    hourly_rate: float  # Новый атрибут для создания ресурса

class SessionCreate(BaseModel):
    user_id: int
    start_time: datetime

class Session(BaseModel):
    session_id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None

class PaymentCreate(BaseModel):
    user_id: int
    amount: float
    payment_date: datetime

class Payment(BaseModel):
    payment_id: int
    user_id: int
    amount: float
    payment_date: datetime