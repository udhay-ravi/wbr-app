function renderQuestions(questions) {
  const questionnaire = document.getElementById('questionnaire');
  questionnaire.innerHTML = '<h2>Clarifying Questions</h2>';

  questions
    .filter((question) => question.id !== 'app_idea')
    .forEach((question) => {
      const wrapper = document.createElement('div');
      wrapper.className = 'question';

      const label = document.createElement('label');
      label.setAttribute('for', question.id);
      label.innerText = question.label;

      const select = document.createElement('select');
      select.id = question.id;

      question.options.forEach((option) => {
        const el = document.createElement('option');
        el.value = option;
        el.innerText = option;
        select.appendChild(el);
      });

      wrapper.appendChild(label);
      wrapper.appendChild(select);
      questionnaire.appendChild(wrapper);
    });

  questionnaire.classList.remove('hidden');
  document.getElementById('generateWrap').classList.remove('hidden');
}

async function askClarifyingQuestions() {
  const appIdea = document.getElementById('appIdea').value.trim();
  if (!appIdea) {
    alert('Please provide an app idea first.');
    return;
  }

  const response = await fetch('/api/system-design/questions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_idea: appIdea }),
  });

  const payload = await response.json();
  renderQuestions(payload.questions || []);
}

function collectAnswers() {
  const answers = {};
  document.querySelectorAll('.question select').forEach((select) => {
    answers[select.id] = select.value;
  });
  return answers;
}

function addListSection(card, title, items) {
  const sectionTitle = document.createElement('h3');
  sectionTitle.innerText = title;
  card.appendChild(sectionTitle);

  const list = document.createElement('ul');
  items.forEach((item) => {
    const li = document.createElement('li');
    li.innerText = item;
    list.appendChild(li);
  });
  card.appendChild(list);
}

function renderResults(recommendation) {
  const results = document.getElementById('results');
  results.innerHTML = '';

  const heading = document.createElement('h2');
  heading.innerText = `Designs for: ${recommendation.app_idea}`;
  results.appendChild(heading);

  const summary = document.createElement('p');
  summary.innerText = recommendation.clarifying_summary.join(' | ');
  results.appendChild(summary);

  recommendation.designs.forEach((design) => {
    const card = document.createElement('article');
    card.className = 'option-card';

    const title = document.createElement('h3');
    title.innerText = design.level;

    const goal = document.createElement('p');
    goal.innerHTML = `<strong>Goal:</strong> ${design.goal}`;

    const components = document.createElement('p');
    components.innerHTML = `<strong>Components:</strong> ${design.components.join(', ')}`;

    const why = document.createElement('p');
    why.innerHTML = `<strong>Why this level:</strong> ${design.why_this_level}`;

    const diagramTitle = document.createElement('h4');
    diagramTitle.innerText = 'System Design Diagram';

    const diagram = document.createElement('pre');
    diagram.innerText = design.diagram;

    card.appendChild(title);
    card.appendChild(goal);
    card.appendChild(components);
    card.appendChild(why);
    card.appendChild(diagramTitle);
    card.appendChild(diagram);

    addListSection(card, 'User Actions', design.user_actions);
    addListSection(card, 'Traffic Flow', design.traffic_flow);

    results.appendChild(card);
  });
}

async function generateOptions() {
  const appIdea = document.getElementById('appIdea').value.trim();
  const response = await fetch('/api/system-design/options', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_idea: appIdea, answers: collectAnswers() }),
  });

  const payload = await response.json();
  if (!response.ok) {
    alert(payload.error || 'Failed to generate architecture');
    return;
  }

  renderResults(payload);
}

document.getElementById('askQuestions').addEventListener('click', askClarifyingQuestions);
document.getElementById('generate').addEventListener('click', generateOptions);
