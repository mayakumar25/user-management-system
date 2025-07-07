from models.database import SessionLocal
from models.models import User
from services.auth import hash_password

# Start DB session
db = SessionLocal()

# Admin details
admin_email = "admin@123gmail.com"
admin_password = "admin123"

# Check if already exists
existing_admin = db.query(User).filter(User.email == admin_email).first()

if not existing_admin:
    admin_user = User(
        email=admin_email,
        username="Admin",
        password=hash_password(admin_password),
        role="admin",
        department="Admin Department",
        college="Admin College",
        profile_photo="static/uploads/default.png"  # required
    )
    db.add(admin_user)
    db.commit()
    print("✅ Admin created successfully.")
else:
    print("ℹ️ Admin already exists.")

db.close()
