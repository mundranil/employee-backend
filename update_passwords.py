"""
Script to update user passwords in the database
Run this to fix password authentication
"""
from passlib.context import CryptContext
import psycopg2

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection
conn = psycopg2.connect(
    dbname="employee",
    user="postgres",
    password="admin",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Users and their passwords
users = [
    ('admin@company.com', 'admin123'),
    ('hr@company.com', 'hr123'),
    ('inventory@company.com', 'inventory123'),
    ('employee@company.com', 'employee123'),
]

print("Updating user passwords...")
print("-" * 50)

for email, password in users:
    # Generate hash
    hashed_password = pwd_context.hash(password)
    
    # Update database
    cursor.execute(
        "UPDATE users SET hashed_password = %s WHERE email = %s",
        (hashed_password, email)
    )
    
    print(f"✓ Updated password for {email}")

# Commit changes
conn.commit()
cursor.close()
conn.close()

print("-" * 50)
print("✅ All passwords updated successfully!")
print("\nYou can now login with:")
print("  admin@company.com / admin123")
print("  hr@company.com / hr123")
print("  inventory@company.com / inventory123")
print("  employee@company.com / employee123")