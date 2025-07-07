import shutil
import os
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from models.database import SessionLocal
from models.models import User
from models.schemas import UserCreate
from services.auth import create_access_token, verify_password, hash_password, SECRET_KEY, ALGORITHM
import services.crud as crud

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    return crud.get_user_by_email(db, email)

# --- Register Page ---
@router.get("/register-page", response_class=HTMLResponse)
def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register-page")
def register_user(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = crud.get_user_by_email(db, email=email)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "msg": "Email already exists."
        })

    hashed_pw = hash_password(password)
    user = crud.create_user(db, UserCreate(email=email, username=username, password=hashed_pw))
    response = RedirectResponse(url="/login", status_code=302)
    return response

# --- Login Page ---
@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "msg": "Invalid credentials"
        })

    token = create_access_token({"sub": user.email})

    if user.role == "admin":
        redirect_url = "/admin/settings"
    else:
        redirect_url = "/home"

    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

# --- User Form Submission ---
@router.get("/form", response_class=HTMLResponse)
def show_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("form.html", {"request": request, "user": user})

@router.post("/form")
def submit_form(
    request: Request,
    username: str = Form(...),
    department: str = Form(...),
    college: str = Form(...),
    profile_photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    os.makedirs("static/uploads", exist_ok=True)
    file_location = f"static/uploads/{profile_photo.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(profile_photo.file, f)

    crud.update_user(db, user.id, {
        "username": username,
        "department": department,
        "college": college,
        "profile_photo": file_location
    })

    return RedirectResponse(url="/home", status_code=302)

# --- Home Page ---
@router.get("/home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    user_count = db.query(User).filter(User.email != "admin@123gmail.com").count()
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
        "count": user_count
    })

# --- Profile Page ---
@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    users = db.query(User).filter(User.email != "admin@123gmail.com").all()
    total_users = len(users)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "users": users,
        "user": user,
        "total_users": total_users
    })

# --- Edit Page (GET) ---
@router.get("/edit", response_class=HTMLResponse)
def edit_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.can_edit:
        return RedirectResponse(url="/profile")

    return templates.TemplateResponse("edit.html", {
        "request": request,
        "user": user
    })
# --- Management Page ---
@router.get("/management", response_class=HTMLResponse)
def management(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    # Exclude the admin from the users list
    users = db.query(User).filter(User.email != "admin@123gmail.com").all()
    total_users = len(users)

    return templates.TemplateResponse("management.html", {
        "request": request,
        "user": user,
        "users": users,
        "total_users": total_users
    })

# --- Edit Submission (POST) ---
@router.post("/edit")
def edit_user_data(
    request: Request,
    username: str = Form(...),
    department: str = Form(...),
    college: str = Form(...),
    profile_photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or not user.can_edit:
        return RedirectResponse(url="/profile")

    os.makedirs("static/uploads", exist_ok=True)
    file_location = f"static/uploads/{profile_photo.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(profile_photo.file, f)

    crud.update_user(db, user.id, {
        "username": username,
        "department": department,
        "college": college,
        "profile_photo": file_location
    })

    return RedirectResponse(url="/profile", status_code=302)

# --- Logout ---
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token", path="/")
    return response

# --- Admin Settings Page ---
@router.get("/admin/settings", response_class=HTMLResponse)
def admin_settings(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login")

    users = db.query(User).filter(User.email != "admin@123gmail.com").all()
    total_users = len(users)

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "users": users,
        "total_users": total_users
    })

@router.post("/admin/permission")
def grant_permission(
    user_id: int = Form(...),
    can_edit: str = Form(...),
    db: Session = Depends(get_db)
):
    can_edit_flag = can_edit.lower() == "true"
    crud.set_edit_permission(db, user_id, can_edit_flag)
    return RedirectResponse(url="/admin/settings", status_code=302)
