from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    categories = relationship("Category", back_populates="user")
    cards = relationship("Card", back_populates="user")

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

