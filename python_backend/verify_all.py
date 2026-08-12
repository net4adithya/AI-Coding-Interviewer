import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from app.db.session import SessionLocal
from app.users.models import User, RoleEnum
from main import app
from fastapi.testclient import TestClient
from app.api.dependencies import get_current_user

def run_tests():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    
    print("Starting Validations...\n")
    
    # 1. Supabase Pooler Connection / SQLAlchemy / SELECT 1
    pooler_pass = False
    sa_pass = False
    select1_pass = False
    if db_url and "5432" in db_url:
        pooler_pass = True
        
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            sa_pass = True
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                select1_pass = True
    except Exception as e:
        print(f"DB Error: {e}")
        
    # 2. Alembic
    alembic_pass = False
    try:
        alembic_res = subprocess.run(["venv\\Scripts\\alembic", "history"], capture_output=True, text=True)
        if alembic_res.returncode == 0:
            alembic_pass = True
        else:
            print(f"Alembic Error: {alembic_res.stderr}")
    except Exception as e:
        print(f"Alembic Exception: {e}")

    # 3. Database Queries (Verify both existing users)
    queries_pass = False
    authority_pass = False
    intern_pass = False
    db = None
    try:
        db = SessionLocal()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        intern_user = db.query(User).filter(User.email == "intern@test.com").first()
        queries_pass = True
        
        if admin_user and admin_user.role == RoleEnum.AUTHORITY:
            authority_pass = True
            
        if intern_user and intern_user.role == RoleEnum.INTERN:
            intern_pass = True
            
    except Exception as e:
        print(f"Query Error: {e}")
    finally:
        if db:
            db.close()
            
    # 4. /users/me endpoint and FastAPI startup and operations
    fastapi_pass = False
    users_me_pass = False
    operations_pass = True
    
    try:
        client = TestClient(app)
        fastapi_pass = True
        
        # Override get_current_user
        def override_get_current_user():
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.email == "admin@test.com").first()
                if not user:
                    user = User(email="admin@test.com", role=RoleEnum.AUTHORITY, supabase_uid="mock-uid")
                return user
            finally:
                db.close()
                
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        res = client.get("/users/me")
        if res.status_code == 200 and res.json().get("email") == "admin@test.com":
            users_me_pass = True
        else:
            print(f"/users/me failed: {res.status_code} {res.text}")
            
        # Verify operations don't 500 (DB failure)
        endpoints = [
            "/api/v1/assessments/",
            "/api/v1/editor/", # Question banks might be here
            "/assignments/",
            "/submissions/",
            "/authority-review/",
        ]
        
        for ep in endpoints:
            r = client.get(ep)
            if r.status_code >= 500:
                print(f"Operation endpoint {ep} returned {r.status_code}: {r.text}")
                operations_pass = False
                
    except Exception as e:
        print(f"FastAPI Error: {e}")
        fastapi_pass = False
        operations_pass = False
        
    # 5. Backend Tests
    pytest_pass = False
    try:
        pytest_res = subprocess.run(["venv\\Scripts\\pytest", "tests/"], capture_output=True, text=True)
        if pytest_res.returncode == 0:
            pytest_pass = True
        else:
            print(f"Pytest Error:\n{pytest_res.stdout}\n{pytest_res.stderr}")
    except Exception as e:
        print(f"Pytest Exception: {e}")
        
    print("\nFINAL REPORT:\n")
    print(f"Supabase Pooler Connection: {'PASS' if pooler_pass else 'FAIL'}")
    print(f"SQLAlchemy: {'PASS' if sa_pass else 'FAIL'}")
    print(f"SELECT 1: {'PASS' if select1_pass else 'FAIL'}")
    print(f"Alembic: {'PASS' if alembic_pass else 'FAIL'}")
    print(f"Database Queries: {'PASS' if queries_pass else 'FAIL'}")
    print(f"/users/me: {'PASS' if users_me_pass else 'FAIL'}")
    print(f"Authority Mapping: {'PASS' if authority_pass else 'FAIL'}")
    print(f"Intern Mapping: {'PASS' if intern_pass else 'FAIL'}")
    print(f"Backend Tests: {'PASS' if pytest_pass else 'FAIL'}")
    print(f"FastAPI Startup: {'PASS' if fastapi_pass else 'FAIL'}")
    
    all_passed = all([pooler_pass, sa_pass, select1_pass, alembic_pass, queries_pass, users_me_pass, authority_pass, intern_pass, pytest_pass, fastapi_pass, operations_pass])
    
    print("\nDATABASE STATUS:")
    print("READY" if all_passed else "NOT READY")

if __name__ == "__main__":
    run_tests()
