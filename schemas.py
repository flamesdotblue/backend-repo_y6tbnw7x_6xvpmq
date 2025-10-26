"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

# Example schemas (you can keep or remove if not needed)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Auth-related schemas for OTP login flow
class AuthUser(BaseModel):
    """
    Authentication users collection
    Collection name: "authuser"
    """
    email: EmailStr = Field(..., description="User email")
    display_name: Optional[str] = Field(None, description="Display name")
    is_verified: bool = Field(default=True, description="Email verified via OTP")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")

class Otp(BaseModel):
    """
    OTP requests collection
    Collection name: "otp"
    """
    email: EmailStr = Field(..., description="Email where the OTP is sent")
    code: str = Field(..., min_length=4, max_length=10, description="One-time passcode")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    used: bool = Field(default=False, description="Whether the OTP has been used")
