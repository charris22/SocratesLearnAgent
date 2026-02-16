# Owen's Learn Agent — Developer Guide

Welcome, Owen! This guide walks you through how the tutoring agent works and how to extend it. You'll learn real software engineering patterns by building on top of working code.

---

## 🚀 Quick Start

```bash
# 1. Activate the virtual environment
.venv\Scripts\activate

# 2. Run the server
uvicorn app.main:app --reload

# 3. Open the app
# http://localhost:8000

# 4. Run tests
pytest -v
```

---

## How the App Works (The Big Picture)

```
User clicks "Send"
       │
       ▼
  static/app.js          ← Frontend: sends HTTP request
       │
       ▼
  app/routes/chat.py      ← Route: validates input, calls service
       │
       ▼
  app/services/chat_service.py  ← Service: builds prompt, calls LLM
       │
       ▼
  app/azure_client.py     ← Client: connects to Azure OpenAI
       │
       ▼
  Azure AI Foundry         ← LLM: generates response
       │
       ▼
  (reverse the path back to the browser)
```

Every request follows this same flow: **Frontend → Route → Service → Azure → Back**.

---

## Key Concepts You'll Learn

### 1. Async/Await (Python)

When we call Azure OpenAI, we wait for a response over the internet. Instead of blocking the entire server, `async/await` lets Python do other work while waiting.

```python
# Blocking (bad for a web server):
response = client.chat.completions.create(...)  # server frozen until response

# Async (what we use):
response = await client.chat.completions.create(...)  # server handles other requests while waiting
```

**Rule of thumb:** If a function calls Azure OpenAI or another async function, it must be `async def` and you must `await` the call.

### 2. Pydantic Models

Instead of passing around raw dictionaries, we define structured data classes:

```python
class ChatRequest(BaseModel):
    message: str                         # required string
    session_id: str = "default"          # optional with default
    subject: str = "general"             # optional with default
```

**Why?** FastAPI automatically validates incoming JSON against these models. If someone sends `{"message": 123}`, they get a clear error instead of a crash deep in your code.

### 3. The Service-Layer Pattern

```
Routes (thin)  →  Services (logic)  →  External APIs
```

- **Routes** (`app/routes/`): Handle HTTP — parse request, return response, set status codes
- **Services** (`app/services/`): Handle business logic — build prompts, process data, manage state
- **Why separate?** Services can be tested without HTTP. Routes can swap services. Each layer has one job.

### 4. Prompt Engineering

The LLM's behavior is controlled by the prompts in `app/prompts.py`. Think of the system prompt as the AI's "personality card" — it defines who it is and how it behaves.

```python
TUTOR_SYSTEM_PROMPT = """You are a friendly, encouraging math tutor...
- Use the Socratic method (ask guiding questions)
- Use LaTeX notation: \\( inline \\) and \\[ display \\]
..."""
```

Small changes to the prompt can dramatically change behavior. This is where you'll experiment the most.

---

## Project Structure Explained

| File | What It Does | When to Change It |
|------|-------------|-------------------|
| `app/config.py` | Loads `.env` settings into typed Python objects | Adding a new config value |
| `app/azure_client.py` | Creates the Azure OpenAI client (singleton) | Changing auth or endpoint logic |
| `app/models.py` | Defines all data structures (Pydantic) | Adding a new API or data type |
| `app/prompts.py` | All LLM prompt templates | Tuning AI behavior |
| `app/services/*.py` | Business logic (chat, quiz, progress) | Adding features or fixing bugs |
| `app/routes/*.py` | HTTP handlers (thin wrappers) | Adding new API endpoints |
| `app/main.py` | App startup, middleware, route registration | Registering new routers |
| `static/index.html` | Page layout and structure | Adding UI sections |
| `static/style.css` | Visual theme (dark mode, colors, layout) | Changing appearance |
| `static/app.js` | Interactivity, API calls, rendering | Adding UI behavior |
| `tests/*.py` | Automated tests | Verifying your changes work |

---

## How to Use Copilot Agent Mode

In VS Code, open Copilot Chat and switch to **Agent** mode. Then you can:

### Reference prompt files with `#`
Type `#` and select a prompt file to get guided help:
- `#add-endpoint` — Walk through adding a new API
- `#add-llm-feature` — Add a feature that uses Azure OpenAI
- `#add-frontend-feature` — Add something to the UI
- `#understand-codebase` — Get a guided architecture tour
- `#debug-issue` — Systematic debugging help
- `#write-tests` — Learn testing patterns
- `#add-database` — Add persistence (replace in-memory stores)
- `#improve-prompts` — Make the AI tutor smarter

### Ask questions about the code
Copilot knows about this project (via `.github/copilot-instructions.md`) and will reference the right files.

### Let the agent make changes
In agent mode, Copilot can:
- Read your code and explain it
- Create new files
- Edit existing files
- Run terminal commands
- Run tests to verify changes

---

## Common Development Tasks

### Starting the server
```bash
.venv\Scripts\activate
uvicorn app.main:app --reload
```
The `--reload` flag restarts the server when you save a Python file.

### Running tests
```bash
pytest -v                    # all tests, verbose
pytest tests/test_models.py  # one file
pytest -k "test_accuracy"    # one test by name
```

### Testing an API endpoint manually
Visit `http://localhost:8000/docs` — FastAPI generates interactive API docs automatically.

### Checking for errors
```bash
ruff check app/              # lint check
ruff format app/             # auto-format
```

---

## Debugging Tips

1. **Check the terminal** — Python errors appear in the terminal running uvicorn
2. **Check the browser console** — JavaScript errors appear in F12 → Console
3. **Check the Network tab** — F12 → Network shows API calls, status codes, and response bodies
4. **Use `/docs`** — Test API endpoints without the frontend at `http://localhost:8000/docs`
5. **Add print()** — Quick debugging: `print(f"DEBUG: {variable}")` in Python
6. **Read error messages carefully** — They usually tell you exactly what went wrong and where

---

## What's Coming Next

Check `BACKLOG.md` for a list of tasks you can tackle, organized by difficulty. Each one teaches a different skill. Start with "Easy" and work your way up!

---

## Getting Help

1. **Ask Copilot** — Use the prompt files above for structured guidance
2. **Read the error** — Most errors tell you what's wrong
3. **Search the code** — Use Ctrl+Shift+F to find where something is used
4. **Check the FastAPI docs** — https://fastapi.tiangolo.com/
5. **Check the OpenAI docs** — https://platform.openai.com/docs/api-reference
