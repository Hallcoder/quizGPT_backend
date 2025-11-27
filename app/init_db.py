from app.core.database import Base, engine
from app.models.quiz import Quiz, Question, QuizAttempt, Response


def init_db():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
