from sqlalchemy.orm import Session
from database.models import User, GoogleToken, AmazonToken, TodoistToken

def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, name: str = "") -> User:
    user = User(telegram_id=telegram_id, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_or_update_user(db, telegram_id: str, name: str, authorized: bool):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.name = name
        user.amazon_authorized = authorized
    else:
        user = User(
            telegram_id=telegram_id,
            name=name,
            amazon_authorized=authorized
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authorize_user(db: Session, telegram_id: int):
    user = get_user_by_telegram_id(db, telegram_id)
    if user:
        user.amazon_authorized = True
        db.commit()
        return user
    return None

def store_google_token(db: Session, user_id: int, token_data: dict):
    token = GoogleToken(user_id=user_id, **token_data)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token

def store_amazon_token(db: Session, user_id: int, token_data: dict):
    token = AmazonToken(user_id=user_id, **token_data)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token

def store_todoist_token(db: Session, user_id: int, token_data: dict):
    token = TodoistToken(user_id=user_id, **token_data)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token
