from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models.database import Base, engine, SessionLocal
from routes import router  # your main router file (the one with login, register, etc.)
from services.auth import hash_password
from services.crud import get_user_by_email, create_user
from models.schemas import UserCreate

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(router.router)

# --- Create Admin User on Startup ---
def create_admin_if_not_exists():
    db = SessionLocal()
    try:
        admin = get_user_by_email(db, "admin@123gmail.com")
        if not admin:
            create_user(db, UserCreate(
                email="admin@123gmail.com",
                username="Admin",
                password=hash_password("admin123"),
                role="admin"
            ))
            print(" Admin user created.")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

# Call this function once when the app starts
create_admin_if_not_exists()
