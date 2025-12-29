"""
Create Admin User and Sample Data - create_admin.py
File: C:\Office\employee_backend\create_admin.py
"""

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine, init_db
import models
from datetime import datetime, date

# Initialize database
init_db()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_sample_data():
    """Create admin user and sample data"""
    db = SessionLocal()
    
    try:
        print("\n🔧 Creating sample data...")
        
        # Check if admin already exists
        existing_admin = db.query(models.User).filter(
            models.User.email == "admin@company.com"
        ).first()
        
        if existing_admin:
            print("⚠️  Admin user already exists!")
            print(f"   Email: {existing_admin.email}")
            print(f"   Role: {existing_admin.role}")
        else:
            # Create admin user
            admin_user = models.User(
                email="admin@company.com",
                full_name="Admin User",
                password_hash=pwd_context.hash("admin123"),
                role="admin",
                department="IT",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("✅ Admin user created!")
            print(f"   Email: admin@company.com")
            print(f"   Password: admin123")
            print(f"   Role: admin")
        
        # Create HR user
        existing_hr = db.query(models.User).filter(
            models.User.email == "hr@company.com"
        ).first()
        
        if not existing_hr:
            hr_user = models.User(
                email="hr@company.com",
                full_name="HR Manager",
                password_hash=pwd_context.hash("hr123"),
                role="hr",
                department="Human Resources",
                is_active=True
            )
            db.add(hr_user)
            db.commit()
            db.refresh(hr_user)
            print("✅ HR user created!")
            print(f"   Email: hr@company.com")
            print(f"   Password: hr123")
        
        # Create employee user
        existing_employee = db.query(models.User).filter(
            models.User.email == "employee@company.com"
        ).first()
        
        if not existing_employee:
            employee_user = models.User(
                email="employee@company.com",
                full_name="John Employee",
                password_hash=pwd_context.hash("employee123"),
                role="employee",
                department="Engineering",
                is_active=True
            )
            db.add(employee_user)
            db.commit()
            db.refresh(employee_user)
            print("✅ Employee user created!")
            print(f"   Email: employee@company.com")
            print(f"   Password: employee123")
        
        # Create inventory manager
        existing_inv = db.query(models.User).filter(
            models.User.email == "inventory@company.com"
        ).first()
        
        if not existing_inv:
            inv_user = models.User(
                email="inventory@company.com",
                full_name="Inventory Manager",
                password_hash=pwd_context.hash("inventory123"),
                role="inventory_manager",
                department="IT",
                is_active=True
            )
            db.add(inv_user)
            db.commit()
            db.refresh(inv_user)
            print("✅ Inventory Manager created!")
            print(f"   Email: inventory@company.com")
            print(f"   Password: inventory123")
        
        # Get admin for creating jobs
        admin = db.query(models.User).filter(
            models.User.email == "admin@company.com"
        ).first()
        
        # Create sample jobs
        job_count = db.query(models.Job).count()
        if job_count == 0:
            sample_jobs = [
                {
                    "title": "Senior Full Stack Developer",
                    "description": "We are looking for an experienced Full Stack Developer...",
                    "department": "Engineering",
                    "location": "Hyderabad",
                    "experience_required": "5-7 years",
                    "skills_required": "React, Node.js, Python, AWS",
                    "status": "open",
                    "created_by": admin.id
                },
                {
                    "title": "DevOps Engineer",
                    "description": "Join our DevOps team to build and maintain infrastructure...",
                    "department": "Engineering",
                    "location": "Bangalore",
                    "experience_required": "3-5 years",
                    "skills_required": "Docker, Kubernetes, AWS, CI/CD",
                    "status": "open",
                    "created_by": admin.id
                },
                {
                    "title": "Product Manager",
                    "description": "Drive product strategy and roadmap...",
                    "department": "Product",
                    "location": "Remote",
                    "experience_required": "4-6 years",
                    "skills_required": "Product Management, Agile, Stakeholder Management",
                    "status": "open",
                    "created_by": admin.id
                }
            ]
            
            for job_data in sample_jobs:
                job = models.Job(**job_data)
                db.add(job)
            
            db.commit()
            print(f"✅ Created {len(sample_jobs)} sample jobs!")
        
        # Create sample assets
        asset_count = db.query(models.Asset).count()
        if asset_count == 0:
            sample_assets = [
                {
                    "serial_number": "LPT-2024-001",
                    "category": "Laptop",
                    "model": "MacBook Pro 16",
                    "manufacturer": "Apple",
                    "purchase_date": date(2024, 1, 15),
                    "warranty_expiry": date(2027, 1, 15),
                    "status": "available",
                    "location": "IT Store"
                },
                {
                    "serial_number": "LPT-2024-002",
                    "category": "Laptop",
                    "model": "Dell XPS 15",
                    "manufacturer": "Dell",
                    "purchase_date": date(2024, 2, 10),
                    "warranty_expiry": date(2027, 2, 10),
                    "status": "available",
                    "location": "IT Store"
                },
                {
                    "serial_number": "MON-2024-001",
                    "category": "Monitor",
                    "model": "Dell UltraSharp 27",
                    "manufacturer": "Dell",
                    "purchase_date": date(2024, 1, 20),
                    "warranty_expiry": date(2027, 1, 20),
                    "status": "available",
                    "location": "IT Store"
                }
            ]
            
            for asset_data in sample_assets:
                asset = models.Asset(**asset_data)
                db.add(asset)
            
            db.commit()
            print(f"✅ Created {len(sample_assets)} sample assets!")
        
        print("\n✅ Sample data creation complete!")
        print("\n📋 Test Credentials:")
        print("   Admin:     admin@company.com / admin123")
        print("   HR:        hr@company.com / hr123")
        print("   Employee:  employee@company.com / employee123")
        print("   Inventory: inventory@company.com / inventory123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()