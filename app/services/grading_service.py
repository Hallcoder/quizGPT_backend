from typing import List, Dict
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.quiz import QuestionType


class GradingService:
    """Service for automatic grading of quiz responses"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def grade_answer(
        self,
        question_text: str,
        question_type: QuestionType,
        correct_answer: str,
        user_answer: str,
        explanation: str = None
    ) -> Dict:
        """Grade a single answer and provide feedback"""

        if question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]:
            # Exact match for MC and T/F
            import logging
            logger = logging.getLogger(__name__)

            normalized_user = self._normalize_answer(user_answer)
            normalized_correct = self._normalize_answer(correct_answer)

            logger.info(f"Grading - Question: {question_text[:50]}...")
            logger.info(f"User answer: '{user_answer}' (normalized: '{normalized_user}')")
            logger.info(f"Correct answer: '{correct_answer}' (normalized: '{normalized_correct}')")

            is_correct = normalized_user == normalized_correct
            points_earned = 1.0 if is_correct else 0.0

            logger.info(f"Result: {'CORRECT' if is_correct else 'INCORRECT'}")

            return {
                "is_correct": is_correct,
                "points_earned": points_earned,
                "feedback": explanation if not is_correct else "Correct! " + (explanation or "")
            }

        else:
            # Use GPT for grading short answer and fill-in-blank
            return await self._grade_with_gpt(
                question_text,
                correct_answer,
                user_answer,
                explanation
            )

    async def _grade_with_gpt(
        self,
        question_text: str,
        correct_answer: str,
        user_answer: str,
        explanation: str = None
    ) -> Dict:
        """Use GPT to grade open-ended responses"""

        prompt = f"""You are a fair and consistent quiz grader. Grade the following answer:

Question: {question_text}

Expected Answer: {correct_answer}

Student's Answer: {user_answer}

Evaluate if the student's answer is correct. Consider:
- Semantic equivalence (same meaning, different words)
- Key concepts covered
- Factual accuracy
- Partial credit for partially correct answers

Return a JSON object:
{{
    "is_correct": true/false,
    "points_earned": 0.0-1.0,  // 0 for wrong, 1 for fully correct, 0.5 for partial
    "feedback": "Brief explanation of grading decision"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert educational grader."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            # Fallback to simple comparison if GPT fails
            is_correct = self._normalize_answer(user_answer) == self._normalize_answer(correct_answer)
            return {
                "is_correct": is_correct,
                "points_earned": 1.0 if is_correct else 0.0,
                "feedback": "Grading completed."
            }

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        """Normalize answer for comparison"""
        return answer.strip().lower()

    async def grade_quiz(
        self,
        questions_data: List[Dict],
        user_answers: Dict[int, str]
    ) -> Dict:
        """Grade entire quiz and calculate score"""

        total_points = 0
        points_earned = 0
        responses = []

        for question in questions_data:
            question_id = question["id"]
            user_answer = user_answers.get(question_id, "")

            # Grade the answer
            result = await self.grade_answer(
                question["question_text"],
                question["question_type"],
                question["correct_answer"],
                user_answer,
                question.get("explanation")
            )

            total_points += question.get("points", 1)
            points_earned += result["points_earned"] * question.get("points", 1)

            responses.append({
                "question_id": question_id,
                "user_answer": user_answer,
                "is_correct": result["is_correct"],
                "correct_answer": question["correct_answer"],
                "explanation": question.get("explanation"),
                "points_earned": result["points_earned"] * question.get("points", 1),
                "feedback": result["feedback"]
            })

        percentage = (points_earned / total_points * 100) if total_points > 0 else 0

        return {
            "total_points": total_points,
            "points_earned": points_earned,
            "percentage": round(percentage, 2),
            "responses": responses
        }


# Singleton instance
grading_service = GradingService()
