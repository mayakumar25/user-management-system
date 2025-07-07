from sqlalchemy import Column, Integer, String, Boolean
from models.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String)
    password = Column(String)
    role = Column(String, default="user")  # user or admin
    department = Column(String, default="")
    college = Column(String, default="")
    profile_photo = Column(String, default="")
    can_edit = Column(Boolean, default=False)
