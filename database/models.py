from sqlalchemy import Column, DateTime, Integer, BigInteger, String, Boolean, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String)
    amazon_authorized = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class GoogleToken(Base):
    __tablename__ = 'google_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_type = Column(String)
    expiry = Column(TIMESTAMP)
    scope = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class AmazonToken(Base):
    __tablename__ = 'amazon_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    role_arn = Column(String)
    seller_id = Column(String)
    client_id = Column(String)
    client_secret = Column(String)
    expiry = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class TodoistToken(Base):
    __tablename__ = 'todoist_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expiry = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True)
    asin = Column(String(255), nullable=False)
    review_id = Column(String(255), unique=True, nullable=False)
    title = Column(Text)
    rating = Column(String(255))
    text = Column(Text)
    review_date = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    asin = Column(String(255), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())