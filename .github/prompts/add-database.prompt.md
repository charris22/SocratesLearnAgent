---
mode: agent
description: "Add database persistence — swap in-memory stores for a real DB"
---

# Add Database Persistence

Owen wants to replace the in-memory dictionaries with a real database so data survives server restarts.

## Current state

The app uses three in-memory stores (Python dicts):
- `chat_service._sessions` — chat conversation history
- `quiz_service._questions` — generated quiz questions
- `progress_service._students` — student profiles and scores

These are intentionally designed to be swapped out. Each service accesses them through simple dict operations.

## Options (discuss tradeoffs with Owen):

### Option A: SQLite + aiosqlite (simplest)
- **Pros:** No external service, file-based, zero config, great for learning
- **Cons:** Single-file, doesn't scale to multiple servers
- **Good for:** Local development, learning SQL

### Option B: Azure Cosmos DB (production-ready)
- **Pros:** Serverless, global, pairs with Azure AI Foundry
- **Cons:** Requires Azure subscription, more complex setup
- **Good for:** Production deployment, learning cloud databases

### Option C: Azure Table Storage (lightweight)
- **Pros:** Simple key-value, cheap, easy Azure integration
- **Cons:** Limited query capabilities
- **Good for:** Simple persistence without full database complexity

## Steps (using SQLite as example):

1. **Add `aiosqlite`** to `pyproject.toml` dependencies
2. **Create `app/database.py`** with table schemas and connection management
3. **Update each service** to use SQL instead of dict operations:
   - Replace `_sessions[key] = value` → `INSERT`/`UPDATE` statements
   - Replace `_sessions.get(key)` → `SELECT` statements
   - Keep the same function signatures so routes don't change
4. **Add database initialization** in `app/main.py` using FastAPI lifespan events
5. **Update tests** to use a test database (in-memory SQLite)
6. **Migrate existing tests** to verify they still pass

## Teaching moments:
- What is an ORM? Do we need one? (raw SQL vs SQLAlchemy vs Tortoise)
- Async database access with `aiosqlite`
- Database migrations — why and how
- The repository pattern — abstracting storage behind an interface
- Connection pooling and lifecycle management
