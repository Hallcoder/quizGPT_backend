from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.models.quiz import Quiz, Question, QuizAttempt, Response
from app.schemas.quiz import (
    QuizGenerationRequest, QuizResponse, QuizForStudent,
    QuizSubmission, QuizResult, DifficultyLevel, QuestionType
)
from app.services.file_processor import FileProcessor
from app.services.quiz_generator import quiz_generator
from app.services.grading_service import grading_service

router = APIRouter()


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    content: Optional[str] = Form(None),
    content_type: str = Form(...),
    difficulty: DifficultyLevel = Form(DifficultyLevel.MEDIUM),
    num_questions: int = Form(10),
    question_types: str = Form("multiple_choice"),  # Comma-separated
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Generate a quiz from various content sources

    - **content**: Text content or URL (for text/url types)
    - **content_type**: Type of content (text, url, pdf, image)
    - **file**: Uploaded file (for pdf/image types)
    - **difficulty**: Difficulty level (easy, medium, hard)
    - **num_questions**: Number of questions to generate
    - **question_types**: Comma-separated question types
    """

    try:
        # Parse question types
        question_type_list = [
            QuestionType(qt.strip())
            for qt in question_types.split(",")
        ]

        # Process content based on type
        file_path = None
        if content_type in ["pdf", "image"]:
            if not file:
                raise HTTPException(status_code=400, detail="File required for PDF/image")
            file_path = await FileProcessor.save_upload_file(file)
            processed_content = await FileProcessor.process_content(content, content_type, file_path)
        else:
            if not content:
                raise HTTPException(status_code=400, detail="Content required for text/URL")
            processed_content = await FileProcessor.process_content(content, content_type)

        # Create generation request
        gen_request = QuizGenerationRequest(
            content=processed_content,
            content_type=content_type,
            difficulty=difficulty,
            num_questions=num_questions,
            question_types=question_type_list
        )

        # Generate quiz using GPT
        quiz_data = await quiz_generator.generate_quiz(processed_content, gen_request)

        # Save to database
        db_quiz = Quiz(
            title=quiz_data["title"],
            description=quiz_data["description"],
            source_type=content_type,
            source_content=processed_content[:500],  # Store first 500 chars
            difficulty=difficulty
        )
        db.add(db_quiz)
        db.flush()

        # Save questions
        for idx, question in enumerate(quiz_data["questions"]):
            options_json = None
            if question.options:
                options_json = json.dumps([
                    {"id": opt.id, "text": opt.text}
                    for opt in question.options
                ])

            db_question = Question(
                quiz_id=db_quiz.id,
                question_type=question.question_type,
                question_text=question.question_text,
                options=options_json,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                points=question.points,
                order=idx
            )
            db.add(db_question)

        db.commit()
        db.refresh(db_quiz)

        return db_quiz

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}", response_model=QuizForStudent)
async def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """
    Get a quiz for taking (without answers)
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return quiz


@router.get("/{quiz_id}/full", response_model=QuizResponse)
async def get_quiz_with_answers(quiz_id: int, db: Session = Depends(get_db)):
    """
    Get full quiz including answers (for review/admin)
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return quiz


@router.post("/submit", response_model=QuizResult)
async def submit_quiz(
    submission: QuizSubmission,
    db: Session = Depends(get_db)
):
    """
    Submit quiz answers and get results with automatic grading
    """

    # Get quiz and questions
    quiz = db.query(Quiz).filter(Quiz.id == submission.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Create quiz attempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=submission.user_id or "anonymous"
    )
    db.add(attempt)
    db.flush()

    # Prepare data for grading
    questions_data = []
    user_answers = {}

    for question in quiz.questions:
        options = None
        if question.options:
            options = json.loads(question.options)

        questions_data.append({
            "id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "points": question.points,
            "options": options
        })

    for answer in submission.answers:
        user_answers[answer.question_id] = answer.user_answer

    # Grade the quiz
    grading_result = await grading_service.grade_quiz(questions_data, user_answers)

    # Save responses
    for response_data in grading_result["responses"]:
        db_response = Response(
            attempt_id=attempt.id,
            question_id=response_data["question_id"],
            user_answer=response_data["user_answer"],
            is_correct=1 if response_data["is_correct"] else 0,
            points_earned=response_data["points_earned"],
            feedback=response_data["feedback"]
        )
        db.add(db_response)

    # Update attempt with score
    attempt.score = grading_result["points_earned"]
    attempt.total_points = grading_result["total_points"]
    attempt.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "score": attempt.score,
        "total_points": attempt.total_points,
        "percentage": grading_result["percentage"],
        "responses": grading_result["responses"],
        "completed_at": attempt.completed_at
    }


@router.get("/list", response_model=List[QuizResponse])
async def list_quizzes(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all quizzes
    """
    quizzes = db.query(Quiz).offset(skip).limit(limit).all()
    return quizzes


@router.delete("/{quiz_id}")
async def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """
    Delete a quiz
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    db.delete(quiz)
    db.commit()

    return {"message": "Quiz deleted successfully"}
