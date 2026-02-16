# Owen's Learn Agent – Copilot Instructions

## Project Overview

This is **Owen's Learn Agent**, an AI-powered math tutoring application built with:

- **Backend**: Python 3.13, FastAPI, async
- **AI**: Azure AI Foundry / Azure OpenAI (gpt-4.1-mini) via the `openai` SDK
- **Frontend**: Vanilla HTML/CSS/JS with KaTeX (math rendering), Marked (markdown), and an HTML5 Canvas scratch pad
- **Architecture**: Service-layer pattern with in-memory stores (designed for future database swap)

## Project Structure

```
app/
├── main.py              → FastAPI app, middleware, route registration, static files
├── config.py            → Pydantic Settings from .env
├── azure_client.py      → Singleton OpenAI client factory (supports AI Foundry + standard Azure OpenAI)
├── models.py            → Pydantic domain models (ChatMessage, QuizQuestion, StudentProfile, etc.)
├── prompts.py           → System prompts and LLM prompt templates
├── routes/
│   ├── chat.py          → POST /api/chat/, GET /api/chat/{id}/history, DELETE /api/chat/{id}
│   ├── quiz.py          → POST /api/quiz/generate, POST /api/quiz/submit
│   └── progress.py      → GET /api/progress/{id}, POST /api/progress/{id}/difficulty
└── services/
    ├── chat_service.py      → Multi-turn conversation with session management
    ├── quiz_service.py      → AI quiz generation + grading
    └── progress_service.py  → Student progress tracking + adaptive difficulty
static/
├── index.html           → SPA shell with sidebar nav, 4 tabs
├── style.css            → Dark theme design system (CSS custom properties)
└── app.js               → Tab routing, chat, quiz, scratch pad canvas, progress cards
tests/
├── test_models.py       → Unit tests for domain models
└── test_progress.py     → Unit tests for progress service (no LLM calls)
```

## Key Conventions

1. **Async everywhere** – All service functions that call Azure OpenAI are `async`. Routes use `async def`.
2. **Pydantic models** – Every API request/response has a Pydantic model in `models.py`.
3. **Service layer** – Routes are thin; business logic lives in `services/`.
4. **In-memory stores** – `_sessions`, `_questions`, `_students` dicts. These are designed to be swapped for a real database later (Cosmos DB, SQLite, etc.).
5. **Prompt templates** – All LLM prompts live in `prompts.py` using Python format strings.
6. **Config via .env** – All secrets and settings come from environment variables via `config.py`.
7. **Azure client auto-detection** – `azure_client.py` detects whether the endpoint is Azure AI Foundry (`services.ai.azure.com`) or standard Azure OpenAI and configures the right SDK client.

## When Modifying Code

- **Adding a new API endpoint**: Create route in `app/routes/`, add service function in `app/services/`, register the router in `app/main.py`.
- **Adding a new LLM feature**: Add prompt template to `prompts.py`, service logic in appropriate service file.
- **Adding a new model**: Define in `models.py` with Pydantic, use in both route and service.
- **Frontend changes**: All in `static/`. Use `renderContent()` in `app.js` for any text that might contain math/markdown.
- **Tests**: Add to `tests/`. Offline tests (no LLM) should test service logic directly.

## Code Style

- Python: Ruff formatter, line length 100, type hints everywhere
- JS: Vanilla ES6+, no build step, DOM manipulation
- CSS: Custom properties in `:root`, BEM-ish class names

## Owen's Learning Context

Owen is learning to build AI agents. When helping him:
- Explain **why** something works, not just what to change
- Point to relevant files and functions when discussing architecture
- Suggest incremental improvements he can try himself
- Use the prompt files in `.github/prompts/` for guided tasks
