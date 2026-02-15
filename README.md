# Owen's Learn Agent

An AI-powered tutoring agent built with **Python**, **FastAPI**, and **Azure AI Foundry / Azure OpenAI**.

## Features

- **Conversational Chat** – Multi-turn Socratic tutoring powered by Azure OpenAI (GPT-4o)
- **Quiz Generation** – AI-generated multiple-choice quizzes on any subject/topic
- **Progress Tracking** – Track attempts, accuracy, and knowledge gaps per topic
- **Adaptive Difficulty** – LLM-driven difficulty recommendations based on student performance
- **Web UI** – Clean dark-mode single-page app for interacting with the tutor

## Project Structure

```
OwensLearnAgent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py             # Settings from .env
│   ├── azure_client.py       # Azure OpenAI client factory
│   ├── models.py             # Pydantic domain models
│   ├── prompts.py            # System prompts & templates
│   ├── routes/
│   │   ├── chat.py           # POST /api/chat/
│   │   ├── quiz.py           # POST /api/quiz/generate, /api/quiz/submit
│   │   └── progress.py       # GET /api/progress/{id}
│   └── services/
│       ├── chat_service.py   # Conversation management
│       ├── quiz_service.py   # Quiz generation & grading
│       └── progress_service.py  # Student progress & adaptive difficulty
├── static/
│   ├── index.html            # Web UI
│   ├── style.css
│   └── app.js
├── tests/
│   ├── test_models.py
│   └── test_progress.py
├── pyproject.toml
├── .env.sample
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- An Azure OpenAI resource with a GPT-4o deployment

### Setup

1. **Create a virtual environment and install dependencies:**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -e ".[dev]"
   ```

2. **Configure environment variables:**

   ```bash
   copy .env.sample .env
   ```

   Edit `.env` with your Azure OpenAI endpoint and deployment name.
   
   **Authentication** uses `DefaultAzureCredential` by default (recommended).  
   Run `az login` first, or set `AZURE_OPENAI_API_KEY` for key-based auth.

3. **Run the server:**

   ```bash
   uvicorn app.main:app --reload
   ```

   Open [http://localhost:8000](http://localhost:8000) in your browser.

### Run Tests

```bash
pytest
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/` | Send a message, get a tutor reply |
| GET | `/api/chat/{session_id}/history` | Get conversation history |
| DELETE | `/api/chat/{session_id}` | Clear a chat session |
| POST | `/api/quiz/generate` | Generate quiz questions |
| POST | `/api/quiz/submit` | Submit & grade an answer |
| GET | `/api/progress/{student_id}` | Get student progress |
| POST | `/api/progress/{student_id}/difficulty` | Get AI difficulty recommendation |
| GET | `/health` | Health check |

## Next Steps

- [ ] Persist data to Azure Cosmos DB
- [ ] Add Azure AI Foundry agent orchestration
- [ ] Add document/PDF ingestion for custom study material
- [ ] Deploy to Azure Container Apps
- [ ] Add authentication with Microsoft Entra ID
