from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Category, Card
from app.schemas import UserCreate, UserResponse, CategoryResponse, CardResponse

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        return db_user

    db_user = User(email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get('/{user_id}/categories', response_model=List[CategoryResponse])
def get_user_categories(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    categories = db.query(Category).filter(
        Category.user_id == user_id).all()
    return categories


@router.get('/{user_id}/cards', response_model=List[CardResponse])
def get_user_cards(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cards = db.query(Card).filter(Card.user_id == user_id).all()
    return cards
