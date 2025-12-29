from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = 'employee'
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Job Posting Schemas
class JobPostingBase(BaseModel):
    job_title: str
    department: str
    experience_range: Optional[str] = None
    status: str = 'open'
    fte_flex: Optional[str] = "FTE"
    is_budgeted: bool = True
    job_description_url: Optional[str] = None
    job_description_text: Optional[str] = None
    required_skills: Optional[str] = None

class JobPostingCreate(JobPostingBase):
    pass

class JobPostingUpdate(BaseModel):
    job_title: Optional[str] = None
    department: Optional[str] = None
    experience_range: Optional[str] = None
    status: Optional[str] = None
    fte_flex: Optional[str] = None
    is_budgeted: Optional[bool] = None
    job_description_url: Optional[str] = None
    job_description_text: Optional[str] = None
    required_skills: Optional[str] = None

class JobPosting(JobPostingBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Referral Schemas
class ReferralBase(BaseModel):
    job_id: int
    candidate_name: str
    candidate_email: EmailStr
    candidate_phone: Optional[str] = None
    department: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    about_candidate: Optional[str] = None
    resume_url: Optional[str] = None
    candidate_photo_url: Optional[str] = None

class ReferralCreate(ReferralBase):
    pass

class ReferralUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class Referral(ReferralBase):
    id: int
    referred_by: int
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Asset Schemas
class AssetBase(BaseModel):
    laptop_serial_number: str
    charger_number: Optional[str] = None
    mac_id: Optional[str] = None
    category: str = 'laptop'
    external_mouse: Optional[str] = None
    headphones: Optional[str] = None
    mouse_pad: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetAssign(BaseModel):
    current_assignee_name: str
    current_assignee_user_id: str
    current_assignee_email: EmailStr

class AssetUpdate(BaseModel):
    charger_number: Optional[str] = None
    external_mouse: Optional[str] = None
    headphones: Optional[str] = None
    mouse_pad: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class Asset(AssetBase):
    id: int
    current_assignee_name: Optional[str] = None
    current_assignee_user_id: Optional[str] = None
    current_assignee_email: Optional[str] = None
    assigned_date: Optional[datetime] = None
    previous_assignee_name: Optional[str] = None
    previous_assignee_user_id: Optional[str] = None
    previous_assignee_date: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    procurement_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AssetHistoryItem(BaseModel):
    id: int
    assignee_name: Optional[str]
    assignee_user_id: Optional[str]
    assignee_email: Optional[str]
    assigned_date: Optional[datetime]
    returned_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True