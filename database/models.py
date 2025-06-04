from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Text, TIMESTAMP, ForeignKey
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
