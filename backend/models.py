# backend/models.py

from typing import Optional
from pydantic import BaseModel

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