# Owen's Learn Agent — Task Backlog

Tasks organized by difficulty. Each one teaches a specific skill. Pick one, use the corresponding prompt file in Copilot agent mode, and build!

---

## 🟢 Easy (Good First Tasks)

### E1: Add a `/health` endpoint
**Skills:** Routes, FastAPI basics
**What:** Add `GET /health` that returns `{"status": "ok"}`. Simple, but it teaches the route → registration pattern.
**Prompt file:** `#add-endpoint`
**Files to change:** Create `app/routes/health.py`, update `app/main.py`

### E2: Add a "Clear Chat" button
**Skills:** Frontend DOM manipulation, API calls
**What:** Add a button in the chat UI that calls `DELETE /api/chat/{session_id}` and clears the messages.
**Prompt file:** `#add-frontend-feature`
**Files to change:** `static/index.html`, `static/app.js`

### E3: Show the current difficulty level in the UI
**Skills:** Reading API data, rendering
**What:** Call `GET /api/progress/{student_id}` and display the difficulty level in the Progress tab or chat header.
**Prompt file:** `#add-frontend-feature`
**Files to change:** `static/app.js`

### E4: Improve the tutor's math formatting
**Skills:** Prompt engineering
**What:** Modify `TUTOR_SYSTEM_PROMPT` so the tutor consistently uses LaTeX notation and structures responses better.
**Prompt file:** `#improve-prompts`
**Files to change:** `app/prompts.py`

### E5: Add tests for the quiz service grading
**Skills:** Testing, mocking
**What:** Write tests for `grade_answer()` in `quiz_service.py` — test correct answer, wrong answer, and missing question.
**Prompt file:** `#write-tests`
**Files to change:** Create `tests/test_quiz.py`

---

## 🟡 Medium (Building Skills)

### M1: Add a "Hint" button to the quiz
**Skills:** Frontend + API integration, LLM features
**What:** When a student is stuck on a quiz question, they can click "Hint" to get an AI-generated hint (without revealing the answer).
**Prompt file:** `#add-llm-feature`, `#add-endpoint`
**Files to change:** `app/prompts.py`, `app/services/quiz_service.py`, `app/routes/quiz.py`, `static/app.js`

### M2: Add subject-specific system prompts
**Skills:** Prompt engineering, service logic
**What:** Instead of one generic tutor prompt, use different prompts for Math, Science, Language Arts, etc.
**Prompt file:** `#improve-prompts`
**Files to change:** `app/prompts.py`, `app/services/chat_service.py`

### M3: Save chat history to a JSON file
**Skills:** File I/O, data persistence
**What:** When a chat session ends (or periodically), save the conversation to a JSON file so it survives server restarts. This is a stepping stone to a real database.
**Prompt file:** `#add-database`
**Files to change:** `app/services/chat_service.py`, possibly a new `app/storage.py`

### M4: Add an "Export Quiz" feature
**Skills:** Data formatting, frontend download
**What:** Let students export a completed quiz as a printable HTML page or JSON file. Teaches data transformation and browser download APIs.
**Prompt file:** `#add-frontend-feature`
**Files to change:** `static/app.js`, possibly `static/index.html`

### M5: Add a loading skeleton to the UI
**Skills:** CSS animations, UX design
**What:** Replace the simple "Thinking..." indicator with a proper skeleton loading animation while waiting for LLM responses.
**Prompt file:** `#add-frontend-feature`
**Files to change:** `static/style.css`, `static/app.js`

### M6: Add input validation and error toasts
**Skills:** Error handling, UX
**What:** Show user-friendly toast notifications when things go wrong (empty message, API error, etc.) instead of silent failures.
**Prompt file:** `#add-frontend-feature`
**Files to change:** `static/app.js`, `static/style.css`

---

## 🔴 Hard (Real Engineering Challenges)

### H1: Add SQLite persistence
**Skills:** Databases, async I/O, schema design
**What:** Replace all three in-memory stores with SQLite using `aiosqlite`. Data survives server restarts.
**Prompt file:** `#add-database`
**Files to change:** `pyproject.toml`, create `app/database.py`, update all three services

### H2: Add streaming responses
**Skills:** Server-Sent Events, async generators, frontend streaming
**What:** Instead of waiting for the full LLM response, stream tokens to the browser as they arrive. Makes the tutor feel much more responsive.
**Files to change:** `app/services/chat_service.py`, `app/routes/chat.py`, `static/app.js`
**Concepts:** SSE, `StreamingResponse`, `async for chunk in response`, `EventSource` in JS

### H3: Add user authentication
**Skills:** Auth, sessions, security
**What:** Add login/signup so each student has their own profile and progress. Could use simple session tokens or Azure AD.
**Files to change:** Create `app/auth.py`, update `app/main.py`, add login UI

### H4: Deploy to Azure Container Apps
**Skills:** Docker, Azure CLI, cloud deployment
**What:** Containerize the app and deploy it to Azure so Owen can share it with friends.
**Files to create:** `Dockerfile`, `.dockerignore`, deployment scripts
**Concepts:** Container images, environment variables in the cloud, health checks

### H5: Add a "Study Plan" feature
**Skills:** Multi-step LLM reasoning, complex prompts, data modeling
**What:** Using the student's progress data, have the LLM generate a personalized study plan with topics to review, practice problems, and a timeline.
**Files to change:** `app/prompts.py`, create `app/services/study_plan_service.py`, create `app/routes/study_plan.py`, update frontend

### H6: Add multi-modal support (image input)
**Skills:** Vision APIs, file upload, advanced LLM features
**What:** Let students take a photo of a math problem (or draw on the scratch pad) and have the tutor analyze it using GPT-4's vision capabilities.
**Files to change:** `app/services/chat_service.py`, `app/routes/chat.py`, `static/app.js`

---

## 🏆 Boss Level

### B1: Build a teacher dashboard
**Skills:** Full-stack feature, data visualization, new user role
**What:** Create a separate view where a teacher can see all students' progress, quiz scores, and common misconceptions. Requires rethinking the data model and adding role-based views.

### B2: Make it a real-time collaborative tutor
**Skills:** WebSockets, real-time state, advanced frontend
**What:** Multiple students in a "classroom" with the AI tutor, seeing each other's questions and the tutor's responses in real time.

---

## How to Pick a Task

1. **Start with 🟢 Easy** — These build confidence and teach the patterns
2. **Try them in order** — E1 → E2 → E3 teaches a natural progression
3. **Use the prompt files** — They'll guide you step-by-step
4. **Don't skip testing** — E5 early teaches you to verify your work
5. **When ready, jump to 🟡** — These combine multiple skills
6. **🔴 Hard tasks** are real engineering — take your time, break them into subtasks
