from sqlalchemy.orm import Session
from models.models import User
from models.schemas import UserCreate, UserUpdate

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        username=user.username,
        password=user.password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_users(db: Session):
    return db.query(User).all()

def get_user_count(db: Session):
    return db.query(User).count()

def update_user(db: Session, user_id: int, update_data: dict):
    user = get_user_by_id(db, user_id)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

def set_edit_permission(db: Session, user_id: int, can_edit: bool):
    user = get_user_by_id(db, user_id)
    user.can_edit = can_edit
    db.commit()
    db.refresh(user)
    return user
