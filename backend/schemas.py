from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("A senha deve ter no mínimo 6 caracteres")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("O nome não pode estar vazio")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ReadingItem(BaseModel):
    index: int
    reading: str
    category: str
    completed: bool = False


class DayData(BaseModel):
    date: str
    readings: List[ReadingItem]


class ProgressResponse(BaseModel):
    total: int
    done: int
    pct: float
    days_left: int
    per_day_today: int
    streak: int
    today: DayData
    future: dict  # date → list of readings


class ToggleRequest(BaseModel):
    reading_index: int


class ToggleResponse(BaseModel):
    reading_index: int
    completed: bool
    day_complete: bool
    streak: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("A senha deve ter no mínimo 6 caracteres")
        return v


class MessageResponse(BaseModel):
    message: str
