
# from fastapi import FastAPI, Depends, HTTPException, status, Request
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta
# from typing import Optional, List
# from jose import jwt, JWTError
# # import jwt
# from passlib.context import CryptContext
# from pydantic import BaseModel, EmailStr
# import os

# # Database imports (adjust based on your setup)
# from database import SessionLocal, engine
# import models

# # JWT Settings
# SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# # Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # OAuth2 scheme
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# # Create FastAPI app
# app = FastAPI(title="Employee Portal API")

# # CORS configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "http://localhost:3000",
#         "http://127.0.0.1:5173",
#         "http://127.0.0.1:3000"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ============================================
# # DATABASE DEPENDENCY
# # ============================================

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # ============================================
# # PYDANTIC MODELS
# # ============================================

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     email: Optional[str] = None

# class UserCreate(BaseModel):
#     email: EmailStr
#     full_name: str
#     password: str
#     role: str = "employee"
#     department: Optional[str] = None

# class UserResponse(BaseModel):
#     id: int
#     email: str
#     full_name: str
#     role: str
#     department: Optional[str]
#     is_active: bool
#     created_at: datetime

#     class Config:
#         from_attributes = True

# # ============================================
# # AUTHENTICATION UTILITIES
# # ============================================

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a password against a hash"""
#     return pwd_context.verify(plain_password, hashed_password)

# def get_password_hash(password: str) -> str:
#     """Hash a password"""
#     return pwd_context.hash(password)

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     """Create JWT access token"""
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     """Get current user from JWT token"""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
    
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token has expired",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except jwt.JWTError:
#         raise credentials_exception
    
#     user = db.query(models.User).filter(models.User.email == email).first()
#     if user is None:
#         raise credentials_exception
    
#     return user

# # ============================================
# # AUTH ENDPOINTS
# # ============================================

# @app.post("/api/auth/login", response_model=Token)
# async def login(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     """Login endpoint"""
#     # Find user by email (username field contains email)
#     user = db.query(models.User).filter(
#         models.User.email == form_data.username
#     ).first()
    
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     if not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="User account is inactive"
#         )
    
#     # Create access token
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
    
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.post("/api/auth/register", response_model=UserResponse)
# async def register(user_data: UserCreate, db: Session = Depends(get_db)):
#     """Register new user"""
#     # Check if user already exists
#     existing_user = db.query(models.User).filter(
#         models.User.email == user_data.email
#     ).first()
    
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     # Create new user
#     new_user = models.User(
#         email=user_data.email,
#         full_name=user_data.full_name,
#         password_hash=get_password_hash(user_data.password),
#         role=user_data.role,
#         department=user_data.department,
#         is_active=True
#     )
    
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
    
#     return new_user

# @app.get("/api/auth/me", response_model=UserResponse)
# async def get_me(current_user: models.User = Depends(get_current_user)):
#     """Get current user info"""
#     return current_user

# # ============================================
# # JOBS ENDPOINTS
# # ============================================

# @app.get("/api/jobs")
# async def get_jobs(
#     current_user: models.User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all jobs"""
#     jobs = db.query(models.JobPosting).all()
    
#     # Add referral count to each job
#     result = []
#     for job in jobs:
#         job_dict = {
#             "id": job.id,
#             "title": job.job_title,
#             "description": job.description,
#             "department": job.department,
#             "location": job.location,
#             "experience_required": job.experience_required,
#             "skills_required": job.skills_required,
#             "status": job.status,
#             "created_by": job.created_by,
#             "created_at": job.created_at,
#             "updated_at": job.updated_at,
#             "referral_count": db.query(models.Referral).filter(
#                 models.Referral.job_id == job.id
#             ).count()
#         }
#         result.append(job_dict)
    
#     return result

# @app.get("/api/jobs/{job_id}")
# async def get_job(
#     job_id: int,
#     current_user: models.User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get single job by ID"""
#     job = db.query(models.Job).filter(models.Job.id == job_id).first()
    
#     if not job:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Job not found"
#         )
    
#     # Add referral count
#     referral_count = db.query(models.Referral).filter(
#         models.Referral.job_id == job.id
#     ).count()
    
#     job_dict = {
#         "id": job.id,
#         "title": job.title,
#         "description": job.description,
#         "department": job.department,
#         "location": job.location,
#         "experience_required": job.experience_required,
#         "skills_required": job.skills_required,
#         "status": job.status,
#         "created_by": job.created_by,
#         "created_at": job.created_at,
#         "updated_at": job.updated_at,
#         "referral_count": referral_count
#     }
    
#     return job_dict

# # ============================================
# # REFERRALS ENDPOINTS
# # ============================================

# @app.get("/api/referrals")
# async def get_referrals(
#     current_user: models.User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all referrals (admin/hr/hiring_manager) or user's own referrals"""
    
#     # Admin, HR, and Hiring Manager can see all referrals
#     if current_user.role in ["hr", "hiring_manager", "admin"]:
#         referrals = db.query(models.Referral).all()
#     else:
#         # Regular employees see only their own referrals
#         referrals = db.query(models.Referral).filter(
#             models.Referral.referred_by == current_user.id
#         ).all()
    
#     # Enhance with job details
#     result = []
#     for ref in referrals:
#         job = db.query(models.Job).filter(models.Job.id == ref.job_id).first()
#         ref_dict = {
#             "id": ref.id,
#             "job_id": ref.job_id,
#             "job_title": job.title if job else "N/A",
#             "candidate_name": ref.candidate_name,
#             "candidate_email": ref.candidate_email,
#             "candidate_phone": ref.candidate_phone,
#             "candidate_linkedin": ref.candidate_linkedin,
#             "resume_path": ref.resume_path,
#             "status": ref.status,
#             "referred_by": ref.referred_by,
#             "submitted_at": ref.submitted_at,
#             "updated_at": ref.updated_at,
#             "notes": ref.notes
#         }
#         result.append(ref_dict)
    
#     return result

# @app.get("/api/referrals/my-referrals")
# async def get_my_referrals(
#     current_user: models.User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get current user's referrals"""
#     referrals = db.query(models.Referral).filter(
#         models.Referral.referred_by == current_user.id
#     ).all()
    
#     # Enhance with job details
#     result = []
#     for ref in referrals:
#         job = db.query(models.Job).filter(models.Job.id == ref.job_id).first()
#         ref_dict = {
#             "id": ref.id,
#             "job_id": ref.job_id,
#             "job_title": job.title if job else "N/A",
#             "candidate_name": ref.candidate_name,
#             "candidate_email": ref.candidate_email,
#             "candidate_phone": ref.candidate_phone,
#             "candidate_linkedin": ref.candidate_linkedin,
#             "resume_path": ref.resume_path,
#             "status": ref.status,
#             "referred_by": ref.referred_by,
#             "submitted_at": ref.submitted_at,
#             "updated_at": ref.updated_at,
#             "notes": ref.notes
#         }
#         result.append(ref_dict)
    
#     return result

# # ============================================
# # ASSETS ENDPOINTS (INVENTORY)
# # ============================================

# @app.get("/api/assets")
# async def get_assets(
#     current_user: models.User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all assets"""
#     assets = db.query(models.Asset).all()
    
#     # Enhance with assigned user details
#     result = []
#     for asset in assets:
#         assigned_user = None
#         if asset.assigned_to:
#             assigned_user = db.query(models.User).filter(
#                 models.User.id == asset.assigned_to
#             ).first()
        
#         asset_dict = {
#             "id": asset.id,
#             "serial_number": asset.serial_number,
#             "category": asset.category,
#             "model": asset.model,
#             "manufacturer": asset.manufacturer,
#             "purchase_date": asset.purchase_date,
#             "warranty_expiry": asset.warranty_expiry,
#             "status": asset.status,
#             "assigned_to": asset.assigned_to,
#             "assigned_to_name": assigned_user.full_name if assigned_user else None,
#             "department": assigned_user.department if assigned_user else None,
#             "location": asset.location,
#             "notes": asset.notes,
#             "created_at": asset.created_at,
#             "updated_at": asset.updated_at
#         }
#         result.append(asset_dict)
    
#     return result

# # ============================================
# # HEALTH CHECK
# # ============================================

# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {
#         "status": "online",
#         "message": "Employee Portal API is running",
#         "version": "1.0.0"
#     }

# @app.get("/api/health")
# async def health_check():
#     """Detailed health check"""
#     return {
#         "status": "healthy",
#         "timestamp": datetime.utcnow(),
#         "database": "connected"
#     }

# # ============================================
# # RUN SERVER
# # ============================================

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Fixed main.py - Matches your actual database schema
File: C:\Office\employee_backend\main.py
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os

# Database imports
from database import SessionLocal, engine
import models

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create FastAPI app
app = FastAPI(title="Employee Portal API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DATABASE DEPENDENCY
# ============================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# PYDANTIC MODELS
# ============================================

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "employee"
    department: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================
# AUTHENTICATION UTILITIES
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # ✅ FIXED: Use correct field name 'hashed_password'
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

# ============================================
# AUTH ENDPOINTS
# ============================================

@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint"""
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()
    
    # ✅ FIXED: Use 'hashed_password' instead of 'password_hash'
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # ✅ FIXED: Use 'hashed_password' field
    new_user = models.User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        department=user_data.department,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# ============================================
# JOBS ENDPOINTS
# ============================================

@app.get("/api/jobs")
async def get_jobs(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all jobs"""
    # ✅ FIXED: Use JobPosting model
    jobs = db.query(models.JobPosting).all()
    
    result = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            # ✅ FIXED: Use actual schema fields
            "title": job.job_title,
            "description": job.job_description_text or "",
            "department": job.department,
            "location": "",  # Not in your schema
            "experience_required": job.experience_range or "",
            "skills_required": job.required_skills or "",
            "status": job.status,
            "created_by": job.created_by,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "referral_count": db.query(models.Referral).filter(
                models.Referral.job_id == job.id
            ).count()
        }
        result.append(job_dict)
    
    return result

@app.get("/api/jobs/{job_id}")
async def get_job(
    job_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single job by ID"""
    # ✅ FIXED: Use JobPosting model
    job = db.query(models.JobPosting).filter(models.JobPosting.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    referral_count = db.query(models.Referral).filter(
        models.Referral.job_id == job.id
    ).count()
    
    job_dict = {
        "id": job.id,
        # ✅ FIXED: Use actual schema fields
        "title": job.job_title,
        "description": job.job_description_text or "",
        "department": job.department,
        "location": "",
        "experience_required": job.experience_range or "",
        "skills_required": job.required_skills or "",
        "status": job.status,
        "created_by": job.created_by,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "referral_count": referral_count
    }
    
    return job_dict

# ============================================
# REFERRALS ENDPOINTS
# ============================================

@app.get("/api/referrals")
async def get_referrals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all referrals (admin/hr/hiring_manager) or user's own referrals"""
    
    if current_user.role in ["hr", "hiring_manager", "admin"]:
        referrals = db.query(models.Referral).all()
    else:
        referrals = db.query(models.Referral).filter(
            models.Referral.referred_by == current_user.id
        ).all()
    
    result = []
    for ref in referrals:
        # ✅ FIXED: Use JobPosting model
        job = db.query(models.JobPosting).filter(models.JobPosting.id == ref.job_id).first()
        ref_dict = {
            "id": ref.id,
            "job_id": ref.job_id,
            # ✅ FIXED: Use job_title field
            "job_title": job.job_title if job else "N/A",
            "candidate_name": ref.candidate_name,
            "candidate_email": ref.candidate_email,
            "candidate_phone": ref.candidate_phone,
            "candidate_linkedin": "",  # Not in your schema
            "resume_path": ref.resume_url or "",
            "status": ref.status,
            "referred_by": ref.referred_by,
            "submitted_at": ref.created_at,
            "updated_at": ref.updated_at,
            "notes": ref.notes
        }
        result.append(ref_dict)
    
    return result

@app.get("/api/referrals/my-referrals")
async def get_my_referrals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's referrals"""
    referrals = db.query(models.Referral).filter(
        models.Referral.referred_by == current_user.id
    ).all()
    
    result = []
    for ref in referrals:
        # ✅ FIXED: Use JobPosting model
        job = db.query(models.JobPosting).filter(models.JobPosting.id == ref.job_id).first()
        ref_dict = {
            "id": ref.id,
            "job_id": ref.job_id,
            # ✅ FIXED: Use job_title field
            "job_title": job.job_title if job else "N/A",
            "candidate_name": ref.candidate_name,
            "candidate_email": ref.candidate_email,
            "candidate_phone": ref.candidate_phone,
            "candidate_linkedin": "",
            "resume_path": ref.resume_url or "",
            "status": ref.status,
            "referred_by": ref.referred_by,
            "submitted_at": ref.created_at,
            "updated_at": ref.updated_at,
            "notes": ref.notes
        }
        result.append(ref_dict)
    
    return result

# ============================================
# ASSETS ENDPOINTS (INVENTORY)
# ============================================

@app.get("/api/assets")
async def get_assets(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assets"""
    assets = db.query(models.Asset).all()
    
    result = []
    for asset in assets:
        # Get current assignee user details if assigned
        assigned_user = None
        if asset.current_assignee_user_id:
            assigned_user = db.query(models.User).filter(
                models.User.id == int(asset.current_assignee_user_id)
            ).first()
        
        asset_dict = {
            "id": asset.id,
            # ✅ FIXED: Use actual schema fields
            "serial_number": asset.laptop_serial_number or "",
            "category": asset.category,
            "model": asset.charger_number or "",  # Using available field
            "manufacturer": "",  # Not in schema
            "purchase_date": asset.procurement_date,
            "warranty_expiry": asset.warranty_expiry,
            "status": asset.status,
            "assigned_to": asset.current_assignee_user_id,
            "assigned_to_name": asset.current_assignee_name or "",
            "department": assigned_user.department if assigned_user else None,
            "location": "",  # Not in schema
            "notes": asset.notes,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at
        }
        result.append(asset_dict)
    
    return result

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Employee Portal API is running",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": "connected"
    }

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)