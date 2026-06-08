gitfrom fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import pymysql
import os
import hashlib

app = FastAPI()

# ---------------- Templates ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ---------------- Database Connection ----------------
def get_db():
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="root",  # Change this to your MySQL password
            database="internship_portal",
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        print("Database connection error:", e)
        raise HTTPException(status_code=500, detail="Database connection failed")

# ---------------- Pydantic Models ----------------
class User(BaseModel):
    name: str
    email: str
    password: str
    role: str
    mobile: Optional[str] = None
    skills: Optional[str] = None

class Internship(BaseModel):
    company_id: int
    title: str
    skills_required: str
    stipend: Optional[str] = None
    description: Optional[str] = None

class Application(BaseModel):
    internship_id: int
    student_id: int
    experience: Optional[str] = None
    knowledge: Optional[str] = None
    documents: str
    status: str = "Pending"

class StatusUpdate(BaseModel):
    application_id: int
    status: str

# ---------------- Helper Functions ----------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- Template Routes (Frontend Pages) ----------------
@app.get("/", response_class=HTMLResponse)
@app.get("/index", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/company_dashboard", response_class=HTMLResponse)
def company_dashboard(request: Request):
    return templates.TemplateResponse("company_dashboard.html", {"request": request})

@app.get("/student_dashboard", response_class=HTMLResponse)
def student_dashboard(request: Request):
    return templates.TemplateResponse("student_dashboard.html", {"request": request})

@app.get("/apply", response_class=HTMLResponse)
def apply_page(request: Request):
    return templates.TemplateResponse("apply.html", {"request": request})

@app.get("/student_view_internship", response_class=HTMLResponse)
def student_view_internships(request: Request):
    return templates.TemplateResponse("student_view_internships.html", {"request": request})

@app.get("/student_my_applications", response_class=HTMLResponse)
def student_my_applications(request: Request):
    return templates.TemplateResponse("student_my_applications.html", {"request": request})

@app.get("/student_profile", response_class=HTMLResponse)
def student_profile(request: Request):
    return templates.TemplateResponse("student_profile.html", {"request": request})

@app.get("/company_post_internship", response_class=HTMLResponse)
def company_post_internship_page(request: Request):
    return templates.TemplateResponse("company_post_internship.html", {"request": request})

@app.get("/company_view_internships", response_class=HTMLResponse)
def company_view_internships_page(request: Request):
    return templates.TemplateResponse("company_view_internships.html", {"request": request})

@app.get("/hr_profile", response_class=HTMLResponse)
def hr_profile_page(request: Request):
    return templates.TemplateResponse("hr_profile.html", {"request": request})

@app.get("/logout", response_class=HTMLResponse)
def logout_page(request: Request):
    return templates.TemplateResponse("logout.html", {"request": request})

# ---------------- User Management APIs ----------------

@app.post("/api/register")
def register(user: User):
    """Register a new user (student or company)"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Hash the password before storing
            hashed_password = hash_password(user.password)
            
            cursor.execute(
                "INSERT INTO users (name, email, password, role, mobile, skills) VALUES (%s, %s, %s, %s, %s, %s)",
                (user.name, user.email, hashed_password, user.role, user.mobile, user.skills)
            )
        conn.commit()
        return {"message": "User registered successfully", "success": True}
    except pymysql.err.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists")
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        conn.close()

@app.post("/api/login")
def login(email: str = Form(...), password: str = Form(...), role: str = Form(...)):
    """Login user and return user details"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email=%s AND role=%s", (email, role))
            user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=400, detail="User not found with this email and role")
        
        # Check both plain text (for old passwords) and hashed password
        hashed_password = hash_password(password)
        if password != user['password'] and hashed_password != user['password']:
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        # Remove password from response for security
        del user['password']
        del user['created_at']  # Remove timestamp for cleaner response
        
        return {"message": "Login successful", "user": user, "success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
    finally:
        conn.close()

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    """Get user details by ID"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, name, email, role, mobile, skills, created_at FROM users WHERE user_id=%s", 
                (user_id,)
            )
            user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"user": user, "success": True}
    finally:
        conn.close()

# ---------------- Internship Management APIs ----------------

@app.post("/api/internships")
def post_internship(internship: Internship):
    """Company posts a new internship"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO internships (company_id, title, skills_required, stipend, description) VALUES (%s, %s, %s, %s, %s)",
                (internship.company_id, internship.title, internship.skills_required, 
                 internship.stipend, internship.description)
            )
        conn.commit()
        return {"message": "Internship posted successfully", "success": True}
    except Exception as e:
        print(f"Post internship error: {e}")
        raise HTTPException(status_code=500, detail="Failed to post internship")
    finally:
        conn.close()

@app.get("/api/internships")
def view_all_internships():
    """View all available internships (for students)"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    i.internship_id, 
                    i.company_id, 
                    i.title, 
                    i.skills_required, 
                    i.stipend, 
                    i.description, 
                    i.posted_at, 
                    u.name as company_name 
                FROM internships i 
                JOIN users u ON i.company_id = u.user_id 
                WHERE u.role = 'company'
                ORDER BY i.posted_at DESC
            """)
            internships = cursor.fetchall()
        
        return {"internships": internships, "success": True}
    except Exception as e:
        print(f"View internships error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch internships")
    finally:
        conn.close()

@app.get("/api/internship/{internship_id}")
def get_internship_details(internship_id: int):
    """Get details of a specific internship"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    i.*, 
                    u.name as company_name,
                    u.email as company_email,
                    u.mobile as company_mobile
                FROM internships i
                JOIN users u ON i.company_id = u.user_id
                WHERE i.internship_id = %s
            """, (internship_id,))
            internship = cursor.fetchone()
        
        if not internship:
            raise HTTPException(status_code=404, detail="Internship not found")
        
        return {"internship": internship, "success": True}
    finally:
        conn.close()

@app.get("/api/company/internships/{company_id}")
def get_company_internships(company_id: int):
    """Get all internships posted by a company with application count"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    i.*,
                    COUNT(a.application_id) as total_applications,
                    SUM(CASE WHEN a.status = 'Pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN a.status = 'Selected' THEN 1 ELSE 0 END) as selected_count,
                    SUM(CASE WHEN a.status = 'Rejected' THEN 1 ELSE 0 END) as rejected_count
                FROM internships i
                LEFT JOIN applications a ON i.internship_id = a.internship_id
                WHERE i.company_id = %s
                GROUP BY i.internship_id
                ORDER BY i.posted_at DESC
            """, (company_id,))
            internships = cursor.fetchall()
        
        return {"internships": internships, "success": True}
    finally:
        conn.close()

# ---------------- Application Management APIs ----------------

@app.post("/api/apply")
def apply_for_internship(application: Application):
    """Student applies for an internship"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Check if student already applied for this internship
            cursor.execute(
                "SELECT * FROM applications WHERE internship_id=%s AND student_id=%s",
                (application.internship_id, application.student_id)
            )
            existing = cursor.fetchone()
            
            if existing:
                raise HTTPException(status_code=400, detail="You have already applied for this internship")
            
            # Insert new application
            cursor.execute(
                "INSERT INTO applications (internship_id, student_id, experience, knowledge, documents, status) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (application.internship_id, application.student_id, application.experience,
                 application.knowledge, application.documents, application.status)
            )
        conn.commit()
        return {"message": "Application submitted successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Apply error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit application")
    finally:
        conn.close()

@app.get("/api/applications/{student_id}")
def get_student_applications(student_id: int):
    """Get all applications submitted by a student"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.application_id, 
                    a.internship_id, 
                    a.student_id, 
                    a.experience, 
                    a.knowledge, 
                    a.documents, 
                    a.status, 
                    a.applied_at,
                    i.title as internship_title, 
                    i.skills_required, 
                    i.stipend,
                    i.description,
                    u.name as company_name,
                    u.email as company_email
                FROM applications a
                JOIN internships i ON a.internship_id = i.internship_id
                JOIN users u ON i.company_id = u.user_id
                WHERE a.student_id = %s
                ORDER BY a.applied_at DESC
            """, (student_id,))
            applications = cursor.fetchall()
        
        return {"applications": applications, "success": True}
    except Exception as e:
        print(f"Get applications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch applications")
    finally:
        conn.close()

@app.get("/api/student/applications/status/{student_id}")
def get_student_application_status(student_id: int):
    """Get student applications with detailed status messages"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.application_id, 
                    a.internship_id,
                    a.status, 
                    a.applied_at,
                    i.title as internship_title,
                    i.skills_required,
                    i.stipend,
                    u.name as company_name,
                    CASE 
                        WHEN a.status = 'Selected' THEN 'Congratulations! You have been selected for this internship.'
                        WHEN a.status = 'Rejected' THEN 'Thank you for your application. Unfortunately, you were not selected this time.'
                        ELSE 'Your application is under review.'
                    END as status_message
                FROM applications a
                JOIN internships i ON a.internship_id = i.internship_id
                JOIN users u ON i.company_id = u.user_id
                WHERE a.student_id = %s
                ORDER BY 
                    CASE 
                        WHEN a.status = 'Selected' THEN 1
                        WHEN a.status = 'Rejected' THEN 2
                        ELSE 3
                    END,
                    a.applied_at DESC
            """, (student_id,))
            applications = cursor.fetchall()
        
        return {"applications": applications, "success": True}
    finally:
        conn.close()

@app.get("/api/application/{application_id}")
def get_application_details(application_id: int):
    """Get detailed information about a specific application"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.*, 
                    i.title as internship_title,
                    i.skills_required,
                    i.stipend,
                    i.description,
                    u.name as company_name,
                    u.email as company_email,
                    s.name as student_name,
                    s.email as student_email,
                    s.mobile as student_mobile,
                    s.skills as student_skills
                FROM applications a
                JOIN internships i ON a.internship_id = i.internship_id
                JOIN users u ON i.company_id = u.user_id
                JOIN users s ON a.student_id = s.user_id
                WHERE a.application_id = %s
            """, (application_id,))
            application = cursor.fetchone()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {"application": application, "success": True}
    finally:
        conn.close()

@app.get("/api/company/applications/{company_id}")
def get_company_applications(company_id: int):
    """Get all applications for internships posted by a company"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.application_id, 
                    a.internship_id, 
                    a.experience, 
                    a.knowledge, 
                    a.documents, 
                    a.status, 
                    a.applied_at,
                    i.title as internship_title,
                    i.skills_required as internship_skills,
                    u.name as student_name, 
                    u.email as student_email, 
                    u.mobile as student_mobile, 
                    u.skills as student_skills
                FROM applications a
                JOIN internships i ON a.internship_id = i.internship_id
                JOIN users u ON a.student_id = u.user_id
                WHERE i.company_id = %s
                ORDER BY a.applied_at DESC
            """, (company_id,))
            applications = cursor.fetchall()
        
        return {"applications": applications, "success": True}
    finally:
        conn.close()

@app.get("/api/internship/{internship_id}/applications")
def get_internship_applications(internship_id: int):
    """Get all applications for a specific internship"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.application_id, 
                    a.student_id,
                    a.experience, 
                    a.knowledge, 
                    a.documents, 
                    a.status, 
                    a.applied_at,
                    u.name as student_name,
                    u.email as student_email,
                    u.mobile as student_mobile,
                    u.skills as student_skills
                FROM applications a
                JOIN users u ON a.student_id = u.user_id
                WHERE a.internship_id = %s
                ORDER BY a.applied_at DESC
            """, (internship_id,))
            applications = cursor.fetchall()
        
        return {"applications": applications, "success": True}
    finally:
        conn.close()

@app.put("/api/applications/{application_id}/status")
def update_application_status(application_id: int, status: str = Form(...)):
    """Update application status (Select/Reject by company)"""
    if status not in ['Pending', 'Selected', 'Rejected']:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'Pending', 'Selected', or 'Rejected'")
    
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE applications SET status = %s WHERE application_id = %s", 
                (status, application_id)
            )
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Application not found")
        
        conn.commit()
        return {"message": f"Application status updated to {status}", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Status update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update status")
    finally:
        conn.close()

@app.put("/api/applications/bulk-update")
def bulk_update_application_status(updates: List[StatusUpdate]):
    """Bulk update multiple application statuses"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            for update in updates:
                if update.status not in ['Pending', 'Selected', 'Rejected']:
                    continue
                
                cursor.execute(
                    "UPDATE applications SET status = %s WHERE application_id = %s", 
                    (update.status, update.application_id)
                )
        
        conn.commit()
        return {"message": f"Updated {len(updates)} applications successfully", "success": True}
    except Exception as e:
        conn.rollback()
        print(f"Bulk update error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")
    finally:
        conn.close()

# ---------------- Statistics & Dashboard APIs ----------------

@app.get("/api/student/dashboard/{student_id}")
def get_student_dashboard_stats(student_id: int):
    """Get dashboard statistics for students"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Total applications
            cursor.execute(
                "SELECT COUNT(*) as total FROM applications WHERE student_id = %s",
                (student_id,)
            )
            total = cursor.fetchone()['total']
            
            # Pending applications
            cursor.execute(
                "SELECT COUNT(*) as pending FROM applications WHERE student_id = %s AND status = 'Pending'",
                (student_id,)
            )
            pending = cursor.fetchone()['pending']
            
            # Selected applications
            cursor.execute(
                "SELECT COUNT(*) as selected FROM applications WHERE student_id = %s AND status = 'Selected'",
                (student_id,)
            )
            selected = cursor.fetchone()['selected']
            
            # Rejected applications
            cursor.execute(
                "SELECT COUNT(*) as rejected FROM applications WHERE student_id = %s AND status = 'Rejected'",
                (student_id,)
            )
            rejected = cursor.fetchone()['rejected']
            
            # Available internships count
            cursor.execute("SELECT COUNT(*) as available FROM internships")
            available = cursor.fetchone()['available']
        
        return {
            "total_applications": total,
            "pending": pending,
            "selected": selected,
            "rejected": rejected,
            "available_internships": available,
            "success": True
        }
    finally:
        conn.close()

@app.get("/api/company/dashboard/{company_id}")
def get_company_dashboard_stats(company_id: int):
    """Get dashboard statistics for companies"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Total internships posted
            cursor.execute(
                "SELECT COUNT(*) as total FROM internships WHERE company_id = %s",
                (company_id,)
            )
            total_internships = cursor.fetchone()['total']
            
            # Total applications received
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM applications a
                JOIN internships i ON a.internship_id = i.internship_id
                WHERE i.company_id = %s
            """, (company_id,))
            total_applications = cursor.fetchone()['total']
            
            # Pending applications
            cursor.execute("""
                SELECT COUNT(*) as pending 
                FROM applications a
                JOIN internships i ON a.internship_id = i.internship_id
                WHERE i.company_id = %s AND a.status = 'Pending'
            """, (company_id,))
            pending = cursor.fetchone()['pending']
            
            # Selected students
            cursor.execute("""
                SELECT COUNT(*) as selected 
                FROM applications a
                JOIN internships i ON a.internship_id = i.internship_id
                WHERE i.company_id = %s AND a.status = 'Selected'
            """, (company_id,))
            selected = cursor.fetchone()['selected']
        
        return {
            "total_internships": total_internships,
            "total_applications": total_applications,
            "pending_applications": pending,
            "selected_students": selected,
            "success": True
        }
    finally:
        conn.close()

# ---------------- Startup Event ----------------
@app.on_event("startup")
async def startup_event():
    """Check database connection on startup"""
    try:
        conn = get_db()
        conn.close()
        print("=" * 50)
        print("✅ Database connection successful!")
        print("✅ Server is running on http://localhost:8000")
        print("=" * 50)
    except Exception as e:
        print("=" * 50)
        print("❌ Database connection failed:", e)
        print("=" * 50)

# ---------------- Main Entry Point ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)