import requests
import json
import time

API_BASE = "http://localhost:8000"

def get_auth_token(email, password):
    url = "https://rfqmnstrnvipxknvrouy.supabase.co/auth/v1/token?grant_type=password"
    headers = {
        "apikey": "sb_publishable_f6Kciw9KKmJdJwC-lbpeGQ_gNqyVtcs",
        "Content-Type": "application/json"
    }
    data = {"email": email, "password": password}
    r = requests.post(url, headers=headers, json=data)
    if r.status_code != 200:
        raise Exception(f"Login failed for {email}: {r.text}")
    return r.json()["access_token"]

def main():
    print("--- PART 6: TEST AUTHORITY FLOW ---")
    
    # Login as authority
    try:
        auth_token = get_auth_token("admin@test.com", "Admin@123")
    except Exception as e:
        print(f"Auth error (maybe different password?): {e}")
        # Try lowercase password
        auth_token = get_auth_token("admin@test.com", "admin123")
        
    print("Logged in as Authority.")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Get banks
    r = requests.get(f"{API_BASE}/api/v1/assessments/question-banks", headers=headers)
    banks = r.json()
    if not banks:
        print("No question banks found.")
        return
    bank_id = banks[0]["id"]
    print(f"Using bank ID: {bank_id}")
    
    # Get questions
    r = requests.get(f"{API_BASE}/api/v1/assessments/question-banks/{bank_id}/questions", headers=headers)
    questions = r.json()
    if not questions:
        print("No questions found in bank.")
        return
    question_id = questions[0]["id"]
    print(f"Using question ID: {question_id} (Topic: {questions[0].get('topic')})")
    
    # Create Assessment (Manual selection)
    create_payload = {
        "title": "E2E Test Assessment",
        "duration_minutes": 45,
        "total_questions": 1,
        "difficulty_distribution": {},
        "ai_selection_enabled": False,
        "question_ids": [question_id],
        "question_bank_id": bank_id
    }
    r = requests.post(f"{API_BASE}/api/v1/assessments/", headers=headers, json=create_payload)
    if r.status_code != 200:
        print("Failed to create assessment:", r.text)
        return
    assessment = r.json()
    ass_id = assessment["id"]
    print(f"Created Assessment ID: {ass_id}, Status: {assessment['status']}")
    
    # Verify assessment questions mapping via preview
    r = requests.get(f"{API_BASE}/api/v1/assessments/{ass_id}/questions", headers=headers)
    ass_questions = r.json()
    print(f"Assessment {ass_id} has {len(ass_questions)} questions.")
    
    # Publish assessment
    r = requests.post(f"{API_BASE}/api/v1/assessments/{ass_id}/publish", headers=headers)
    if r.status_code != 200:
        print("Failed to publish assessment:", r.text)
        return
    print("Assessment published.")
    
    # Assign to intern
    assign_payload = {"email": "intern@test.com"}
    r = requests.post(f"{API_BASE}/api/v1/assessments/{ass_id}/assign-email", headers=headers, json=assign_payload)
    if r.status_code != 200:
        print("Failed to assign assessment:", r.text)
        return
    assignment = r.json()
    print(f"Assigned to intern successfully. Assignment ID: {assignment['id']}")
    
    print("\n--- PART 7: TEST INTERN FLOW ---")
    try:
        intern_token = get_auth_token("intern@test.com", "Intern@123")
    except:
        intern_token = get_auth_token("intern@test.com", "intern123")
    print("Logged in as Intern.")
    intern_headers = {"Authorization": f"Bearer {intern_token}"}
    
    # Get assigned assessment
    r = requests.get(f"{API_BASE}/api/v1/assessments/intern/me", headers=intern_headers)
    if r.status_code != 200:
        print("Intern get assessment failed:", r.text)
        return
    intern_ass = r.json()
    print(f"Intern retrieved assessment ID: {intern_ass['id']}, Title: {intern_ass['title']}")
    
    print("\n--- DONE ---")

if __name__ == "__main__":
    main()
