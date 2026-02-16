/* ═══════════════════════════════════════════════════════════
   Owen's Learn Agent – Application Logic
   ═══════════════════════════════════════════════════════════ */

const API = '';
let sessionId = crypto.randomUUID().replace(/-/g, '');

/* ── Markdown + KaTeX renderer ────────────────────────── */
function renderContent(raw) {
  // Step 1: Parse markdown
  const html = marked.parse(raw, { breaks: true, gfm: true });

  // Step 2: Insert into a temp container so KaTeX auto-render works
  const tmp = document.createElement('div');
  tmp.innerHTML = html;

  // Step 3: Render LaTeX with KaTeX auto-render
  if (window.renderMathInElement) {
    renderMathInElement(tmp, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
    });
  }
  return tmp.innerHTML;
}

/* ── Tab navigation & drawer system ───────────────────── */
const drawerOverlay = document.getElementById('drawer-overlay');
const drawers = document.querySelectorAll('.drawer');

function closeDrawers() {
  drawers.forEach(d => d.classList.remove('open'));
  drawerOverlay.classList.remove('visible');
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.querySelector('.nav-item[data-tab="chat"]').classList.add('active');
}

document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;

    if (tab === 'chat') {
      closeDrawers();
      return;
    }

    const drawer = document.getElementById(tab);
    const isOpen = drawer.classList.contains('open');

    // Close all drawers first
    drawers.forEach(d => d.classList.remove('open'));

    if (!isOpen) {
      drawer.classList.add('open');
      drawerOverlay.classList.add('visible');
      document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (tab === 'scratchpad') setTimeout(resizeCanvas, 350);
      if (tab === 'progress') loadProgress();
    } else {
      closeDrawers();
    }
  });
});

// Close drawer on overlay click
drawerOverlay.addEventListener('click', closeDrawers);

// Close buttons inside drawers
document.querySelectorAll('.drawer-close').forEach(btn => {
  btn.addEventListener('click', closeDrawers);
});

/* ═════════════════════════════════════════════════════════
   CHAT
   ═════════════════════════════════════════════════════════ */
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const messagesEl = document.getElementById('messages');
const subjectInput = document.getElementById('subject');

// Auto-resize textarea
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 140) + 'px';
});

// Enter to send, Shift+Enter for newline
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event('submit'));
  }
});

// Suggestion chips send messages
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    userInput.value = chip.dataset.msg;
    chatForm.dispatchEvent(new Event('submit'));
  });
});

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;
  userInput.value = '';
  userInput.style.height = 'auto';

  // Hide welcome card
  const welcome = messagesEl.querySelector('.welcome-card');
  if (welcome) welcome.remove();

  appendMsg('user', text);
  const thinkingEl = showThinking();

  try {
    const res = await fetch(`${API}/api/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        subject: subjectInput.value || 'Math',
      }),
    });
    const data = await res.json();
    thinkingEl.remove();
    appendMsg('assistant', data.reply || data.detail || 'Error');
  } catch (err) {
    thinkingEl.remove();
    appendMsg('assistant', `⚠️ Error: ${err.message}`);
  }
});

document.getElementById('clear-chat').addEventListener('click', async () => {
  await fetch(`${API}/api/chat/${sessionId}`, { method: 'DELETE' });
  messagesEl.innerHTML = `
    <div class="welcome-card">
      <div class="welcome-icon">&#x1F44B;</div>
      <h3>Welcome!</h3>
      <p>I'm your math tutor. Try asking me something like:</p>
      <div class="suggestion-chips">
        <button class="chip" data-msg="Explain how to solve systems of equations">Systems of equations</button>
        <button class="chip" data-msg="What is the quadratic formula and how do I use it?">Quadratic formula</button>
        <button class="chip" data-msg="Help me understand fractions and how to add them">Adding fractions</button>
        <button class="chip" data-msg="Explain the Pythagorean theorem with examples">Pythagorean theorem</button>
      </div>
    </div>`;
  // Re-attach chip listeners
  messagesEl.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      userInput.value = chip.dataset.msg;
      chatForm.dispatchEvent(new Event('submit'));
    });
  });
  sessionId = crypto.randomUUID().replace(/-/g, '');
});

function appendMsg(role, text) {
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  if (role === 'assistant') {
    el.innerHTML = renderContent(text);
  } else {
    el.textContent = text;
  }
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

function showThinking() {
  const el = document.createElement('div');
  el.className = 'thinking';
  el.innerHTML = '<span></span><span></span><span></span>';
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

/* ═════════════════════════════════════════════════════════
   QUIZ
   ═════════════════════════════════════════════════════════ */
const quizContainer = document.getElementById('quiz-container');
const quizScoreboard = document.getElementById('quiz-scoreboard');
let currentQuiz = [];

document.getElementById('generate-quiz').addEventListener('click', async () => {
  const btn = document.getElementById('generate-quiz');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Generating...';
  quizContainer.innerHTML = '';
  quizContainer.classList.remove('hidden');
  quizScoreboard.classList.add('hidden');
  currentQuiz = [];

  const difficulty = document.querySelector('input[name="diff"]:checked')?.value || 'medium';

  try {
    const res = await fetch(`${API}/api/quiz/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: subjectInput.value || 'Math',
        topic: document.getElementById('quiz-topic').value || 'Mixed',
        num_questions: parseInt(document.getElementById('quiz-count').value) || 5,
        difficulty,
      }),
    });
    const data = await res.json();
    currentQuiz = data.questions || [];
    renderQuiz(currentQuiz);
  } catch (err) {
    quizContainer.innerHTML = `<div class="quiz-card"><p>⚠️ ${err.message}</p></div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Generate Quiz`;
  }
});

function renderQuiz(questions) {
  const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
  questions.forEach((q, i) => {
    const card = document.createElement('div');
    card.className = 'quiz-card';
    card.dataset.id = q.id;

    const qTextHtml = renderContent(q.question);
    const choicesHtml = q.choices.map((c, ci) => {
      const choiceContent = renderContent(c.replace(/^[A-F]\.\s*/, ''));
      return `<button class="choice-btn" data-index="${ci}">
        <span class="choice-letter">${letters[ci]}</span>
        <span class="choice-text">${choiceContent}</span>
      </button>`;
    }).join('');
    const explHtml = renderContent(q.explanation);

    card.innerHTML = `
      <div class="q-number">Question ${i + 1} of ${questions.length}</div>
      <div class="q-text">${qTextHtml}</div>
      <div class="choices">${choicesHtml}</div>
      <div class="explanation-box">${explHtml}</div>
    `;

    card.querySelectorAll('.choice-btn').forEach(btn => {
      btn.addEventListener('click', () => handleChoice(card, q, parseInt(btn.dataset.index)));
    });

    quizContainer.appendChild(card);
  });
}

async function handleChoice(card, question, selectedIndex) {
  if (card.dataset.answered) return;
  card.dataset.answered = 'true';

  const choices = card.querySelectorAll('.choice-btn');
  choices.forEach(c => c.classList.add('disabled'));
  choices[selectedIndex].classList.add('selected');

  try {
    const studentId = document.getElementById('student-id')?.value || 'default';
    const res = await fetch(`${API}/api/quiz/submit?student_id=${studentId}`, {
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
    card.querySelector('.explanation-box').classList.add('visible');

    // Check if all answered
    const answered = quizContainer.querySelectorAll('[data-answered]').length;
    if (answered === currentQuiz.length) showScoreboard();
  } catch (err) {
    console.error(err);
  }
}

function showScoreboard() {
  const correct = quizContainer.querySelectorAll('.choice-btn.selected.correct').length;
  const total = currentQuiz.length;
  const pct = Math.round((correct / total) * 100);

  let emoji = '🎉';
  if (pct < 40) emoji = '💪';
  else if (pct < 70) emoji = '👍';

  quizScoreboard.classList.remove('hidden');
  quizScoreboard.innerHTML = `
    <div>${emoji}</div>
    <div class="score-big">${pct}%</div>
    <div class="score-label">${correct} of ${total} correct</div>
    <div class="score-bar"><div class="score-bar-fill" style="width:${pct}%"></div></div>
  `;
}

/* ═════════════════════════════════════════════════════════
   SCRATCH PAD
   ═════════════════════════════════════════════════════════ */
const canvas = document.getElementById('scratch-canvas');
const ctx = canvas.getContext('2d');
let drawing = false;
let tool = 'pen';
let strokes = [];     // For undo
let currentStroke = [];

function resizeCanvas() {
  const wrap = canvas.parentElement;
  const rect = wrap.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';
  ctx.scale(dpr, dpr);
  redraw();
}

function redraw() {
  const dpr = window.devicePixelRatio || 1;
  ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr);
  strokes.forEach(stroke => drawStroke(stroke));
}

function drawStroke(stroke) {
  if (stroke.points.length < 2) return;
  ctx.beginPath();
  ctx.strokeStyle = stroke.color;
  ctx.lineWidth = stroke.size;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.globalCompositeOperation = stroke.eraser ? 'destination-out' : 'source-over';
  ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
  for (let i = 1; i < stroke.points.length; i++) {
    ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
  }
  ctx.stroke();
  ctx.globalCompositeOperation = 'source-over';
}

function getPos(e) {
  const rect = canvas.getBoundingClientRect();
  const t = e.touches ? e.touches[0] : e;
  return { x: t.clientX - rect.left, y: t.clientY - rect.top };
}

canvas.addEventListener('pointerdown', (e) => {
  drawing = true;
  const pos = getPos(e);
  currentStroke = {
    color: tool === 'eraser' ? '#fff' : document.getElementById('pen-color').value,
    size: parseInt(document.getElementById('pen-size').value),
    eraser: tool === 'eraser',
    points: [pos],
  };
  canvas.setPointerCapture(e.pointerId);
});

canvas.addEventListener('pointermove', (e) => {
  if (!drawing) return;
  const pos = getPos(e);
  currentStroke.points.push(pos);
  // Draw incrementally for performance
  const pts = currentStroke.points;
  if (pts.length >= 2) {
    ctx.beginPath();
    ctx.strokeStyle = currentStroke.color;
    ctx.lineWidth = currentStroke.size;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.globalCompositeOperation = currentStroke.eraser ? 'destination-out' : 'source-over';
    ctx.moveTo(pts[pts.length - 2].x, pts[pts.length - 2].y);
    ctx.lineTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
    ctx.stroke();
    ctx.globalCompositeOperation = 'source-over';
  }
});

canvas.addEventListener('pointerup', () => {
  if (!drawing) return;
  drawing = false;
  if (currentStroke.points && currentStroke.points.length > 1) {
    strokes.push(currentStroke);
  }
  currentStroke = [];
});

// Tool buttons
document.querySelectorAll('.tool-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const action = btn.dataset.tool;
    if (action === 'pen' || action === 'eraser') {
      tool = action;
      document.querySelectorAll('.tool-btn[data-tool="pen"], .tool-btn[data-tool="eraser"]')
        .forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    } else if (action === 'clear') {
      strokes = [];
      redraw();
    } else if (action === 'undo') {
      strokes.pop();
      redraw();
    }
  });
});

window.addEventListener('resize', () => {
  if (document.getElementById('scratchpad').classList.contains('active')) {
    resizeCanvas();
  }
});

// Initial canvas size (deferred until tab is shown)
setTimeout(() => {
  if (document.getElementById('scratchpad').classList.contains('active')) resizeCanvas();
}, 100);

/* ═════════════════════════════════════════════════════════
   PROGRESS
   ═════════════════════════════════════════════════════════ */
document.getElementById('load-progress').addEventListener('click', loadProgress);

async function loadProgress() {
  const studentId = document.getElementById('student-id')?.value || 'default';
  const container = document.getElementById('progress-content');
  container.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';

  try {
    const res = await fetch(`${API}/api/progress/${studentId}`);
    const data = await res.json();

    if (!data.topics || data.topics.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">&#x1F4CA;</div>
          <p>No progress yet — take a quiz to get started!</p>
        </div>`;
      return;
    }

    container.innerHTML = `<div class="progress-grid">
      ${data.topics.map(t => {
        const pct = parseInt(t.accuracy) || 0;
        let barColor = 'var(--success)';
        if (pct < 40) barColor = 'var(--danger)';
        else if (pct < 70) barColor = 'var(--warning)';
        return `<div class="progress-card">
          <div class="pc-topic">${t.topic}</div>
          <div class="pc-subject">${t.subject}</div>
          <div class="pc-stats">
            <span><strong>${t.correct}</strong>/${t.attempts} correct</span>
            <span><strong>${t.accuracy}</strong></span>
          </div>
          <div class="pc-bar"><div class="pc-bar-fill" style="width:${pct}%;background:${barColor}"></div></div>
          <span class="pc-difficulty ${t.difficulty}">${t.difficulty}</span>
        </div>`;
      }).join('')}
    </div>`;
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><p>⚠️ ${err.message}</p></div>`;
  }
}

/* ── Wait for KaTeX to load, then make renderMathInElement available ── */
document.addEventListener('DOMContentLoaded', () => {
  // KaTeX auto-render loads via defer, might not be ready yet
  const check = setInterval(() => {
    if (window.renderMathInElement) clearInterval(check);
  }, 100);
});
