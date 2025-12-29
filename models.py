from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Remove Python enums, use simple strings instead

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default='employee')  # Changed from Enum to String
    department = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    referrals = relationship("Referral", back_populates="referred_by_user")

class JobPosting(Base):
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    experience_range = Column(String)  # e.g., "5-7", "10+"
    status = Column(String, default='open')  # Changed from Enum to String
    fte_flex = Column(String)  # "FTE", "Flex", etc.
    is_budgeted = Column(Boolean, default=True)
    job_description_url = Column(String)
    job_description_text = Column(Text)
    required_skills = Column(Text)  # JSON string of skills array
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    referrals = relationship("Referral", back_populates="job")

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    candidate_name = Column(String, nullable=False)
    candidate_email = Column(String, nullable=False)
    candidate_phone = Column(String)
    department = Column(String)
    experience = Column(String)
    skills = Column(Text)  # JSON string of skills array
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    about_candidate = Column(Text)
    resume_url = Column(String)
    candidate_photo_url = Column(String)
    status = Column(String, default='submitted')  # Changed from Enum to String
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job = relationship("JobPosting", back_populates="referrals")
    referred_by_user = relationship("User", back_populates="referrals")

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    laptop_serial_number = Column(String, unique=True, index=True)
    charger_number = Column(String)
    mac_id = Column(String, unique=True)
    category = Column(String, default='laptop')  # Changed from Enum to String
    external_mouse = Column(String)
    headphones = Column(String)
    mouse_pad = Column(String)
    
    # Current assignment
    current_assignee_name = Column(String)
    current_assignee_user_id = Column(String)
    current_assignee_email = Column(String)
    assigned_date = Column(DateTime)
    
    # Previous assignment
    previous_assignee_name = Column(String)
    previous_assignee_user_id = Column(String)
    previous_assignee_date = Column(DateTime)
    
    status = Column(String, default='available')  # Changed from Enum to String
    notes = Column(Text)
    procurement_date = Column(DateTime)
    warranty_expiry = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    history = relationship("AssetHistory", back_populates="asset")

class AssetHistory(Base):
    __tablename__ = "asset_history"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    assignee_name = Column(String)
    assignee_user_id = Column(String)
    assignee_email = Column(String)
    assigned_date = Column(DateTime)
    returned_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    asset = relationship("Asset", back_populates="history")

