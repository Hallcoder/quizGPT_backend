from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum
import json


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_IN_BLANK = "fill_in_blank"


class QuizGenerationRequest(BaseModel):
    content: str
    content_type: str = Field(..., description="text, url, pdf, image")
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    num_questions: int = Field(default=10, ge=1, le=50)
    question_types: List[QuestionType] = Field(default=[QuestionType.MULTIPLE_CHOICE])


class QuestionOption(BaseModel):
    id: str
    text: str


class QuestionBase(BaseModel):
    question_type: QuestionType
    question_text: str
    options: Optional[List[QuestionOption]] = None
    correct_answer: str
    explanation: Optional[str] = None
    points: int = 1


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: int
    quiz_id: int
    order: int

    @field_validator("options", mode="before")
    @classmethod
    def parse_options(cls, v):
        if isinstance(v, str):
            parsed = json.loads(v)
            return [QuestionOption(**opt) for opt in parsed]
        return v

    class Config:
        from_attributes = True


class QuestionForStudent(BaseModel):
    """Question schema without correct answer for students"""
    id: int
    question_type: QuestionType
    question_text: str
    options: Optional[List[QuestionOption]] = None
    points: int

    @field_validator("options", mode="before")
    @classmethod
    def parse_options(cls, v):
        if isinstance(v, str):
            parsed = json.loads(v)
            return [QuestionOption(**opt) for opt in parsed]
        return v

    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM


class QuizCreate(QuizBase):
    source_type: str
    source_content: str
    questions: List[QuestionCreate]


class QuizResponse(QuizBase):
    id: int
    source_type: str
    created_at: datetime
    questions: List[QuestionResponse]

    class Config:
        from_attributes = True


class QuizForStudent(QuizBase):
    """Quiz schema for students (without answers)"""
    id: int
    source_type: str
    created_at: datetime
    questions: List[QuestionForStudent]

    class Config:
        from_attributes = True


class AnswerSubmission(BaseModel):
    question_id: int
    user_answer: str


class QuizSubmission(BaseModel):
    quiz_id: int
    user_id: Optional[str] = None
    answers: List[AnswerSubmission]


class ResponseFeedback(BaseModel):
    question_id: int
    user_answer: str
    is_correct: bool
    correct_answer: str
    explanation: Optional[str]
    points_earned: float


class QuizResult(BaseModel):
    attempt_id: int
    quiz_id: int
    score: float
    total_points: int
    percentage: float
    responses: List[ResponseFeedback]
    completed_at: datetime

    class Config:
        from_attributes = True
