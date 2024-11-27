from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse
from decouple import config
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
import app.models as models
from typing import List
from app.database import engine, SessionLocal

app = FastAPI(root_path="/api")

# Detect environment
ENVIRONMENT = config("ENVIRONMENT", default="development")  # "development" or "production"

# Middleware para redirigir HTTP a HTTPS solo en producción
if ENVIRONMENT == "production":
    @app.middleware("http")
    async def https_redirect(request: Request, call_next):
        if request.url.scheme == "http" and "localhost" not in request.url.netloc:
            https_url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(https_url))

        response = await call_next(request)
        return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config('ALLOWED_ORIGINS', cast=lambda v: [
                         s.strip() for s in v.split(',')]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request/response


class CategoryBase(BaseModel):
    name: str = Field(min_length=1)


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


class CardBase(BaseModel):
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)
    category_id: int


class CardResponse(CardBase):
    id: int
    category: CategoryResponse

    class Config:
        from_attributes = True


class PaginatedCardResponse(BaseModel):
    cards: List[CardResponse]
    total_count: int
    current_page: int
    category_id: int

# Category endpoints


@app.get("/search")
def search_cards(
    query: str = Query(..., min_length=1, description="Search term"),
    page: int = Query(0, ge=0),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Calculate offset based on page number
    offset = page * page_size

    # Create base query
    search_query = f"%{query}%"
    base_query = db.query(models.Card).filter(
        # Search in both front and back fields using LIKE
        (models.Card.front.ilike(search_query)) |
        (models.Card.back.ilike(search_query))
    )

    # Get total count for pagination
    total_count = base_query.count()

    # Get paginated results
    cards = (
        base_query
        .order_by(desc(models.Card.id))
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


@app.get('/categories/{category_id}/cards/', response_model=PaginatedCardResponse)
def get_cards_by_category(
    category_id: int,
    page: int = Query(0, ge=0),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Fetch cards for the specific category with related category
    cards = (
        db.query(models.Card)
        .filter(models.Card.category_id == category_id)
        .order_by(desc(models.Card.id))
        .offset(page * page_size)
        .limit(page_size)
        .all()
    )

    # Get total count of cards for this specific category
    total_count = db.query(models.Card).filter(
        models.Card.category_id == category_id).count()

    return {
        "cards": cards,
        "total_count": total_count,
        "current_page": page,
        "category_id": category_id
    }


@app.post('/categories/', response_model=CategoryResponse)
def create_category(category: CategoryBase, db: Session = Depends(get_db)):
    db_category = models.Category(name=category.name)
    try:
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Category creation failed")


@app.get('/categories/', response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

# Card endpoints


@app.post('/cards', response_model=CardResponse)
def create_card(card: CardBase, db: Session = Depends(get_db)):
    # Check if category exists

    category = db.query(models.Category).filter(
        models.Category.id == card.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    card_model = models.Card(
        front=card.front,
        back=card.back,
        category_id=card.category_id
    )
    try:
        db.add(card_model)
        db.commit()
        db.refresh(card_model)
        return card_model
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Card creation failed")


@app.get('/all', response_model=List[CardResponse])
def get_cards(db: Session = Depends(get_db)):
    return db.query(models.Card).join(models.Category).all()


@app.get("/cards")
def get_paginated_cards(
    page: int = Query(0, ge=0),  # Page number, start at 0
    page_size: int = Query(10, ge=1, le=100)  # 10 records per page
):
    db = next(get_db())

    # Calculate offset based on page number
    offset = page * page_size

    # Fetch exactly 10 records for the current page
    cards = (
        db.query(models.Card)
        .order_by(desc(models.Card.id))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Get total count for frontend pagination
    total_count = db.query(models.Card).count()

    return {
        "cards": cards,
        "total_count": total_count,
        "current_page": page,
        "category_id": 0
    }


@app.delete('/cards/{card_id}')
def delete_info(card_id: int, db: Session = Depends(get_db)):
    card_model = db.query(models.Card).filter(
        models.Card.id == card_id).first()

    if card_model is None:
        raise HTTPException(
            status_code=400,
            detail=f"algo paso"
        )

    db.query(models.Card).filter(models.Card.id == card_id).delete()
    db.commit()


@app.delete('/categories/{category_id}')
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category_model = db.query(models.Category).filter(
        models.Category.id == category_id).first()

    if category_model is None:
        raise HTTPException(
            status_code=400,
            detail=f"algo paso"
        )

    db.query(models.Category).filter(
        models.Category.id == category_id).delete()
    db.commit()
