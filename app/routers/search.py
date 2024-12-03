from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Card

router = APIRouter()


@router.get("/")
def search_cards(
    query: str = Query(..., min_length=1, description="Search term"),
    page: int = Query(0, ge=0),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):

    offset = page * page_size

    search_query = f"%{query}%"
    base_query = db.query(Card).filter(
        # Search in both front and back fields using LIKE
        (Card.front.ilike(search_query)) |
        (Card.back.ilike(search_query))
    )

    total_count = base_query.count()

    cards = (
        base_query
        .order_by(desc(Card.id))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "cards": cards,
        "total_count": total_count,
        "current_page": page,
        "search_term": query
    }
