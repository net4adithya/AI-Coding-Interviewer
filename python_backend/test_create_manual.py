import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.assessment.services.assessment_service import AssessmentService
from app.assessment.schemas.assessment import AssessmentCreateRequest

db = SessionLocal()
service = AssessmentService(db)

# Find an existing question
from app.assessment.models.assessment import Question
q = db.query(Question).first()
if not q:
    print("No questions found!")
    sys.exit(1)

req = AssessmentCreateRequest(
    title="Test Manual Assignment",
    duration_minutes=30,
    total_questions=1,
    difficulty_distribution={},
    ai_selection_enabled=False,
    question_ids=[q.id]
)

try:
    assessment = service.create_assessment(req)
    print("Assessment Created:", assessment.id, "Status:", assessment.status)
    
    # Check assessment_questions
    from app.assessment.models.assessment import AssessmentQuestion
    aqs = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).all()
    print("AssessmentQuestions count:", len(aqs))
    for aq in aqs:
        print("  - QID:", aq.question_id)
        
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
