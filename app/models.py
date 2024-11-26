from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    __tablename__ = "categories"  

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, unique=True) 
    cards = relationship("Card", back_populates="category")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    front = Column(String, index=True)
    back = Column(String)
    category = relationship("Category", back_populates="cards")
