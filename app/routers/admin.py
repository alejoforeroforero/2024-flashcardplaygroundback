from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Card, Category, User
from app.schemas import CardResponse, UserResponse

router = APIRouter()

@router.get('/cards', response_model=List[CardResponse])
def get_cards(db: Session = Depends(get_db)):
    return db.query(Card).join(Category).all()

@router.get('/users', response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()