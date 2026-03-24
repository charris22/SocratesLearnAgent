/* ═══════════════════════════════════════════════════════════
   Socrates – Application Logic
   ═══════════════════════════════════════════════════════════ */

const API = '';
let sessionId = crypto.randomUUID().replace(/-/g, '');

/* ── Markdown + KaTeX renderer ────────────────────────── */

// Safety net: wrap bare LaTeX commands in $...$ so KaTeX can find them
function wrapBareLatex(text) {
  // Match common LaTeX commands not already inside $ or \( delimiters
  return text.replace(
    /(?<![\$\\(])\\(frac|sqrt|sum|prod|int|lim|infty|alpha|beta|gamma|delta|theta|pi|sigma|omega|times|div|pm|mp|cdot|leq|geq|neq|approx|equiv|binom|log|ln|sin|cos|tan|sec|csc|cot)\b([^$]*?)(?=[,.)\s]|$)/g,
    (match, cmd, rest, offset, string) => {
      // Don't wrap if already inside a $ delimiter
      const before = string.slice(0, offset);
      const dollars = (before.match(/\$/g) || []).length;
      if (dollars % 2 === 1) return match; // inside $...$
      return `$${match.trim()}$`;
    }
  );
}

function renderContent(raw) {
  // Step 0: Wrap any bare LaTeX commands in $ delimiters
  const wrapped = wrapBareLatex(raw);

  // Step 1: Parse markdown
  const html = marked.parse(wrapped, { breaks: true, gfm: true });

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
  drawers.forEach(d => {
    d.classList.remove('open');
    d.classList.remove('expanded');
  });
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
      if (tab === 'profile') loadProfile();
      if (tab === 'worksheets') loadSavedWorksheets();
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

// Expand / collapse buttons inside drawers
document.querySelectorAll('.drawer-expand').forEach(btn => {
  btn.addEventListener('click', () => {
    const drawer = btn.closest('.drawer');
    const isExpanded = drawer.classList.toggle('expanded');
    btn.title = isExpanded ? 'Collapse' : 'Expand';
    btn.innerHTML = isExpanded ? '&#x2750;' : '&#x26F6;';
  });
});

/* ── Sidebar collapse ─────────────────────────────────── */
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');

sidebarToggle.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
});

/* ── Dynamic subject title ────────────────────────────── */
const chatTitle = document.getElementById('chat-title');
const quizTitle = document.getElementById('quiz-title');

function updateTitles() {
  const subj = subjectInput.value || 'Math';
  chatTitle.textContent = `${subj} Tutor`;
  quizTitle.textContent = `${subj} Quiz`;
}

/* ═════════════════════════════════════════════════════════
   CHAT
   ═════════════════════════════════════════════════════════ */
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const messagesEl = document.getElementById('messages');
const subjectInput = document.getElementById('subject');

function markSubjectChange(subject) {
  const welcome = messagesEl.querySelector('.welcome-card');
  if (welcome) welcome.remove();
  appendMsg('system', `Subject changed to ${subject}`);
}

function setSubject(subject, markInChat = true) {
  if (!subject || subjectInput.value === subject) return;
  subjectInput.value = subject;
  updateTitles();
  if (markInChat) markSubjectChange(subject);
}

// Update titles and visibly mark subject changes in the chat log
subjectInput.addEventListener('change', () => {
  const subject = subjectInput.value || 'Math';
  updateTitles();
  markSubjectChange(subject);
});
updateTitles();

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

function submitPrompt(prompt, subject) {
  if (!prompt) return;

  if (subject) setSubject(subject, true);

  closeDrawers();
  userInput.value = prompt;
  userInput.focus();
  chatForm.dispatchEvent(new Event('submit'));
}

function bindPromptButtons(root = document) {
  root.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      submitPrompt(chip.dataset.msg);
    });
  });

  root.querySelectorAll('.section-action').forEach(button => {
    button.addEventListener('click', () => {
      submitPrompt(button.dataset.prompt, button.dataset.subject);
    });
  });
}

bindPromptButtons();

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
    const reply = data.reply || data.detail || 'Error';
    appendMsg('assistant', reply);
    if (autoSpeak) speakText(reply);
  } catch (err) {
    thinkingEl.remove();
    appendMsg('assistant', `⚠️ Error: ${err.message}`);
  }
});

document.getElementById('clear-chat').addEventListener('click', async () => {
  await fetch(`${API}/api/chat/${sessionId}`, { method: 'DELETE' });
  messagesEl.innerHTML = `
    <div class="welcome-card">
      <div class="welcome-icon">
        <svg width="48" height="48" viewBox="0 0 64 64" fill="none"><circle cx="32" cy="32" r="14" fill="var(--primary)"/><g stroke="var(--primary)" stroke-width="3" stroke-linecap="round"><line x1="32" y1="4" x2="32" y2="14"/><line x1="32" y1="50" x2="32" y2="60"/><line x1="4" y1="32" x2="14" y2="32"/><line x1="50" y1="32" x2="60" y2="32"/><line x1="12.2" y1="12.2" x2="19.4" y2="19.4"/><line x1="44.6" y1="44.6" x2="51.8" y2="51.8"/><line x1="51.8" y1="12.2" x2="44.6" y2="19.4"/><line x1="19.4" y1="44.6" x2="12.2" y2="51.8"/></g></svg>
      </div>
      <h3>Welcome to Socrates!</h3>
      <p>I'm your tutor. Try asking me something like:</p>
      <div class="suggestion-chips">
        <button class="chip" data-msg="Explain how to solve systems of equations">Systems of equations</button>
        <button class="chip" data-msg="What is the quadratic formula and how do I use it?">Quadratic formula</button>
        <button class="chip" data-msg="Help me understand fractions and how to add them">Adding fractions</button>
        <button class="chip" data-msg="Explain the Pythagorean theorem with examples">Pythagorean theorem</button>
      </div>
    </div>`;
  bindPromptButtons(messagesEl);
  sessionId = crypto.randomUUID().replace(/-/g, '');
});

function appendMsg(role, text) {
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  if (role === 'assistant') {
    el.innerHTML = renderContent(text);
    // Add speak button for assistant messages
    const speakBtn = document.createElement('button');
    speakBtn.className = 'msg-speak-btn';
    speakBtn.title = 'Read aloud';
    speakBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>';
    speakBtn.addEventListener('click', () => speakText(text, speakBtn));
    el.appendChild(speakBtn);
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
   VOICE INPUT / OUTPUT
   ═════════════════════════════════════════════════════════ */
const micBtn = document.getElementById('mic-btn');
const autoSpeakBtn = document.getElementById('auto-speak-btn');
let autoSpeak = false;

// ── Text-to-Speech ───────────────────────────────────────
function stripMarkdownForSpeech(text) {
  return text
    .replace(/\$\$[\s\S]*?\$\$/g, ' (math expression) ')   // display math
    .replace(/\$[^$]+\$/g, ' (math expression) ')           // inline math
    .replace(/\\[\[\(][\s\S]*?\\[\]\)]/g, ' (math expression) ')
    .replace(/```[\s\S]*?```/g, '')                          // code blocks
    .replace(/`[^`]+`/g, '')                                 // inline code
    .replace(/[#*_~>\[\]|]/g, '')                            // markdown chars
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')                    // images
    .replace(/\[[^\]]*\]\([^)]*\)/g, (m) => m.replace(/\[|\]|\([^)]*\)/g, '')) // links → text
    .replace(/\n{2,}/g, '. ')
    .replace(/\n/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

let currentUtterance = null;

function speakText(text, btn) {
  if (!('speechSynthesis' in window)) return;

  // If already speaking this text, stop it
  if (speechSynthesis.speaking) {
    speechSynthesis.cancel();
    if (btn) btn.classList.remove('speaking');
    currentUtterance = null;
    return;
  }

  const clean = stripMarkdownForSpeech(text);
  if (!clean) return;

  const utter = new SpeechSynthesisUtterance(clean);
  utter.rate = 1.0;
  utter.pitch = 1.0;

  // Pick a natural-sounding voice if available
  const voices = speechSynthesis.getVoices();
  const preferred = voices.find(v =>
    /natural|neural|enhanced/i.test(v.name) && v.lang.startsWith('en')
  ) || voices.find(v => v.lang.startsWith('en') && v.localService);
  if (preferred) utter.voice = preferred;

  if (btn) {
    btn.classList.add('speaking');
    utter.onend = () => btn.classList.remove('speaking');
    utter.onerror = () => btn.classList.remove('speaking');
  }

  currentUtterance = utter;
  speechSynthesis.speak(utter);
}

function stopSpeaking() {
  if (speechSynthesis.speaking) speechSynthesis.cancel();
  currentUtterance = null;
}

// Auto-speak toggle
autoSpeakBtn.addEventListener('click', () => {
  autoSpeak = !autoSpeak;
  autoSpeakBtn.classList.toggle('active', autoSpeak);
  autoSpeakBtn.title = autoSpeak ? 'Auto-speak ON (click to mute)' : 'Toggle auto-speak responses';
  if (!autoSpeak) stopSpeaking();
});

// Ensure voices are loaded (some browsers load async)
if ('speechSynthesis' in window) {
  speechSynthesis.getVoices();
  speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
}

// ── Speech-to-Text ───────────────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add('listening');
    micBtn.title = 'Listening… click to stop';
  };

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    userInput.value = transcript;
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 140) + 'px';

    // When final, stop listening and let user review before sending
    if (event.results[event.results.length - 1].isFinal) {
      stopListening();
      userInput.focus();
    }
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    stopListening();
  };

  recognition.onend = () => {
    stopListening();
  };
} else {
  // Browser doesn't support speech recognition
  micBtn.style.display = 'none';
}

function startListening() {
  if (!recognition || isListening) return;
  stopSpeaking(); // stop any TTS so mic doesn't pick it up
  userInput.value = '';
  recognition.start();
}

function stopListening() {
  isListening = false;
  micBtn.classList.remove('listening');
  micBtn.title = 'Voice input (click to record)';
  try { recognition?.stop(); } catch { /* already stopped */ }
}

micBtn.addEventListener('click', () => {
  if (isListening) {
    stopListening();
  } else {
    startListening();
  }
});

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

/* ═════════════════════════════════════════════════════════
   WORKSHEETS
   ═════════════════════════════════════════════════════════ */
let currentWorksheet = null;

document.getElementById('generate-ws').addEventListener('click', async () => {
  const btn = document.getElementById('generate-ws');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Generating...';

  const studentId = document.getElementById('student-id')?.value || 'default';
  const difficulty = document.querySelector('input[name="ws-diff"]:checked')?.value || 'medium';

  try {
    const res = await fetch(`${API}/api/worksheet/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: subjectInput.value || 'Math',
        topic: document.getElementById('ws-topic').value || 'Mixed',
        num_items: parseInt(document.getElementById('ws-count').value) || 10,
        difficulty,
        student_id: studentId,
        include_answer_key: true,
      }),
    });
    currentWorksheet = await res.json();
    renderWorksheetPreview(currentWorksheet);
    loadSavedWorksheets();
  } catch (err) {
    document.getElementById('ws-preview').innerHTML = `<p>⚠️ ${err.message}</p>`;
    document.getElementById('ws-preview').classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Generate Worksheet`;
  }
});

function renderWorksheetPreview(ws) {
  document.getElementById('ws-preview-title').textContent = ws.title;
  const itemsEl = document.getElementById('ws-items');
  itemsEl.innerHTML = ws.items.map(item => `
    <div class="ws-item-card">
      <div class="ws-item-num">${item.number}.</div>
      <div class="ws-item-question">${renderContent(item.question)}</div>
      <div class="ws-item-meta">${item.concept} · ${item.difficulty} · ${item.points} pt${item.points !== 1 ? 's' : ''}</div>
    </div>
  `).join('');

  document.getElementById('ws-preview').classList.remove('hidden');

  // Build answer form
  const answerFields = document.getElementById('ws-answer-fields');
  answerFields.innerHTML = ws.items.map(item => `
    <div class="ws-answer-row">
      <label><strong>${item.number}.</strong></label>
      <input type="text" class="ws-answer-input" data-number="${item.number}" placeholder="Your answer..." />
    </div>
  `).join('');
  document.getElementById('ws-score-section').classList.remove('hidden');
  document.getElementById('ws-results').classList.add('hidden');
}

// Print worksheet
document.getElementById('ws-print').addEventListener('click', () => {
  if (!currentWorksheet) return;
  window.open(`${API}/api/worksheet/${currentWorksheet.id}/print`, '_blank');
});

document.getElementById('ws-print-key').addEventListener('click', () => {
  if (!currentWorksheet) return;
  window.open(`${API}/api/worksheet/${currentWorksheet.id}/print?answers=true`, '_blank');
});

// Score worksheet
document.getElementById('ws-submit-score').addEventListener('click', async () => {
  if (!currentWorksheet) return;
  const btn = document.getElementById('ws-submit-score');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Scoring...';

  const inputs = document.querySelectorAll('.ws-answer-input');
  const answers = Array.from(inputs).map(input => ({
    number: parseInt(input.dataset.number),
    student_answer: input.value.trim(),
  }));

  const studentId = document.getElementById('student-id')?.value || 'default';

  try {
    const res = await fetch(`${API}/api/worksheet/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        worksheet_id: currentWorksheet.id,
        student_id: studentId,
        answers,
      }),
    });
    const result = await res.json();
    renderWorksheetResults(result);
  } catch (err) {
    document.getElementById('ws-results').innerHTML = `<p>⚠️ ${err.message}</p>`;
    document.getElementById('ws-results').classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Score My Worksheet';
  }
});

function renderWorksheetResults(result) {
  const resultsEl = document.getElementById('ws-results');
  const pct = Math.round(result.percentage);
  let emoji = '🎉';
  if (pct < 40) emoji = '💪';
  else if (pct < 70) emoji = '👍';

  resultsEl.innerHTML = `
    <div class="ws-score-summary">
      <div>${emoji}</div>
      <div class="score-big">${pct}%</div>
      <div class="score-label">${result.earned} of ${result.total} points</div>
      <div class="score-bar"><div class="score-bar-fill" style="width:${pct}%"></div></div>
    </div>
    <div class="ws-scored-items">
      ${result.items.map(item => `
        <div class="ws-scored-item ${item.correct ? 'correct' : 'wrong'}">
          <div class="ws-scored-num">${item.number}.</div>
          <div class="ws-scored-body">
            <div>Your answer: <strong>${item.student_answer || '(blank)'}</strong></div>
            ${!item.correct ? `<div>Correct answer: <strong>${renderContent(item.correct_answer)}</strong></div>` : ''}
            <div class="ws-scored-feedback">${item.feedback}</div>
          </div>
          <div class="ws-scored-badge">${item.correct ? '✓' : '✗'}</div>
        </div>
      `).join('')}
    </div>
    ${result.recommendations.length > 0 ? `
      <div class="ws-recs">
        <h4>Recommendations</h4>
        <ul>${result.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>
      </div>
    ` : ''}
  `;
  resultsEl.classList.remove('hidden');
}

// ── Saved worksheets ───────────────────────────────────────
async function loadSavedWorksheets() {
  const listEl = document.getElementById('ws-saved-list');
  const studentId = document.getElementById('student-id')?.value || 'default';
  try {
    const res = await fetch(`${API}/api/worksheet/list?student_id=${encodeURIComponent(studentId)}`);
    const items = await res.json();
    if (!items.length) {
      listEl.innerHTML = '<p class="text-muted">No saved worksheets yet.</p>';
      return;
    }
    listEl.innerHTML = items.map(ws => `
      <div class="ws-saved-item" data-ws-id="${ws.id}">
        <div class="ws-saved-info">
          <div class="ws-saved-title">${ws.title}</div>
          <div class="ws-saved-meta">${ws.created_at || ''}</div>
        </div>
        <span class="ws-saved-badge ${ws.difficulty}">${ws.difficulty}</span>
      </div>
    `).join('');
    listEl.querySelectorAll('.ws-saved-item').forEach(el => {
      el.addEventListener('click', () => resumeWorksheet(el.dataset.wsId));
    });
  } catch {
    listEl.innerHTML = '<p class="text-muted">Could not load worksheets.</p>';
  }
}

async function resumeWorksheet(id) {
  try {
    const res = await fetch(`${API}/api/worksheet/${id}`);
    if (!res.ok) throw new Error('Not found');
    currentWorksheet = await res.json();
    renderWorksheetPreview(currentWorksheet);
    // Scroll the preview into view
    document.getElementById('ws-preview').scrollIntoView({ behavior: 'smooth' });
  } catch {
    alert('Could not load that worksheet.');
  }
}

/* ═════════════════════════════════════════════════════════
   PROFILE
   ═════════════════════════════════════════════════════════ */

// Load profile when drawer opens
async function loadProfile() {
  const studentId = document.getElementById('student-id')?.value || 'default';
  try {
    const res = await fetch(`${API}/api/progress/${studentId}/profile`);
    const data = await res.json();
    document.getElementById('profile-name').value = data.name || '';
    document.getElementById('profile-grade').value = data.grade || '';
    document.getElementById('profile-interests').value = (data.interests || []).join(', ');
    document.getElementById('profile-strengths').value = (data.strengths || []).join(', ');
    const paceRadio = document.querySelector(`input[name="pacing"][value="${data.pacing || 'standard'}"]`);
    if (paceRadio) paceRadio.checked = true;
  } catch (err) {
    console.error('Failed to load profile:', err);
  }

  // Load mastery data
  try {
    const res = await fetch(`${API}/api/progress/${studentId}`);
    const data = await res.json();
    const grid = document.getElementById('mastery-grid');
    if (data.mastery && data.mastery.length > 0) {
      grid.innerHTML = data.mastery.map(m => {
        const pct = Math.round(m.mastery_score * 100);
        let barColor = 'var(--success)';
        if (pct < 40) barColor = 'var(--danger)';
        else if (pct < 70) barColor = 'var(--warning)';
        return `<div class="progress-card">
          <div class="pc-topic">${m.concept}</div>
          <div class="pc-subject">${m.subject}</div>
          <div class="pc-stats">
            <span>Mastery: <strong>${pct}%</strong></span>
            <span>Evidence: <strong>${m.evidence_count}</strong></span>
            <span>Streak: <strong>${m.streak}</strong></span>
          </div>
          <div class="pc-bar"><div class="pc-bar-fill" style="width:${pct}%;background:${barColor}"></div></div>
        </div>`;
      }).join('');
    } else {
      grid.innerHTML = '<p class="empty-hint">No mastery data yet. Take quizzes or complete worksheets to build your profile.</p>';
    }
  } catch (err) {
    console.error('Failed to load mastery:', err);
  }
}

document.getElementById('profile-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const studentId = document.getElementById('student-id')?.value || 'default';
  const body = {
    name: document.getElementById('profile-name').value.trim() || null,
    grade: document.getElementById('profile-grade').value.trim() || null,
    interests: document.getElementById('profile-interests').value.split(',').map(s => s.trim()).filter(Boolean),
    strengths: document.getElementById('profile-strengths').value.split(',').map(s => s.trim()).filter(Boolean),
    pacing: document.querySelector('input[name="pacing"]:checked')?.value || 'standard',
  };

  try {
    await fetch(`${API}/api/progress/${studentId}/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    // Brief visual confirmation
    const btn = document.querySelector('#profile-form button[type="submit"]');
    const orig = btn.textContent;
    btn.textContent = '✓ Saved!';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  } catch (err) {
    console.error('Failed to save profile:', err);
  }
});

document.getElementById('load-recs').addEventListener('click', async () => {
  const btn = document.getElementById('load-recs');
  btn.disabled = true;
  btn.textContent = 'Loading...';
  const studentId = document.getElementById('student-id')?.value || 'default';
  const list = document.getElementById('recs-list');

  try {
    const res = await fetch(`${API}/api/progress/${studentId}/recommendations`);
    const data = await res.json();
    const recs = data.recommendations || [];
    if (recs.length === 0) {
      list.innerHTML = '<p class="empty-hint">Complete more activities to unlock personalized recommendations.</p>';
    } else {
      list.innerHTML = recs.map(r => `
        <div class="rec-card">
          <div class="rec-concept">${r.concept}</div>
          <div class="rec-subject">${r.subject} · ${r.suggested_difficulty} · ${r.suggested_activity}</div>
          <div class="rec-reason">${r.reason}</div>
        </div>
      `).join('');
    }
  } catch (err) {
    list.innerHTML = `<p>⚠️ ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Get Recommendations';
  }
});

/* ── Difficulty pill toggle ─────────────────────────────────────────────── */
document.querySelectorAll('.difficulty-pills').forEach(group => {
  // Mark the default-checked pill on load
  const checked = group.querySelector('input[type="radio"]:checked');
  if (checked) {
    const lbl = group.querySelector(`label[for="${checked.id}"]`);
    if (lbl) lbl.classList.add('selected');
  }
  // On any change, move the .selected class
  group.addEventListener('change', (e) => {
    group.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
    const lbl = group.querySelector(`label[for="${e.target.id}"]`);
    if (lbl) lbl.classList.add('selected');
  });
});

/* ── Wait for KaTeX to load, then make renderMathInElement available ── */
document.addEventListener('DOMContentLoaded', () => {
  // KaTeX auto-render loads via defer, might not be ready yet
  const check = setInterval(() => {
    if (window.renderMathInElement) clearInterval(check);
  }, 100);
});
