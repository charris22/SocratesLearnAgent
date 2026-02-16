---
mode: agent
description: "Add a new API endpoint to the tutoring agent — walks through the full pattern"
---

# Add a New API Endpoint

Owen wants to add a new API endpoint to the tutoring agent. Walk him through the full pattern this project uses.

## Steps to follow (explain each one as you go):

1. **Define the Pydantic models** in `app/models.py` for the request and response
   - Explain what Pydantic does and why we use it (validation, serialization)
   - Show how `Field()` works with defaults and constraints

2. **Create the service function** in `app/services/`
   - If it calls Azure OpenAI, make it `async`
   - If it needs a prompt template, add it to `app/prompts.py`
   - Explain the service-layer pattern: why routes should be thin

3. **Create the route** in `app/routes/`
   - Use `APIRouter` with a prefix and tag
   - Keep it thin — just validate input, call the service, return the response
   - Add proper error handling with `HTTPException`

4. **Register the router** in `app/main.py`
   - Show the `app.include_router()` pattern

5. **Write a test** in `tests/`
   - For offline logic, test the service function directly
   - Explain why we avoid calling the real LLM in tests

6. **Update the frontend** in `static/` if the endpoint needs UI

After each step, explain **why** we did it that way and what alternatives exist.
