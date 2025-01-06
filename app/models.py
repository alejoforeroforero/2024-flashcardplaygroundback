from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    refresh_tokens = relationship(
        "RefreshToken", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    categories = relationship("Category", back_populates="user")
    cards = relationship("Card", back_populates="user")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")

class Category(Base):
    __tablename__ = "categories" 
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, unique=True) 
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="categories")
    cards = relationship("Card", back_populates="category")

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    front = Column(String, index=True)
    back = Column(String)
    
    category = relationship("Category", back_populates="cards")
    user = relationship("User", back_populates="cards")

