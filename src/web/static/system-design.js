async function loadQuestions() {
  const response = await fetch('/api/system-design/questions');
  const payload = await response.json();
  const questionnaire = document.getElementById('questionnaire');

  payload.questions.forEach((question) => {
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
}

function collectAnswers() {
  const answers = {};
  document.querySelectorAll('.question select').forEach((select) => {
    answers[select.id] = select.value;
  });
  return answers;
}

function renderOptions(options) {
  const results = document.getElementById('results');
  results.innerHTML = '';

  options.forEach((option) => {
    const card = document.createElement('article');
    card.className = 'option-card';

    const heading = document.createElement('h2');
    heading.innerText = option.name;

    const fit = document.createElement('p');
    fit.innerHTML = `<strong>Best for:</strong> ${option.best_for}`;

    const components = document.createElement('p');
    components.innerHTML = `<strong>Cloud services:</strong> ${option.components.join(', ')}`;

    const diagramTitle = document.createElement('h3');
    diagramTitle.innerText = 'Architecture Diagram';

    const diagram = document.createElement('pre');
    diagram.innerText = option.diagram;

    const tradeoffs = document.createElement('ul');
    option.tradeoffs.forEach((item) => {
      const li = document.createElement('li');
      li.innerText = item;
      tradeoffs.appendChild(li);
    });

    const sizing = document.createElement('ul');
    option.sizing_notes.forEach((item) => {
      const li = document.createElement('li');
      li.innerText = item;
      sizing.appendChild(li);
    });

    card.appendChild(heading);
    card.appendChild(fit);
    card.appendChild(components);
    card.appendChild(diagramTitle);
    card.appendChild(diagram);
    card.appendChild(document.createElement('h3')).innerText = 'Trade-offs';
    card.appendChild(tradeoffs);
    card.appendChild(document.createElement('h3')).innerText = 'Sizing Notes';
    card.appendChild(sizing);

    results.appendChild(card);
  });
}

async function generateOptions() {
  const response = await fetch('/api/system-design/options', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers: collectAnswers() }),
  });

  const payload = await response.json();
  renderOptions(payload.options);
}

document.getElementById('generate').addEventListener('click', generateOptions);
loadQuestions();
