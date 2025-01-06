from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from decouple import config
import app.models as models
from app.database import engine
from app.routers import auth, users, categories, cards, search, admin


app = FastAPI(root_path="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config('ALLOWED_ORIGINS', cast=lambda v: [
                         s.strip().rstrip('/') for s in v.split(',')]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(categories.router, prefix="/categories",
                   tags=["Categories"])
app.include_router(cards.router, prefix="/cards", tags=["Cards"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
