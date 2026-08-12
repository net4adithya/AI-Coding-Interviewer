import os
import sys

sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
from app.db.session import SessionLocal
from app.users.models import User, RoleEnum
from main import app
from fastapi.testclient import TestClient
from app.api.dependencies import get_current_user

def run_tests():
    load_dotenv()
    
    print("Testing Endpoints...\n")
    client = TestClient(app)
    
    # Override get_current_user as authority
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
    
    assessment_api_pass = True
    get_all_pass = False
    ass_creation_pass = False
    ass_details_pass = False
    ass_questions_pass = False
    assignment_retrieval_pass = False
    
    # 1. GET /api/v1/assessments/
    res = client.get("/api/v1/assessments/")
    if res.status_code == 200:
        get_all_pass = True
        assessments = res.json()
        print(f"GET /api/v1/assessments/: PASS ({len(assessments)} found)")
    else:
        print(f"GET /api/v1/assessments/: FAIL ({res.status_code} - {res.text})")
        assessment_api_pass = False

    # 2. Assessment creation
    payload = {
        "title": "Test Assessment",
        "description": "Test Desc",
        "duration_minutes": 60,
        "difficulty": "medium",
        "passing_score": 70,
        "total_questions": 10,
        "difficulty_distribution": {"easy": 3, "medium": 4, "hard": 3}
    }
    res = client.post("/api/v1/assessments/", json=payload)
    if res.status_code == 200:
        ass_creation_pass = True
        new_ass = res.json()
        ass_id = new_ass["id"]
        print(f"Assessment creation: PASS (ID: {ass_id})")
        
        # 3. Assessment details
        res = client.get(f"/api/v1/assessments/{ass_id}")
        if res.status_code == 200:
            ass_details_pass = True
            print("Assessment details: PASS")
        else:
            print(f"Assessment details: FAIL ({res.status_code} - {res.text})")
            assessment_api_pass = False
            
        # 4. Assessment/question retrieval
        res = client.get(f"/api/v1/assessments/{ass_id}/questions")
        if res.status_code == 200:
            ass_questions_pass = True
            print("Assessment/question retrieval: PASS")
        else:
            print(f"Assessment/question retrieval: FAIL ({res.status_code} - {res.text})")
            assessment_api_pass = False
    else:
        print(f"Assessment creation: FAIL ({res.status_code} - {res.text})")
        assessment_api_pass = False
        
    # 5. Assignment retrieval
    # For this, we test intern perspective
    def override_intern():
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == "intern@test.com").first()
            if not user:
                user = User(email="intern@test.com", role=RoleEnum.INTERN, supabase_uid="mock-intern")
            return user
        finally:
            db.close()
    app.dependency_overrides[get_current_user] = override_intern
    
    res = client.get("/api/v1/assessments/intern/me")
    if res.status_code in [200, 404]: # 404 is fine if not assigned
        assignment_retrieval_pass = True
        print(f"Assignment retrieval: PASS ({res.status_code})")
    else:
        print(f"Assignment retrieval: FAIL ({res.status_code} - {res.text})")
        assessment_api_pass = False
        
    print("\nFINAL REPORT:\n")
    print(f"Assessment API:\n{'PASS' if assessment_api_pass else 'FAIL'}\n")
    print(f"GET /api/v1/assessments/:\n{'PASS' if get_all_pass else 'FAIL'}\n")
    print(f"Assessment creation:\n{'PASS' if ass_creation_pass else 'FAIL'}\n")
    print(f"Assessment details:\n{'PASS' if ass_details_pass else 'FAIL'}\n")
    print(f"Assessment/question retrieval:\n{'PASS' if ass_questions_pass else 'FAIL'}\n")
    print(f"Assignment retrieval:\n{'PASS' if assignment_retrieval_pass else 'FAIL'}")

if __name__ == "__main__":
    run_tests()
