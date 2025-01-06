from fastapi import APIRouter, Depends, Response, HTTPException, Request
from fastapi.responses import JSONResponse
from decouple import config
import jwt
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, RefreshToken
from app.schemas import GoogleLoginRequest, LoginResponse, RefreshTokenRequest
import secrets

router = APIRouter()

ACCESS_TOKEN_SECRET = config('ACCESS_TOKEN_SECRET')
REFRESH_TOKEN_SECRET = config('REFRESH_TOKEN_SECRET')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')


def create_access_token(user, expires_delta=timedelta(minutes=15)):
    to_encode = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, ACCESS_TOKEN_SECRET, algorithm="HS256")


def create_refresh_token(user, expires_delta=timedelta(days=7)):
    # token = secrets.token_urlsafe(32)  # Genera un token más seguro

    to_encode = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + expires_delta
    }
    token = jwt.encode(to_encode, ACCESS_TOKEN_SECRET, algorithm="HS256")

    # Crear registro en base de datos
    refresh_token_entry = RefreshToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + expires_delta
    )

    db = next(get_db())
    db.add(refresh_token_entry)
    db.commit()

    return token


@router.get("/verify-session")
async def verify_session(request: Request, db: Session = Depends(get_db)):
    # Obtener token de sesión de la cookie
    session_token = request.cookies.get("session_token")
    refresh_token = request.cookies.get("refresh_token")

    if not session_token:
        return JSONResponse(
            content={"authenticated": False},
            status_code=401
        )

    try:
        # Intentar decodificar el access token
        payload = jwt.decode(
            session_token,
            ACCESS_TOKEN_SECRET,
            algorithms=["HS256"]
        )

        # Verificar si el usuario existe
        user = db.query(User).filter(User.id == payload["user_id"]).first()
        if not user:
            return JSONResponse(
                content={"authenticated": False},
                status_code=401
            )

        return JSONResponse(
            content={
                "authenticated": True,
                "user": {
                    "id": payload["user_id"],
                    "email": payload["email"]
                }
            }
        )

    except jwt.ExpiredSignatureError:
        # Si el access token ha expirado, intentar refrescar
        if not refresh_token:
            return JSONResponse(
                content={"authenticated": False},
                status_code=401
            )

        try:
            # Verificar refresh token
            refresh_token_entry = db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token,
                RefreshToken.expires_at > datetime.utcnow()
            ).first()

            if not refresh_token_entry:
                return JSONResponse(
                    content={"authenticated": False},
                    status_code=401
                )

            # Generar nuevos tokens
            user = db.query(User).filter(
                User.id == refresh_token_entry.user_id).first()

            new_access_token = create_access_token(user)
            new_refresh_token = create_refresh_token(user)

            # Invalidar el refresh token anterior
            refresh_token_entry.is_used = True
            db.commit()

            # Configurar nuevas cookies
            response = JSONResponse(
                content={
                    "authenticated": True,
                    "user": {
                        "id": user.id,
                        "email": user.email
                    }
                }
            )

            response.set_cookie(
                key="session_token",
                value=new_access_token,
                httponly=True,
                samesite="lax",
                max_age=900  # 15 minutos
            )

            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                samesite="lax",
                max_age=7*24*3600  # 7 días
            )

            return response

        except Exception:
            return JSONResponse(
                content={"authenticated": False},
                status_code=401
            )

    except jwt.InvalidTokenError:
        return JSONResponse(
            content={"authenticated": False},
            status_code=401
        )


@router.post("/refresh-token")
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        # Buscar token en base de datos
        refresh_token_entry = db.query(RefreshToken).filter(
            RefreshToken.token == request.refresh_token,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()

        if not refresh_token_entry:
            raise HTTPException(
                status_code=401, detail="Token inválido o expirado")

        # Obtener usuario asociado
        user = db.query(User).filter(
            User.id == refresh_token_entry.user_id).first()

        if not user:
            raise HTTPException(
                status_code=404, detail="Usuario no encontrado")

        # Invalidar el refresh token actual
        refresh_token_entry.is_used = True
        db.commit()

        # Generar nuevos tokens
        new_access_token = create_access_token(user)
        new_refresh_token = create_refresh_token(user)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/login")
async def google_login(
    request: dict,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        # Tu lógica de verificación de Google existente aquí...
        token = request.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
        
        try:
            # Verify the token with Google
            id_info = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )
            
            # Check if the token is issued by Google
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')
                
            # Extract user info from verified token
            user_info = {
                "email": id_info.get("email"),
                "name": id_info.get("name"),
                "picture": id_info.get("picture")
            }
            
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid token")

        db_user = db.query(User).filter(
            User.email == user_info['email']).first()
        
        if db_user:
            access_token = create_access_token(db_user)
            refresh_token = create_refresh_token(db_user)

            response.set_cookie(
                key="session_token",
                value=refresh_token,
                httponly=True,
                samesite="lax",
                max_age=900
            )

            return {
                'userInfo': db_user,
                'accessToken': access_token,
            }

        db_user = User(email=user_info['email'])
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        access_token = create_access_token(db_user)
        refresh_token = create_refresh_token(db_user)
        response.set_cookie(
            key="session_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            max_age=900  # 15 minutos
        )
        return {
            'userInfo': db_user,
            'accessToken': access_token,
        }

        # Después de verificar el usuario, generar tokens

    except ValueError:
        raise HTTPException(status_code=403, detail="Token inválido")
