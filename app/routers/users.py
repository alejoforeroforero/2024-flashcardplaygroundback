from fastapi import APIRouter, Depends, Response, HTTPException, Request
from fastapi.responses import JSONResponse
from decouple import config
from typing import List
import jwt
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Category, Card, RefreshToken
from app.schemas import GoogleLoginRequest, CategoryResponse, CardResponse, LoginResponse, RefreshTokenRequest, UserResponse, UserCreate
import secrets

router = APIRouter()

# @router.post("/", response_model=LoginResponse)
# async def google_login(
#     request: GoogleLoginRequest,
#     response: Response,
#     db: Session = Depends(get_db),
# ):
#     try:
#         id_info = id_token.verify_oauth2_token(
#             request.token,
#             requests.Request(),
#             config('GOOGLE_CLIENT_ID')
#         )

#         if 'email' not in id_info or not id_info['email']:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No se proporcionó un correo electrónico válido"
#             )

#         user_info = {
#             "email": id_info['email'],
#         }

#         db_user = db.query(User).filter(
#             User.email == user_info['email']).first()

#         if db_user:
#             token = create_token(db_user)
#             access_token = create_access_token(db_user)
#             refresh_token = create_refresh_token(db_user)
#             create_cookie(token, response)
#             return {
#                 'userInfo': db_user,
#                 'accessToken': access_token
#             }

#         db_user = User(email=user_info['email'])
#         db.add(db_user)
#         db.commit()
#         db.refresh(db_user)
#         token = create_token(db_user)
#         create_cookie(token, response)
#         return {
#             'userInfo': db_user,
#             'accessToken': token
#         }

#     except ValueError:
#         raise HTTPException(status_code=403, detail="Token inválido")



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
