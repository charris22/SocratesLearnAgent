/* Owen's Learn Agent – Frontend logic */

const API = '';  // same origin
let sessionId = crypto.randomUUID().replace(/-/g, '');

// ── Tab navigation ──────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
});

// ── Chat ────────────────────────────────────────────────────
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const messagesEl = document.getElementById('messages');
const subjectInput = document.getElementById('subject');

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;
  userInput.value = '';

  appendMsg('user', text);
  const thinkingEl = appendMsg('assistant', '');
  thinkingEl.classList.add('spinner');

  try {
    const res = await fetch(`${API}/api/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        subject: subjectInput.value || null,
      }),
    });
    const data = await res.json();
    thinkingEl.classList.remove('spinner');
    thinkingEl.textContent = data.reply || data.detail || 'Error';
  } catch (err) {
    thinkingEl.classList.remove('spinner');
    thinkingEl.textContent = `Error: ${err.message}`;
  }
});

document.getElementById('clear-chat').addEventListener('click', async () => {
  await fetch(`${API}/api/chat/${sessionId}`, { method: 'DELETE' });
  messagesEl.innerHTML = '';
  sessionId = crypto.randomUUID().replace(/-/g, '');
});

function appendMsg(role, text) {
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  el.textContent = text;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

// ── Quiz ────────────────────────────────────────────────────
const quizContainer = document.getElementById('quiz-container');
const quizResults = document.getElementById('quiz-results');
let currentQuiz = [];

document.getElementById('generate-quiz').addEventListener('click', async () => {
  const btn = document.getElementById('generate-quiz');
  btn.disabled = true;
  btn.textContent = 'Generating...';
  quizContainer.innerHTML = '';
  quizContainer.classList.remove('hidden');
  quizResults.classList.add('hidden');
  currentQuiz = [];

  try {
    const res = await fetch(`${API}/api/quiz/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: document.getElementById('quiz-subject').value || 'General',
        topic: document.getElementById('quiz-topic').value || 'Mixed',
        num_questions: parseInt(document.getElementById('quiz-count').value) || 5,
        difficulty: document.getElementById('quiz-difficulty').value,
      }),
    });
    const data = await res.json();
    currentQuiz = data.questions || [];
    renderQuiz(currentQuiz);
  } catch (err) {
    quizContainer.innerHTML = `<p>Error: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Quiz';
  }
});

function renderQuiz(questions) {
  questions.forEach((q, i) => {
    const div = document.createElement('div');
    div.className = 'quiz-question';
    div.dataset.id = q.id;
    div.innerHTML = `
      <h3>Q${i + 1}: ${q.question}</h3>
      ${q.choices.map((c, ci) => `
        <label class="choice" data-index="${ci}">${c}</label>
      `).join('')}
      <div class="explanation">${q.explanation}</div>
    `;
    div.querySelectorAll('.choice').forEach(choice => {
      choice.addEventListener('click', () => handleChoiceClick(div, q, parseInt(choice.dataset.index)));
    });
    quizContainer.appendChild(div);
  });
}

async function handleChoiceClick(questionDiv, question, selectedIndex) {
  // Prevent re-answering
  if (questionDiv.dataset.answered) return;
  questionDiv.dataset.answered = 'true';

  const choices = questionDiv.querySelectorAll('.choice');
  choices[selectedIndex].classList.add('selected');

  try {
    const res = await fetch(`${API}/api/quiz/submit?student_id=${document.getElementById('student-id').value || 'default'}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        question_id: question.id,
        selected_index: selectedIndex,
      }),
    });
    const result = await res.json();

    choices[result.correct_index].classList.add('correct');
    if (!result.correct) choices[selectedIndex].classList.add('wrong');

    questionDiv.querySelector('.explanation').classList.add('visible');

    // Check if all questions answered
    const answered = quizContainer.querySelectorAll('[data-answered]').length;
    if (answered === currentQuiz.length) showQuizSummary();
  } catch (err) {
    console.error(err);
  }
}

function showQuizSummary() {
  const correct = quizContainer.querySelectorAll('.choice.selected.correct').length;
  quizResults.classList.remove('hidden');
  quizResults.innerHTML = `
    <h3>Quiz Complete!</h3>
    <p>Score: <strong>${correct} / ${currentQuiz.length}</strong> (${Math.round(correct / currentQuiz.length * 100)}%)</p>
  `;
}

// ── Progress ────────────────────────────────────────────────
document.getElementById('load-progress').addEventListener('click', loadProgress);

async function loadProgress() {
  const studentId = document.getElementById('student-id').value || 'default';
  const container = document.getElementById('progress-content');
  container.innerHTML = 'Loading...';

  try {
    const res = await fetch(`${API}/api/progress/${studentId}`);
    const data = await res.json();

    if (!data.topics || data.topics.length === 0) {
      container.innerHTML = '<p>No progress recorded yet. Take a quiz to get started!</p>';
      return;
    }

    container.innerHTML = `
      <p><strong>${data.name}</strong> (${data.student_id})</p>
      <table class="progress-table">
        <thead><tr>
          <th>Subject</th><th>Topic</th><th>Attempts</th><th>Accuracy</th><th>Difficulty</th>
        </tr></thead>
        <tbody>
          ${data.topics.map(t => `<tr>
            <td>${t.subject}</td><td>${t.topic}</td><td>${t.attempts}</td>
            <td>${t.accuracy}</td><td>${t.difficulty}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<p>Error: ${err.message}</p>`;
  }
}
