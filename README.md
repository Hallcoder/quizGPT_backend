# QuizGPT Backend

FastAPI backend for AI-powered quiz generation.

## Setup

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Random secret key for security

### 3. Start Database

Using Docker:

```bash
cd ..
docker-compose up -d
```

### 4. Initialize Database

```bash
poetry run python -m app.init_db
```

### 5. Run Development Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Quiz Generation

**POST /api/quiz/generate**

Generate a quiz from content (text, URL, PDF, or image).

```bash
# Text content
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -F "content=Your learning content here" \
  -F "content_type=text" \
  -F "difficulty=medium" \
  -F "num_questions=10" \
  -F "question_types=multiple_choice"

# PDF file
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -F "file=@document.pdf" \
  -F "content_type=pdf" \
  -F "difficulty=hard" \
  -F "num_questions=15"

# URL
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -F "content=https://example.com/article" \
  -F "content_type=url" \
  -F "difficulty=easy"
```

### Get Quiz

**GET /api/quiz/{quiz_id}**

Get quiz for taking (without answers).

```bash
curl "http://localhost:8000/api/quiz/1"
```

### Submit Quiz

**POST /api/quiz/submit**

Submit answers and get automatic grading.

```bash
curl -X POST "http://localhost:8000/api/quiz/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "quiz_id": 1,
    "user_id": "user123",
    "answers": [
      {"question_id": 1, "user_answer": "A"},
      {"question_id": 2, "user_answer": "True"}
    ]
  }'
```

### List Quizzes

**GET /api/quiz/list**

```bash
curl "http://localhost:8000/api/quiz/list?skip=0&limit=10"
```

## Features

### Content Processing

- **Text**: Direct text input
- **URLs**: Web scraping with BeautifulSoup
- **PDFs**: Text extraction with pdfplumber and PyPDF2
- **Images**: OCR with Tesseract

### Question Types

- Multiple Choice
- True/False
- Short Answer
- Fill in the Blank

### Difficulty Levels

- Easy
- Medium
- Hard

### Automatic Grading

- Exact matching for multiple choice and true/false
- AI-powered grading for short answer questions
- Detailed feedback and explanations

## Development

### Run Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black app/
```

### Linting

```bash
poetry run flake8 app/
```

### Type Checking

```bash
poetry run mypy app/
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   │   ├── quiz.py
│   │   └── upload.py
│   ├── core/             # Core configuration
│   │   ├── config.py
│   │   └── database.py
│   ├── models/           # Database models
│   │   └── quiz.py
│   ├── schemas/          # Pydantic schemas
│   │   └── quiz.py
│   ├── services/         # Business logic
│   │   ├── file_processor.py
│   │   ├── quiz_generator.py
│   │   └── grading_service.py
│   ├── utils/            # Utilities
│   ├── init_db.py        # Database initialization
│   └── main.py           # FastAPI app
├── pyproject.toml        # Poetry dependencies
├── .env.example          # Environment template
└── README.md
```

## Environment Variables

See `.env.example` for all available configuration options.

## Troubleshooting

### Tesseract not found

Install Tesseract OCR:

**macOS:**
```bash
brew install tesseract
```

**Ubuntu:**
```bash
sudo apt-get install tesseract-ocr
```

### Database connection issues

Make sure PostgreSQL is running:
```bash
docker-compose ps
```

Check connection string in `.env`
