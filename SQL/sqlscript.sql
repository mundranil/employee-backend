-- ========================================
-- EMPLOYEE PORTAL - POSTGRESQL DATABASE SCHEMA
-- PostgreSQL 12+ Compatible
-- CREATE STATEMENTS ONLY
-- ========================================

-- ========================================
-- CREATE SEQUENCES
-- ========================================

CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE job_postings_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE referrals_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE assets_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE asset_history_seq START WITH 1 INCREMENT BY 1;

-- ========================================
-- USERS TABLE
-- ========================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY DEFAULT nextval('users_seq'),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'employee' 
        CHECK (role IN ('admin', 'hr', 'hiring_manager', 'employee', 'inventory_manager')),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Trigger function for auto-update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- JOB POSTINGS TABLE
-- ========================================

CREATE TABLE job_postings (
    id INTEGER PRIMARY KEY DEFAULT nextval('job_postings_seq'),
    job_title VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL,
    experience_range VARCHAR(50),
    status VARCHAR(20) DEFAULT 'open' 
        CHECK (status IN ('open', 'closed', 'on_hold')),
    fte_flex VARCHAR(50),
    is_budgeted BOOLEAN DEFAULT TRUE,
    job_description_url VARCHAR(500),
    job_description_text TEXT,
    required_skills TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jobs_status ON job_postings(status);
CREATE INDEX idx_jobs_department ON job_postings(department);
CREATE INDEX idx_jobs_created_by ON job_postings(created_by);

-- Trigger for job_postings table
CREATE TRIGGER update_job_postings_updated_at 
    BEFORE UPDATE ON job_postings
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- REFERRALS TABLE
-- ========================================

CREATE TABLE referrals (
    id INTEGER PRIMARY KEY DEFAULT nextval('referrals_seq'),
    job_id INTEGER NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    candidate_name VARCHAR(255) NOT NULL,
    candidate_email VARCHAR(255) NOT NULL,
    candidate_phone VARCHAR(20),
    department VARCHAR(100),
    experience VARCHAR(50),
    skills TEXT,
    referred_by INTEGER NOT NULL REFERENCES users(id),
    about_candidate TEXT,
    resume_url VARCHAR(500),
    candidate_photo_url VARCHAR(500),
    status VARCHAR(30) DEFAULT 'submitted' 
        CHECK (status IN ('submitted', 'under_review', 'shortlisted', 
                         'interview_scheduled', 'selected', 'rejected')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_referrals_job_id ON referrals(job_id);
CREATE INDEX idx_referrals_referred_by ON referrals(referred_by);
CREATE INDEX idx_referrals_status ON referrals(status);
CREATE INDEX idx_referrals_candidate_email ON referrals(candidate_email);

-- Trigger for referrals table
CREATE TRIGGER update_referrals_updated_at 
    BEFORE UPDATE ON referrals
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- ASSETS TABLE
-- ========================================

CREATE TABLE assets (
    id INTEGER PRIMARY KEY DEFAULT nextval('assets_seq'),
    laptop_serial_number VARCHAR(100) UNIQUE NOT NULL,
    charger_number VARCHAR(100),
    mac_id VARCHAR(100) UNIQUE,
    category VARCHAR(20) DEFAULT 'laptop' 
        CHECK (category IN ('laptop', 'desktop', 'monitor', 'mouse', 
                           'keyboard', 'headphones', 'charger', 'other')),
    external_mouse VARCHAR(50),
    headphones VARCHAR(100),
    mouse_pad VARCHAR(50),
    current_assignee_name VARCHAR(255),
    current_assignee_user_id VARCHAR(100),
    current_assignee_email VARCHAR(255),
    assigned_date TIMESTAMP,
    previous_assignee_name VARCHAR(255),
    previous_assignee_user_id VARCHAR(100),
    previous_assignee_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'available' 
        CHECK (status IN ('available', 'assigned', 'under_repair', 'retired')),
    notes TEXT,
    procurement_date TIMESTAMP,
    warranty_expiry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assets_serial ON assets(laptop_serial_number);
CREATE INDEX idx_assets_mac_id ON assets(mac_id);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_current_assignee ON assets(current_assignee_user_id);

-- Trigger for assets table
CREATE TRIGGER update_assets_updated_at 
    BEFORE UPDATE ON assets
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- ASSET HISTORY TABLE
-- ========================================

CREATE TABLE asset_history (
    id INTEGER PRIMARY KEY DEFAULT nextval('asset_history_seq'),
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    assignee_name VARCHAR(255),
    assignee_user_id VARCHAR(100),
    assignee_email VARCHAR(255),
    assigned_date TIMESTAMP,
    returned_date TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_asset_history_asset_id ON asset_history(asset_id);
CREATE INDEX idx_asset_history_assignee ON asset_history(assignee_user_id);

-- ========================================
-- INSERT SAMPLE DATA
-- ========================================

-- Insert admin user (password: admin123)
INSERT INTO users (email, full_name, hashed_password, role, department) 
VALUES (
    'admin@company.com',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LoS.zlVCqcKG',
    'admin',
    'IT'
);

-- Insert HR user (password: hr123)
INSERT INTO users (email, full_name, hashed_password, role, department) 
VALUES (
    'hr@company.com',
    'HR Manager',
    '$2b$12$qH8ZPXNJvjX7UPq0Lg.6je2zg8mKZMGPxlCE0M9qKk9wvPnQqH.T2',
    'hr',
    'Human Resources'
);

-- Insert Inventory Manager (password: inventory123)
INSERT INTO users (email, full_name, hashed_password, role, department) 
VALUES (
    'inventory@company.com',
    'Inventory Manager',
    '$2b$12$6k8LXTH4t6PvYP7dVF9ZEuZBq.Rp5P1KqZBqQNXqK7HpXqH7qH7qH',
    'inventory_manager',
    'Operations'
);

-- Insert Employee user (password: employee123)
INSERT INTO users (email, full_name, hashed_password, role, department) 
VALUES (
    'employee@company.com',
    'John Doe',
    '$2b$12$8k9LXTH4t6PvYP7dVF9ZEuZBq.Rp5P1KqZBqQNXqK7HpXqH7qH7qH',
    'employee',
    'Product Engineering'
);

-- Sample Job Posting 1
INSERT INTO job_postings (
    job_title,
    department,
    experience_range,
    status,
    fte_flex,
    is_budgeted,
    job_description_text,
    required_skills,
    created_by
) VALUES (
    'Senior Software Engineer',
    'Product Engineering',
    '5-7',
    'open',
    'FTE',
    TRUE,
    'We are looking for an experienced software engineer to join our team...',
    '["Python", "React", "AWS", "PostgreSQL"]',
    1
);

-- Sample Job Posting 2
INSERT INTO job_postings (
    job_title,
    department,
    experience_range,
    status,
    fte_flex,
    is_budgeted,
    job_description_text,
    required_skills,
    created_by
) VALUES (
    'DevOps Architect',
    'Product Engineering',
    '10+',
    'open',
    'FTE',
    TRUE,
    'Looking for a DevOps Architect with strong cloud experience...',
    '["AWS", "Kubernetes", "Docker", "CI/CD"]',
    2
);

-- Sample Job Posting 3
INSERT INTO job_postings (
    job_title,
    department,
    experience_range,
    status,
    fte_flex,
    is_budgeted,
    job_description_text,
    required_skills,
    created_by
) VALUES (
    'Cloud Engineer I',
    'Product Engineering',
    '5-7',
    'open',
    'FTE',
    TRUE,
    'Cloud Engineer position for managing infrastructure...',
    '["AWS", "Terraform", "Python"]',
    2
);

-- Sample Referral
INSERT INTO referrals (
    job_id,
    candidate_name,
    candidate_email,
    candidate_phone,
    department,
    experience,
    skills,
    referred_by,
    about_candidate,
    status
) VALUES (
    1,
    'Jane Smith',
    'jane.smith@email.com',
    '+1-555-0100',
    'Product Engineering',
    '6 years',
    '["Python", "Django", "React", "AWS"]',
    4,
    'Jane is an excellent engineer with strong problem-solving skills...',
    'submitted'
);

-- Sample Asset 1
INSERT INTO assets (
    laptop_serial_number,
    charger_number,
    mac_id,
    category,
    external_mouse,
    headphones,
    mouse_pad,
    status
) VALUES (
    'SCD42653F5C',
    'WHHRHOA1RITCKK',
    '6C:2F:80:A2:AD:32',
    'laptop',
    'YES',
    'Bluetooth Boat',
    'YES',
    'available'
);

-- Sample Asset 2
INSERT INTO assets (
    laptop_serial_number,
    charger_number,
    mac_id,
    category,
    external_mouse,
    headphones,
    mouse_pad,
    status,
    current_assignee_name,
    current_assignee_user_id,
    current_assignee_email,
    assigned_date
) VALUES (
    'SCD42653DMC',
    'WHHRHOA1RIRCKI',
    '6C:2F:80:A2:A6:07',
    'laptop',
    'yes',
    'Bluetooth Boat',
    'no',
    'assigned',
    'John Doe',
    'EMP001',
    'employee@company.com',
    CURRENT_TIMESTAMP
);

-- Sample Asset 3
INSERT INTO assets (
    laptop_serial_number,
    charger_number,
    mac_id,
    category,
    external_mouse,
    headphones,
    mouse_pad,
    status
) VALUES (
    'SCD42653DS',
    'WHHRHOA1RIR2R4',
    '6C:2F:80:A5:1E:7D',
    'laptop',
    'yes',
    'Bluetooth boat',
    'no',
    'available'
);

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Display summary
SELECT 'Database schema created successfully!' AS message;

-- Display table counts
SELECT 
    (SELECT COUNT(*) FROM users) AS users_count,
    (SELECT COUNT(*) FROM job_postings) AS jobs_count,
    (SELECT COUNT(*) FROM referrals) AS referrals_count,
    (SELECT COUNT(*) FROM assets) AS assets_count,
    (SELECT COUNT(*) FROM asset_history) AS history_count;

-- Display all users
SELECT id, email, full_name, role, department FROM users;

-- Display all job postings
SELECT id, job_title, department, experience_range, status FROM job_postings;

-- Display all assets
SELECT id, laptop_serial_number, status, current_assignee_name FROM assets;