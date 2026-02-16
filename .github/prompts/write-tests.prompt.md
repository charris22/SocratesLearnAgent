---
mode: agent
description: "Write tests for the tutoring agent — testing patterns and best practices"
---

# Write Tests

Owen wants to add tests. Guide him through the testing patterns used in this project.

## Context

- Tests live in `tests/`
- We use `pytest` with `pytest-asyncio` for async test support
- Config in `pyproject.toml`: `asyncio_mode = "auto"`, `testpaths = ["tests"]`
- Run with: `pytest -v`

## Testing layers (explain the tradeoffs of each):

### 1. Unit tests (no LLM, no network)
These test pure logic — models, data transformations, grading.

```python
# Example: tests/test_models.py
from app.models import TopicScore

def test_accuracy():
    score = TopicScore(subject="Math", topic="Fractions", attempts=10, correct=7)
    assert score.accuracy == 0.7
```

**When to write these:** For any logic that doesn't call Azure OpenAI.

### 2. Service tests (mock the LLM)
These test service logic with a fake LLM response.

```python
# Example pattern:
from unittest.mock import AsyncMock, patch

@patch("app.services.chat_service.get_openai_client")
async def test_chat_returns_response(mock_client):
    mock_client.return_value.chat.completions.create = AsyncMock(
        return_value=MockResponse("Hello!")
    )
    result = await chat(ChatRequest(message="hi"))
    assert result.reply == "Hello!"
```

**Explain:** What is mocking? Why mock the LLM? (cost, speed, determinism)

### 3. API tests (FastAPI TestClient)
These test the HTTP layer.

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
```

## Steps:

1. Identify what to test — ask Owen what behavior they want to verify
2. Choose the right testing layer
3. Write the test, explaining each assertion
4. Run `pytest -v` and interpret the output
5. Discuss code coverage and what's worth testing vs over-testing
