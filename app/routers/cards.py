from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import User, Category, Card
from app.schemas import CardResponse, CardCreate

router = APIRouter()


@router.post('/', response_model=CardResponse)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == card.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if category exists and belongs to the user
    category = db.query(Category).filter(
        Category.id == card.category_id,
        Category.user_id == card.user_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=404, detail="Category not found or does not belong to user")

    card_model = Card(
        front=card.front,
        back=card.back,
        category_id=card.category_id,
        user_id=card.user_id
    )
    try:
        db.add(card_model)
        db.commit()
        db.refresh(card_model)
        return card_model
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Card creation failed")


@router.get("/")
def get_paginated_cards(
    page: int = Query(0, ge=0),
    page_size: int = Query(10, ge=1, le=100),
    user_id=int
):
    db = next(get_db())

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    offset = page * page_size

    cards = (
        db.query(Card)
        .filter(Card.user_id == user_id)
        .order_by(desc(Card.id))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_count = db.query(Card).count()

    return {
        "cards": cards,
        "total_count": total_count,
        "current_page": page,
    }


@router.delete('/{card_id}')
def delete_info(card_id: int, db: Session = Depends(get_db)):
    card_model = db.query(Card).filter(
        Card.id == card_id).first()

    if card_model is None:
        raise HTTPException(
            status_code=400,
            detail=f"algo paso"
        )

    db.query(Card).filter(Card.id == card_id).delete()
    db.commit()
