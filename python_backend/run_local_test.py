import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.users.models import User
from app.assessment.services.assessment_service import AssessmentService
from app.assessment.schemas.assessment import AssessmentCreateRequest
from app.assessment.models.assessment import AssessmentQuestion, AssessmentIntern, Question, AssessmentStatusEnum

def main():
    db = SessionLocal()
    ass_service = AssessmentService(db)
    
    print("--- PART 1 & 4 & 5: VERIFY ASSESSMENT QUESTIONS ---")
    
    # 1. Get Odd or Even question
    q = db.query(Question).filter(Question.title.ilike("%Odd%")).first()
    if not q:
        q = db.query(Question).first()
    
    if not q:
        print("FAIL: No questions found in DB.")
        return
        
    print(f"PASS: Found question '{q.title}' (ID: {q.id})")
    
    # 2. Create Assessment manually (AI selection OFF)
    req = AssessmentCreateRequest(
        title="Final Validation Assessment",
        duration_minutes=30,
        total_questions=1,
        difficulty_distribution={},
        ai_selection_enabled=False,
        question_ids=[q.id],
        question_bank_id=q.question_bank_id
    )
    
    try:
        ass = ass_service.create_assessment(req)
        print(f"PASS: Created Assessment ID: {ass.id} (Status: {ass.status})")
    except Exception as e:
        print(f"FAIL: Assessment creation failed: {e}")
        return
        
    # Verify mapping exists
    aqs = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == ass.id).all()
    if not aqs:
        print("FAIL: No rows in assessment_questions for newly created assessment!")
    else:
        print(f"PASS: Found {len(aqs)} rows in assessment_questions.")
        
    # 3. Publish Assessment
    try:
        ass = ass_service.publish_assessment(ass.id)
        print(f"PASS: Published Assessment. New Status: {ass.status}")
    except Exception as e:
        print(f"FAIL: Publish failed: {e}")
        
    print("\n--- PART 1 & 6: FIX ASSIGNMENT PERSISTENCE ---")
    
    # 4. Get Intern
    intern = db.query(User).filter(User.email == "intern@test.com").first()
    if not intern:
        print("FAIL: intern@test.com not found in public.users")
        return
    print(f"PASS: Found intern id={intern.id}, role={intern.role}")
    
    # 5. Assign
    try:
        assignment = ass_service.assign_assessment(ass.id, intern.id)
        print(f"PASS: Assignment returned object with ID: {assignment.id}")
    except Exception as e:
        print(f"FAIL: assign_assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return
        
    # 6. Verify in DB
    db.expire_all()
    rows = db.query(AssessmentIntern).filter(AssessmentIntern.id == assignment.id).all()
    if not rows:
        print("FAIL: DB query for assessment_interns returned EMPTY after assign_assessment!")
    else:
        print("PASS: DB query verified assessment_interns row EXISTS.")
        
    # Print state
    print("\n--- FINAL DB STATE ---")
    print(f"assessment_questions count for {ass.id}:", len(aqs))
    print(f"assessment_interns count for {ass.id}:", len(rows))

if __name__ == "__main__":
    main()
