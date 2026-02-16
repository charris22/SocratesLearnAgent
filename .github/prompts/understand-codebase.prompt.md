---
mode: agent
description: "Understand the codebase — architecture walkthrough for learning"
---

# Understand the Codebase

Owen wants to understand how the tutoring agent works. Walk through the architecture by reading the actual code and explaining it.

## Tour order (read each file and explain):

1. **`app/config.py`** – How environment variables become typed Python settings
   - What is pydantic-settings? Why not just `os.environ`?
   - The `@lru_cache` pattern for singletons

2. **`app/azure_client.py`** – How we connect to Azure OpenAI
   - Singleton pattern with `_client` global
   - Auto-detection of AI Foundry vs standard endpoints
   - `DefaultAzureCredential` vs API key auth — when to use each

3. **`app/models.py`** – Domain modeling with Pydantic
   - How `BaseModel` gives us validation, serialization, docs
   - Enums for fixed choices (`Difficulty`, `Role`)
   - Computed properties (`accuracy`)

4. **`app/prompts.py`** – Prompt engineering
   - System prompt structure and principles
   - JSON-mode prompts for structured output
   - Format strings with `{{` escaping for literal braces

5. **`app/services/chat_service.py`** – How conversations work
   - Session management with in-memory dict
   - Building the messages array for the API
   - History trimming for token management

6. **`app/services/quiz_service.py`** – Structured LLM output
   - JSON-mode output parsing
   - In-memory question store for grading

7. **`app/routes/chat.py`** – Thin route pattern
   - How FastAPI routes map to HTTP methods
   - Request validation via Pydantic
   - Error handling patterns

8. **`app/main.py`** – How it all connects
   - Router registration
   - Static file serving
   - CORS middleware — what it does and why

9. **`static/app.js`** – Frontend rendering
   - `renderContent()` function: Markdown → HTML → KaTeX math
   - Why we use `innerHTML` for assistant messages but `textContent` for user messages (XSS safety)

After the tour, suggest 3 small improvements Owen could try on his own.
