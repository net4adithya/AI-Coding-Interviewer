# python_backend/app/assessment/selection/gemini.py
import json
import logging
from typing import List
import google.generativeai as genai

from app.config import settings
from app.assessment.models.assessment import Assessment, Question
from app.assessment.selection.base import BaseQuestionSelectionProvider

logger = logging.getLogger(__name__)

class GeminiQuestionSelectionProvider(BaseQuestionSelectionProvider):
    """Uses Google Gemini to select an optimal set of questions based on constraints."""
    
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", None)
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Default to pro model for reasoning
            self.model = genai.GenerativeModel("gemini-1.5-pro")
        else:
            self.model = None

    async def select_questions(
        self,
        assessment: Assessment,
        eligible_questions: List[Question],
        **kwargs
    ) -> List[int]:
        if not self.model:
            raise ValueError("Gemini API key is not configured.")

        # Prepare pool
        pool_data = [
            {
                "id": q.id,
                "title": q.title,
                "topic": q.topic,
                "difficulty": q.difficulty.value,
                "expected_time_minutes": q.expected_time_minutes
            }
            for q in eligible_questions
        ]

        prompt = (
            "You are an expert technical interviewer AI. Your task is to select a subset of questions from the provided pool "
            "that EXACTLY match the requested constraints.\n\n"
            f"### Assessment Constraints:\n"
            f"- Total Questions: {assessment.total_questions}\n"
            f"- Exact Difficulty Distribution: {json.dumps(assessment.difficulty_distribution)}\n"
            f"- Target Total Duration (mins): {assessment.duration_minutes}\n\n"
            f"### Eligible Question Pool:\n{json.dumps(pool_data, indent=2)}\n\n"
            "### Instructions:\n"
            "1. Select EXACTLY the requested number of questions for each difficulty.\n"
            "2. Ensure the sum of 'expected_time_minutes' of the selected questions is as close as possible to the Target Total Duration.\n"
            "3. DO NOT hallucinate IDs. Only use IDs from the Eligible Question Pool.\n"
            "4. Respond ONLY with a JSON array of integers representing the IDs of the selected questions. Do not include any other text.\n"
            "Example format: [1, 5, 12, 4]"
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Remove markdown formatting if the model wrapped the JSON
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            text = text.strip()
            
            selected_ids = json.loads(text)
            
            if not isinstance(selected_ids, list):
                raise ValueError("Response is not a JSON list.")
            
            return [int(x) for x in selected_ids]
            
        except Exception as e:
            logger.error(f"Gemini Question Selection failed: {str(e)}")
            raise ValueError(f"Gemini selection failed: {str(e)}")
