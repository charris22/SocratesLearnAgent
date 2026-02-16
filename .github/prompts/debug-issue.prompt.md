---
mode: agent
description: "Debug an issue — systematic debugging approach"
---

# Debug an Issue

Owen has found a bug or is seeing unexpected behavior. Walk him through systematic debugging.

## Debugging approach:

1. **Reproduce** — What exactly happens vs what should happen?
   - Check the browser console (F12 → Console) for JS errors
   - Check the terminal running uvicorn for Python errors
   - Check the Network tab (F12 → Network) for API call status codes

2. **Isolate** — Where in the stack is the problem?
   - **Frontend only?** (JS error, CSS issue, wrong DOM structure)
   - **API layer?** (wrong route, validation error, 4xx/5xx response)
   - **Service layer?** (business logic bug, wrong data transformation)
   - **LLM layer?** (bad prompt, unexpected response format, token limit)
   - **Config?** (wrong .env values, missing settings)

3. **Investigate** — Read the relevant code
   - Trace the data flow from user action → frontend → API → service → LLM → response
   - Add `print()` or `logger.info()` statements for visibility
   - Use the FastAPI docs at `http://localhost:8000/docs` to test API endpoints directly

4. **Fix** — Make the smallest change that fixes the issue
   - Explain why the fix works
   - Check for similar bugs elsewhere
   - Add a test if possible to prevent regression

5. **Verify** — Confirm the fix works
   - Re-test the original reproduction steps
   - Run `pytest` to make sure nothing else broke

## Common issues in this project:
- **404 from Azure OpenAI**: Wrong deployment name or endpoint format (see `azure_client.py`)
- **LaTeX not rendering**: Missing `renderContent()` call or wrong KaTeX delimiters
- **Quiz grading wrong**: Check `correct_index` in the LLM response matches the choices array
- **Session state lost**: Server restarted (in-memory stores are ephemeral)
