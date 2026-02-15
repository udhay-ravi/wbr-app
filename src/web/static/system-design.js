let latestDesign = null;

function createSelect(question) {
  const wrapper = document.createElement('div');
  wrapper.className = 'question';

  const label = document.createElement('label');
  label.setAttribute('for', question.id);
  label.innerText = question.label;

  const select = document.createElement('select');
  select.id = question.id;

  (question.options || []).forEach((option) => {
    const el = document.createElement('option');
    el.value = option;
    el.innerText = option;
    select.appendChild(el);
  });

  wrapper.appendChild(label);
  wrapper.appendChild(select);
  return wrapper;
}

async function loadQuestions() {
  const appIdea = document.getElementById('appIdea').value.trim();
  const response = await fetch('/api/system-design/questions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_idea: appIdea }),
  });

  const payload = await response.json();
  const questionnaire = document.getElementById('questionnaire');
  questionnaire.innerHTML = '';

  (payload.questions || [])
    .filter((question) => !['repo_url', 'app_idea'].includes(question.id))
    .forEach((question) => {
      questionnaire.appendChild(createSelect(question));
    });
}

function collectAnswers() {
  const answers = {
    repo_url: document.getElementById('repo_url').value.trim(),
  };

  document.querySelectorAll('.question select').forEach((select) => {
    answers[select.id] = select.value;
  });
  return answers;
}

function renderDesign(payload) {
  const results = document.getElementById('results');
  results.innerHTML = '';

  const design = payload.designs[0];
  const header = document.createElement('h2');
  header.innerText = `${payload.repository.owner}/${payload.repository.repo} architecture`;

  const summary = document.createElement('p');
  summary.innerText = `${payload.target.provider} · ${payload.target.region} · ${payload.target.environment}`;

  const diagramTitle = document.createElement('h3');
  diagramTitle.innerText = 'System Design Diagram';

  const diagram = document.createElement('pre');
  diagram.innerText = design.diagram;

  const components = document.createElement('p');
  components.innerHTML = `<strong>Components:</strong> ${design.components.join(', ')}`;

  const notes = document.createElement('ul');
  design.notes.forEach((note) => {
    const li = document.createElement('li');
    li.innerText = note;
    notes.appendChild(li);
  });

  results.appendChild(header);
  results.appendChild(summary);
  results.appendChild(diagramTitle);
  results.appendChild(diagram);
  results.appendChild(components);
  results.appendChild(notes);
}

async function generateDesign() {
  await loadQuestions();
  const response = await fetch('/api/system-design/options', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      app_idea: document.getElementById('appIdea').value.trim(),
      answers: collectAnswers(),
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    alert(payload.error || 'Failed to generate design');
    return;
  }

  latestDesign = payload;
  renderDesign(payload);
  document.getElementById('deploy').disabled = false;
}

async function deployToDo() {
  if (!latestDesign) {
    return;
  }

  const token = document.getElementById('do_token').value.trim();
  const response = await fetch('/api/system-design/deploy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_full_name: `${latestDesign.repository.owner}/${latestDesign.repository.repo}`,
      region: latestDesign.target.region,
      do_token: token,
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    alert(payload.error || 'Deployment failed');
    return;
  }

  const results = document.getElementById('results');
  const deployment = document.createElement('pre');
  deployment.innerText = `${payload.message}\n\n${payload.commands.join('\n')}`;
  results.appendChild(document.createElement('h3')).innerText = 'Deployment Commands';
  results.appendChild(deployment);
}

document.getElementById('generate').addEventListener('click', generateDesign);
document.getElementById('deploy').addEventListener('click', deployToDo);
loadQuestions();
