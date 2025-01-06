from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from app.database import get_db
from app.models import User, Category, Card
from app.schemas import CategoryCreate, CategoryResponse, PaginatedCardResponse

router = APIRouter()


@router.post('/', response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.id == category.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_category = Category(name=category.name, user_id=category.user_id)
    try:
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Category creation failed")


@router.get('/', response_model=List[CategoryResponse])
def get_categories(user_id=int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    categories = (
        db.query(Category)
        .filter(Category.user_id == user_id).all()
    )
    return categories


@router.get('/{category_id}/cards/', response_model=PaginatedCardResponse)
def get_cards_by_category(
    category_id: int,
    page: int = Query(0, ge=0),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Fetch cards for the specific category with related category
    cards = (
        db.query(Card)
        .filter(Card.category_id == category_id)
        .order_by(desc(Card.id))
        .offset(page * page_size)
        .limit(page_size)
        .all()
    )

    # Get total count of cards for this specific category
    total_count = db.query(Card).filter(
        Card.category_id == category_id).count()

    return {
        "cards": cards,
        "total_count": total_count,
        "current_page": page,
        "category_id": category_id
    }


@router.delete('/{category_id}')
def delete_category(category_id: int, db: Session = Depends(get_db)):

    category = db.query(Category).filter(
        Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.query(Card).filter(Card.category_id == category_id).delete()
    db.commit()

    db.query(Category).filter(Category.id == category_id).delete()
    db.commit()
