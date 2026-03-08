const STORAGE_KEY = 'pmnotes_state_v1';

const prdSections = [
  {
    id: 'exec_summary',
    title: 'Executive Summary',
    example: 'This PRD introduces Smart Prioritizer, a feature that reduces planning overhead for PMs by 35% and aligns roadmap decisions with business goals.',
    suggestions: [
      'This initiative matters now because {trigger event} is creating a measurable risk/opportunity.',
      'If we deliver this by {date}, we expect {business impact}.',
      'This proposal is intentionally focused on {scope} and excludes {out of scope}.'
    ]
  },
  {
    id: 'business_need',
    title: 'Business State & Need',
    example: 'Revenue growth slowed from 28% to 11% YoY, while feature adoption plateaued in enterprise accounts due to implementation complexity.',
    suggestions: [
      'Current state: {metric} moved from {A} to {B} in {period}.',
      'Root cause hypothesis: {cause}, validated by {signal}.',
      'If unchanged, the expected downside is {risk}.'
    ]
  },
  {
    id: 'goal',
    title: 'Goal',
    example: 'Increase enterprise activation rate from 42% to 60% within two quarters while reducing onboarding cycle time by 20%.',
    suggestions: [
      'Primary goal: Improve {north-star metric} from {baseline} to {target}.',
      'Secondary goal: Reduce {friction metric} by {target percentage}.',
      'Success criteria will be measured weekly using {dashboard/source}.'
    ]
  },
  {
    id: 'market_insight',
    title: 'Market Insight',
    example: 'Competitor analysis shows buyers now prioritize integration depth over standalone feature breadth, especially in regulated industries.',
    suggestions: [
      'Customer segment {segment} increasingly values {capability}.',
      'Competitors {names} are positioning around {theme}.',
      'Our differentiation can come from {defensible advantage}.'
    ]
  },
  {
    id: 'problem_statement',
    title: 'Problem Statement',
    example: 'PMs spend excessive time translating fragmented inputs into coherent PRDs, causing delays and inconsistent quality across teams.',
    suggestions: [
      '{persona} cannot {job-to-be-done} because {core friction}.',
      'This leads to {quantified consequence} for {business/user}.',
      'The most painful moment occurs when {critical workflow step}.'
    ]
  },
  {
    id: 'evidence',
    title: 'Evidence',
    example: 'In 27 PM interviews and 312 usage logs, 68% reported losing over 2 hours per PRD to restructuring and rewriting sections.',
    suggestions: [
      'Evidence source: {research type}, sample size {n}.',
      'Observed pattern: {insight} appears in {x}% of cases.',
      'Confidence level is {high/medium/low} because {reason}.'
    ]
  },
  {
    id: 'insights',
    title: 'Insights',
    example: 'Teams that start with structured prompts generate clearer trade-offs earlier, reducing review cycles by one full iteration on average.',
    suggestions: [
      'Key insight: When {condition}, users prefer {behavior}.',
      'Counter-intuitive finding: {unexpected truth}.',
      'Implication: We should prioritize {capability} before {alternative}.'
    ]
  },
  {
    id: 'strategic_themes',
    title: 'Strategic Themes',
    example: 'Theme 1: Quality of thinking, Theme 2: Cross-functional alignment, Theme 3: Speed without sacrificing rigor.',
    suggestions: [
      'Theme {#}: {theme name} supports objective {objective}.',
      'This theme guides decisions on {product area}.',
      'Trade-off principle: Favor {choice A} over {choice B} when {condition}.'
    ]
  },
  {
    id: 'execution_plan',
    title: 'Execution Plan (Functional, Non-functional, Platform)',
    example: 'Functional: section editor + sentence templates; Non-functional: <2s response, 99.9% uptime; Platform: model abstraction layer with user-provided API key support.',
    suggestions: [
      'Functional requirement: The system must {behavior} for {persona}.',
      'Non-functional requirement: {quality attribute} must meet {target}.',
      'Platform requirement: Integrate with {service} to enable {outcome}.'
    ]
  }
];

const defaultState = {
  todos: [],
  kanban: [],
  model: 'GPT-4.1',
  selectedSections: prdSections.reduce((acc, section) => ({ ...acc, [section.id]: false }), {}),
  sectionContent: prdSections.reduce((acc, section) => ({ ...acc, [section.id]: '' }), {})
};

let state = loadState();

function loadState() {
  try {
    return { ...defaultState, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') };
  } catch {
    return { ...defaultState };
  }
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach((panel) => panel.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    });
  });
}

function renderTodos() {
  const list = document.getElementById('todoList');
  list.innerHTML = '';

  state.todos.forEach((todo, index) => {
    const li = document.createElement('li');
    li.className = 'todo-item';
    li.innerHTML = `<input type="checkbox" ${todo.done ? 'checked' : ''}/><span>${todo.text}</span><button>Delete</button>`;

    const checkbox = li.querySelector('input');
    checkbox.addEventListener('change', () => {
      state.todos[index].done = checkbox.checked;
      persist();
      renderTodos();
      renderCoverageGraph();
    });

    li.querySelector('button').addEventListener('click', () => {
      state.todos.splice(index, 1);
      persist();
      renderTodos();
      renderCoverageGraph();
    });

    list.appendChild(li);
  });
}

function renderKanban() {
  const columns = {
    todo: document.getElementById('todoCol'),
    doing: document.getElementById('doingCol'),
    done: document.getElementById('doneCol')
  };

  Object.values(columns).forEach((node) => {
    node.innerHTML = '';
  });

  state.kanban.forEach((item, index) => {
    const card = document.createElement('div');
    card.className = 'kanban-card';
    card.innerHTML = `<strong>${item.title}</strong><div class="row"><select><option value="todo">To Do</option><option value="doing">Doing</option><option value="done">Done</option></select><button>Delete</button></div>`;

    const select = card.querySelector('select');
    select.value = item.status;
    select.addEventListener('change', () => {
      state.kanban[index].status = select.value;
      persist();
      renderKanban();
      renderCoverageGraph();
    });

    card.querySelector('button').addEventListener('click', () => {
      state.kanban.splice(index, 1);
      persist();
      renderKanban();
      renderCoverageGraph();
    });

    columns[item.status].appendChild(card);
  });
}

function bestSuggestion(sectionId, text) {
  const section = prdSections.find((s) => s.id === sectionId);
  if (!section) return '';

  const sentences = text.split(/[.!?]\s/).filter(Boolean);
  const index = Math.min(sentences.length, section.suggestions.length - 1);
  return section.suggestions[index];
}

function renderPrdSections() {
  const toggles = document.getElementById('sectionToggles');
  const container = document.getElementById('sectionsContainer');
  toggles.innerHTML = '';
  container.innerHTML = '';

  prdSections.forEach((section) => {
    const label = document.createElement('label');
    label.innerHTML = `<input type="checkbox" ${state.selectedSections[section.id] ? 'checked' : ''}/> ${section.title}`;
    label.querySelector('input').addEventListener('change', (event) => {
      state.selectedSections[section.id] = event.target.checked;
      persist();
      renderPrdSections();
      renderCoverageGraph();
    });
    toggles.appendChild(label);

    if (!state.selectedSections[section.id]) return;

    const node = document.getElementById('sectionTemplate').content.cloneNode(true);
    node.querySelector('.section-title').textContent = section.title;
    node.querySelector('.example-text').textContent = section.example;

    const textarea = node.querySelector('.section-input');
    const suggestionText = node.querySelector('.suggestion-text');
    textarea.value = state.sectionContent[section.id] || '';
    suggestionText.textContent = bestSuggestion(section.id, textarea.value);

    textarea.addEventListener('input', () => {
      state.sectionContent[section.id] = textarea.value;
      suggestionText.textContent = bestSuggestion(section.id, textarea.value);
      persist();
      renderCoverageGraph();
    });

    node.querySelector('.insertSuggestionBtn').addEventListener('click', () => {
      const suggestion = suggestionText.textContent;
      const spacer = textarea.value.trim().endsWith('.') || textarea.value.length === 0 ? '' : '. ';
      textarea.value = `${textarea.value}${spacer}${suggestion}`.trim();
      state.sectionContent[section.id] = textarea.value;
      suggestionText.textContent = bestSuggestion(section.id, textarea.value);
      persist();
      renderCoverageGraph();
    });

    container.appendChild(node);
  });
}

function renderCoverageGraph() {
  const graph = document.getElementById('coverageGraph');
  graph.innerHTML = '';

  const sectionScores = prdSections
    .filter((section) => state.selectedSections[section.id])
    .map((section) => {
      const words = (state.sectionContent[section.id] || '').trim().split(/\s+/).filter(Boolean).length;
      const score = Math.min(100, Math.round((words / 120) * 100));
      return { label: section.title, score };
    });

  const dailyScore = {
    label: 'Daily execution coverage',
    score: Math.min(100, Math.round(((state.todos.length + state.kanban.length) / 10) * 100))
  };

  [...sectionScores, dailyScore].forEach((item) => {
    const row = document.createElement('div');
    row.className = 'graph-row';
    row.innerHTML = `<span>${item.label}</span><div class="bar-track"><div class="bar-fill" style="width:${item.score}%"></div></div><strong>${item.score}%</strong>`;
    graph.appendChild(row);
  });
}

function downloadFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function gatherPrdText() {
  const lines = [`PMNotes PRD`, `Model: ${state.model}`, ''];
  prdSections.forEach((section) => {
    if (state.selectedSections[section.id]) {
      lines.push(section.title);
      lines.push(state.sectionContent[section.id] || '[Not filled]');
      lines.push('');
    }
  });
  return lines.join('\n');
}

function initEvents() {
  document.getElementById('addTodoBtn').addEventListener('click', () => {
    const input = document.getElementById('todoInput');
    const text = input.value.trim();
    if (!text) return;
    state.todos.push({ text, done: false });
    input.value = '';
    persist();
    renderTodos();
    renderCoverageGraph();
  });

  document.getElementById('addKanbanBtn').addEventListener('click', () => {
    const input = document.getElementById('kanbanTaskInput');
    const status = document.getElementById('kanbanStatus').value;
    const title = input.value.trim();
    if (!title) return;
    state.kanban.push({ title, status });
    input.value = '';
    persist();
    renderKanban();
    renderCoverageGraph();
  });

  document.getElementById('modelSelector').value = state.model;
  document.getElementById('modelSelector').addEventListener('change', (event) => {
    state.model = event.target.value;
    persist();
  });

  document.getElementById('saveDraftBtn').addEventListener('click', () => {
    persist();
    alert('Draft saved locally.');
  });

  document.getElementById('exportDocBtn').addEventListener('click', () => {
    const html = `<html><body><pre>${gatherPrdText()}</pre></body></html>`;
    downloadFile('PMNotes-PRD.doc', html, 'application/msword');
  });

  document.getElementById('exportPdfBtn').addEventListener('click', () => {
    window.print();
  });
}

setupTabs();
initEvents();
renderTodos();
renderKanban();
renderPrdSections();
renderCoverageGraph();
