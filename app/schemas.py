from pydantic import BaseModel, Field, EmailStr
from typing import List

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

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