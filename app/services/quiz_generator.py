import json
from typing import List, Dict
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.quiz import (
    QuestionType, DifficultyLevel, QuestionCreate,
    QuestionOption, QuizGenerationRequest
)


class QuizGenerator:
    """Service for generating quizzes using GPT"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_quiz(
        self,
        content: str,
        request: QuizGenerationRequest
    ) -> Dict:
        """Generate a quiz from content using GPT"""

        system_prompt = self._build_system_prompt(request)
        user_prompt = self._build_user_prompt(content, request)

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            quiz_data = json.loads(response.choices[0].message.content)
            return self._format_quiz_data(quiz_data, request)

        except Exception as e:
            raise Exception(f"Failed to generate quiz: {str(e)}")

    def _build_system_prompt(self, request: QuizGenerationRequest) -> str:
        """Build system prompt for GPT"""

        question_types_str = ", ".join([qt.value for qt in request.question_types])

        return f"""You are an expert quiz creator. Your task is to generate educational quiz questions based on provided content.

Guidelines:
- Difficulty level: {request.difficulty.value}
- Number of questions: {request.num_questions}
- Question types: {question_types_str}
- Create clear, unambiguous questions
- For multiple choice, provide 4 options with only one correct answer. Set "correct_answer" to the option id (a, b, c, or d)
- For true/false questions:
  * Write a clear statement as the question
  * Set "correct_answer" to exactly "True" or "False" (the answer to whether the statement is true)
  * Do NOT include options field for true/false questions
- Include explanations for correct answers
- Make questions test understanding, not just memorization

IMPORTANT for True/False:
- If the statement in question_text is TRUE, set correct_answer to "True"
- If the statement in question_text is FALSE, set correct_answer to "False"
- Example: If question is "Python is a programming language" -> correct_answer is "True"
- Example: If question is "Python was created in 1950" -> correct_answer is "False"

Return a JSON object with this structure:
{{
    "title": "Quiz title",
    "description": "Brief description",
    "questions": [
        {{
            "question_type": "multiple_choice|true_false|short_answer|fill_in_blank",
            "question_text": "The question text",
            "options": [{{"id": "a", "text": "Option text"}}],  // Only for multiple_choice
            "correct_answer": "The correct answer (for T/F use 'True' or 'False')",
            "explanation": "Why this is correct",
            "points": 1
        }}
    ]
}}"""

    def _build_user_prompt(self, content: str, request: QuizGenerationRequest) -> str:
        """Build user prompt with content"""

        # Truncate content if too long (to avoid token limits)
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        return f"""Generate a {request.difficulty.value} difficulty quiz with {request.num_questions} questions from this content:

{content}

Create questions that test deep understanding of the material."""

    def _format_quiz_data(self, quiz_data: Dict, request: QuizGenerationRequest) -> Dict:
        """Format and validate quiz data from GPT response"""

        formatted_questions = []

        for idx, q in enumerate(quiz_data.get("questions", [])):
            question_type = QuestionType(q["question_type"])

            # Format options for multiple choice
            options = None
            if question_type == QuestionType.MULTIPLE_CHOICE and "options" in q:
                options = [
                    QuestionOption(id=opt["id"], text=opt["text"])
                    for opt in q["options"]
                ]

            formatted_question = QuestionCreate(
                question_type=question_type,
                question_text=q["question_text"],
                options=options,
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation", ""),
                points=q.get("points", 1)
            )

            formatted_questions.append(formatted_question)

        return {
            "title": quiz_data.get("title", "Generated Quiz"),
            "description": quiz_data.get("description", ""),
            "difficulty": request.difficulty,
            "questions": formatted_questions
        }


# Singleton instance
quiz_generator = QuizGenerator()
