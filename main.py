from fastapi import File, UploadFile, Form  # ✅ FIXED: Added Form here
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
import shutil
import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, ConfigDict  # ✅ FIXED: Added ConfigDict
import os

# Database imports
from database import SessionLocal, engine
import models

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Subdirectories
RESUMES_DIR = UPLOAD_DIR / "resumes"
PHOTOS_DIR = UPLOAD_DIR / "photos"
JOB_DESCRIPTIONS_DIR = UPLOAD_DIR / "job_descriptions"

RESUMES_DIR.mkdir(exist_ok=True)
PHOTOS_DIR.mkdir(exist_ok=True)
JOB_DESCRIPTIONS_DIR.mkdir(exist_ok=True)

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

    # ✅ FIXED: Use ConfigDict instead of class Config
    model_config = ConfigDict(from_attributes=True)
        
# Helper function to save uploaded file
def save_upload_file(upload_file: UploadFile, directory: Path) -> str:
    """Save uploaded file and return the file path"""
    try:
        # Generate unique filename
        file_extension = Path(upload_file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = directory / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        return str(file_path)
    finally:
        upload_file.file.close()

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
    jobs = db.query(models.JobPosting).all()
    
    result = []
    for job in jobs:
        job_dict = {
            "id": job.id,
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
        job = db.query(models.JobPosting).filter(models.JobPosting.id == ref.job_id).first()
        ref_dict = {
            "id": ref.id,
            "job_id": ref.job_id,
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
            "notes": ref.notes,
            "department": ref.department,
            "experience": ref.experience,
            "skills": ref.skills,
            "about_candidate": ref.about_candidate
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
        job = db.query(models.JobPosting).filter(models.JobPosting.id == ref.job_id).first()
        ref_dict = {
            "id": ref.id,
            "job_id": ref.job_id,
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

# ✅ GET REFERRAL BY ID - THIS WAS MISSING!
@app.get("/api/referrals/{referral_id}")
async def get_referral(
    referral_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get referral details by ID"""
    
    referral = db.query(models.Referral).filter(
        models.Referral.id == referral_id
    ).first()
    
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    # Check authorization
    if current_user.role not in ["admin", "hr", "hiring_manager"] and referral.referred_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    job = db.query(models.JobPosting).filter(
        models.JobPosting.id == referral.job_id
    ).first()
    
    return {
        "id": referral.id,
        "job_id": referral.job_id,
        "job_title": job.job_title if job else "N/A",
        "candidate_name": referral.candidate_name,
        "candidate_email": referral.candidate_email,
        "candidate_phone": referral.candidate_phone,
        "department": referral.department,
        "experience": referral.experience,
        "skills": referral.skills,
        "about_candidate": referral.about_candidate,
        "resume_url": referral.resume_url,
        "candidate_photo_url": referral.candidate_photo_url,
        "status": referral.status,
        "referred_by": referral.referred_by,
        "notes": referral.notes if hasattr(referral, 'notes') else None,
        "created_at": referral.created_at.isoformat() if referral.created_at else None,
        "updated_at": referral.updated_at.isoformat() if referral.updated_at else None
    }

# ================================
# CREATE REFERRAL WITH FILE UPLOAD
# ================================

@app.post("/api/referrals")
async def create_referral(
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    candidate_phone: str = Form(None),
    department: str = Form(...),
    experience: str = Form(...),
    skills: str = Form(None),
    job_id: int = Form(...),
    about_candidate: str = Form(None),
    referred_by: int = Form(...),
    resume: UploadFile = File(None),
    photo: UploadFile = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new referral with file uploads"""
    
    # Save resume file
    resume_path = None
    if resume:
        resume_path = save_upload_file(resume, RESUMES_DIR)
    
    # Save photo file
    photo_path = None
    if photo:
        photo_path = save_upload_file(photo, PHOTOS_DIR)
    
    # Create referral
    new_referral = models.Referral(
        job_id=job_id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_phone=candidate_phone,
        department=department,
        experience=experience,
        skills=skills,
        referred_by=referred_by,
        about_candidate=about_candidate,
        resume_url=resume_path,
        candidate_photo_url=photo_path,
        status='submitted'
    )
    
    db.add(new_referral)
    db.commit()
    db.refresh(new_referral)
    
    return {
        "id": new_referral.id,
        "message": "Referral created successfully"
    }

# ================================
# UPDATE REFERRAL WITH FILE UPLOAD
# ================================

@app.put("/api/referrals/{referral_id}")
async def update_referral(
    referral_id: int,
    candidate_name: str = Form(None),
    candidate_email: str = Form(None),
    candidate_phone: str = Form(None),
    department: str = Form(None),
    experience: str = Form(None),
    skills: str = Form(None),
    job_id: int = Form(None),
    about_candidate: str = Form(None),
    status: str = Form(None),
    resume: UploadFile = File(None),
    photo: UploadFile = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a referral with optional file uploads"""
    
    referral = db.query(models.Referral).filter(
        models.Referral.id == referral_id
    ).first()
    
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    # Check authorization
    if current_user.role not in ["admin", "hr", "hiring_manager"] and referral.referred_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    if candidate_name: referral.candidate_name = candidate_name
    if candidate_email: referral.candidate_email = candidate_email
    if candidate_phone: referral.candidate_phone = candidate_phone
    if department: referral.department = department
    if experience: referral.experience = experience
    if skills: referral.skills = skills
    if job_id: referral.job_id = job_id
    if about_candidate: referral.about_candidate = about_candidate
    if status: referral.status = status
    
    # Update resume if provided
    if resume:
        resume_path = save_upload_file(resume, RESUMES_DIR)
        referral.resume_url = resume_path
    
    # Update photo if provided
    if photo:
        photo_path = save_upload_file(photo, PHOTOS_DIR)
        referral.candidate_photo_url = photo_path
    
    db.commit()
    db.refresh(referral)
    
    return {
        "id": referral.id,
        "message": "Referral updated successfully"
    }

# ✅ DELETE REFERRAL
@app.delete("/api/referrals/{referral_id}")
async def delete_referral(
    referral_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a referral"""
    
    referral = db.query(models.Referral).filter(
        models.Referral.id == referral_id
    ).first()
    
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    # Only admin, hr can delete
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete referrals")
    
    db.delete(referral)
    db.commit()
    
    return {"message": "Referral deleted successfully"}

# ================================
# CREATE JOB WITH FILE UPLOAD
# ================================

@app.post("/api/jobs")
async def create_job(
    job_title: str = Form(...),
    department: str = Form(...),
    experience_range: str = Form(None),
    fte_flex: str = Form("FTE"),
    is_budgeted: bool = Form(True),
    job_description_text: str = Form(None),
    required_skills: str = Form(None),
    status: str = Form("open"),
    created_by: int = Form(...),
    job_description_file: UploadFile = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job with optional JD file upload"""
    
    # Check authorization
    if current_user.role not in ["admin", "hr", "hiring_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to create jobs")
    
    # Save JD file if provided
    jd_file_path = None
    if job_description_file:
        jd_file_path = save_upload_file(job_description_file, JOB_DESCRIPTIONS_DIR)
    
    # Create job
    new_job = models.JobPosting(
        job_title=job_title,
        department=department,
        experience_range=experience_range,
        fte_flex=fte_flex,
        is_budgeted=is_budgeted,
        job_description_text=job_description_text,
        job_description_url=jd_file_path,
        required_skills=required_skills,
        status=status,
        created_by=created_by
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return {
        "id": new_job.id,
        "message": "Job created successfully"
    }

# ================================
# UPDATE JOB WITH FILE UPLOAD
# ================================

@app.put("/api/jobs/{job_id}")
async def update_job(
    job_id: int,
    job_title: str = Form(None),
    department: str = Form(None),
    experience_range: str = Form(None),
    fte_flex: str = Form(None),
    is_budgeted: bool = Form(None),
    job_description_text: str = Form(None),
    required_skills: str = Form(None),
    status: str = Form(None),
    job_description_file: UploadFile = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a job with optional JD file upload"""
    
    job = db.query(models.JobPosting).filter(
        models.JobPosting.id == job_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check authorization
    if current_user.role not in ["admin", "hr", "hiring_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    if job_title: job.job_title = job_title
    if department: job.department = department
    if experience_range: job.experience_range = experience_range
    if fte_flex: job.fte_flex = fte_flex
    if is_budgeted is not None: job.is_budgeted = is_budgeted
    if job_description_text: job.job_description_text = job_description_text
    if required_skills: job.required_skills = required_skills
    if status: job.status = status
    
    # Update JD file if provided
    if job_description_file:
        jd_file_path = save_upload_file(job_description_file, JOB_DESCRIPTIONS_DIR)
        job.job_description_url = jd_file_path
    
    db.commit()
    db.refresh(job)
    
    return {
        "id": job.id,
        "message": "Job updated successfully"
    }

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
            "serial_number": asset.laptop_serial_number or "",
            "category": asset.category,
            "model": asset.charger_number or "",
            "manufacturer": "",
            "purchase_date": asset.procurement_date,
            "warranty_expiry": asset.warranty_expiry,
            "status": asset.status,
            "assigned_to": asset.current_assignee_user_id,
            "assigned_to_name": asset.current_assignee_name or "",
            "department": assigned_user.department if assigned_user else None,
            "location": "",
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
    
    
    # ========================================
# ULTRA-SIMPLE FIX - COPY THIS ENTIRE FILE
# Replace BOTH /api/assets endpoints in main.py
# ========================================

# GET all assets - WORKING VERSION
@app.get("/api/assets")
async def get_assets(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assets"""
    assets = db.query(models.Asset).all()
    
    result = []
    for asset in assets:
        result.append({
            "id": asset.id,
            "serial_number": asset.laptop_serial_number or "",
            "category": asset.category,
            "model": asset.charger_number or "",
            "manufacturer": "",
            "purchase_date": asset.procurement_date.isoformat() if asset.procurement_date else None,
            "warranty_expiry": asset.warranty_expiry.isoformat() if asset.warranty_expiry else None,
            "status": asset.status,
            "assigned_to": asset.current_assignee_user_id,
            "assigned_to_name": asset.current_assignee_name or "",
            "department": None,
            "location": "",
            "notes": asset.notes,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
        })
    
    return result


# GET single asset - WORKING VERSION
@app.get("/api/assets/{asset_id}")
async def get_asset(
    asset_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single asset by ID"""
    asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return {
        "id": asset.id,
        "serial_number": asset.laptop_serial_number or "",
        "category": asset.category,
        "model": asset.charger_number or "",
        "manufacturer": "",
        "purchase_date": asset.procurement_date.isoformat() if asset.procurement_date else None,
        "warranty_expiry": asset.warranty_expiry.isoformat() if asset.warranty_expiry else None,
        "status": asset.status,
        "assigned_to": asset.current_assignee_user_id,
        "assigned_to_name": asset.current_assignee_name or "",
        "department": None,
        "location": "",
        "notes": asset.notes,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
    }


# CREATE asset - NO CHANGES NEEDED
@app.post("/api/assets")
async def create_asset(
    asset_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new asset"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to create assets")
    
    new_asset = models.Asset(
        laptop_serial_number=asset_data.get('serial_number'),
        category=asset_data.get('category'),
        charger_number=asset_data.get('model'),
        procurement_date=asset_data.get('purchase_date'),
        warranty_expiry=asset_data.get('warranty_expiry'),
        status=asset_data.get('status', 'available'),
        current_assignee_user_id=asset_data.get('assigned_to'),
        current_assignee_name=asset_data.get('assigned_to_name'),
        notes=asset_data.get('notes')
    )
    
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    
    return {"id": new_asset.id, "message": "Asset created successfully"}


# UPDATE asset - NO CHANGES NEEDED
@app.put("/api/assets/{asset_id}")
async def update_asset(
    asset_id: int,
    asset_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an asset"""
    asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to update assets")
    
    if 'serial_number' in asset_data:
        asset.laptop_serial_number = asset_data['serial_number']
    if 'category' in asset_data:
        asset.category = asset_data['category']
    if 'model' in asset_data:
        asset.charger_number = asset_data['model']
    if 'purchase_date' in asset_data:
        asset.procurement_date = asset_data['purchase_date']
    if 'warranty_expiry' in asset_data:
        asset.warranty_expiry = asset_data['warranty_expiry']
    if 'status' in asset_data:
        asset.status = asset_data['status']
    if 'assigned_to' in asset_data:
        asset.current_assignee_user_id = asset_data['assigned_to']
    if 'assigned_to_name' in asset_data:
        asset.current_assignee_name = asset_data['assigned_to_name']
    if 'notes' in asset_data:
        asset.notes = asset_data['notes']
    
    db.commit()
    db.refresh(asset)
    
    return {"id": asset.id, "message": "Asset updated successfully"}


# DELETE asset - NO CHANGES NEEDED
@app.delete("/api/assets/{asset_id}")
async def delete_asset(
    asset_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an asset"""
    asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete assets")
    
    db.delete(asset)
    db.commit()
    
    return {"message": "Asset deleted successfully"}

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)