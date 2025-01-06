from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List


class GoogleLoginRequest(BaseModel):
    token: str


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pass


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    # Configura el modelo para trabajar con instancias de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str


class LoginResponse(BaseModel):
    userInfo: UserResponse
    accessToken: str


class CategoryBase(BaseModel):
    name: str = Field(min_length=1)


class CategoryCreate(CategoryBase):
    user_id: int


class CategoryResponse(CategoryBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class CardBase(BaseModel):
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)
    category_id: int


class CardCreate(CardBase):
    user_id: int


class CardResponse(CardBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class PaginatedCardResponse(BaseModel):
    cards: List[CardResponse]
    total_count: int
    current_page: int
    category_id: int
