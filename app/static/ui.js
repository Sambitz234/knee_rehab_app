// --- Pain Line Chart ---
let painLineChartInstance = null;
async function renderPainLineChart() {
  const res = await fetch('/sessions');
  const sessions = await res.json();
  const exRes = await fetch('/exercises');
  const exercises = await exRes.json();
  const exMap = {};
  exercises.forEach(ex => { exMap[ex.id] = ex.name; });
  // Prepare data: x = exercise name, y = pain, each point is a session (date in tooltip)
  const points = [];
  sessions.forEach(s => {
    if (s.pain_0_10 !== null && s.pain_0_10 !== undefined) {
      points.push({
        x: exMap[s.exercise_id] || `Exercise ${s.exercise_id}`,
        y: s.pain_0_10,
        date: s.date
      });
    }
  });
  // Sort by exercise name then date
  points.sort((a, b) => a.x.localeCompare(b.x) || a.date.localeCompare(b.date));
  const ctx = document.getElementById('painLineChart');
  if (!ctx) return;
  if (painLineChartInstance) painLineChartInstance.destroy();
  painLineChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: points.map(p => p.x),
      datasets: [{
        label: 'Pain (0-10) per Session',
        data: points.map(p => p.y),
        borderColor: chartColor(0),
        backgroundColor: chartColor(0, 0.2),
        tension: 0.2,
        spanGaps: true,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: false,
      plugins: {
        legend: { display: false },
        title: { display: true, text: 'Pain (0-10) per Exercise' },
        tooltip: {
          callbacks: {
            title: (items) => {
              const idx = items[0].dataIndex;
              return points[idx].x + ' (' + points[idx].date + ')';
            },
            label: (item) => 'Pain: ' + item.formattedValue
          }
        }
      },
      scales: {
        x: { type: 'category', title: {display:true, text:'Exercise'} },
        y: { min: 0, max: 10, title: {display:true, text:'Pain (0-10)'} }
      }
    }
  });
}

// Helper for distinct colors
function chartColor(idx, alpha=1) {
  const palette = [
    '54,162,235', // blue
    '255,99,132', // red
    '255,206,86', // yellow
    '75,192,192', // teal
    '153,102,255', // purple
    '255,159,64', // orange
    '201,203,207' // gray
  ];
  const c = palette[idx % palette.length];
  return `rgba(${c},${alpha})`;
}
// --- Session actions ---
async function deleteSession(id) {
  const ok = confirm('Delete session #' + id + '?');
  if (!ok) return;
  const res = await fetch(`/sessions/${id}`, { method: 'DELETE' });
  if (res.status === 204) {
    await fetchSessions();
  } else {
    alert('Failed to delete (status ' + res.status + ')');
  }
}

let editingSessionId = null;
async function editSession(id) {
  const res = await fetch(`/sessions/${id}`);
  if (!res.ok) {
    alert('Failed to fetch session');
    return;
  }
  const s = await res.json();
  document.getElementById('session_date').value = s.date;
  document.getElementById('session_exercise').value = s.exercise_id;
  document.getElementById('session_sets').value = s.sets ?? '';
  document.getElementById('session_reps').value = s.reps ?? '';
  document.getElementById('session_hold_sec').value = s.hold_sec ?? '';
  document.getElementById('session_pain').value = s.pain_0_10 ?? '';
  editingSessionId = id;
  document.getElementById('sessionFormSubmit').textContent = 'Update Session';
  document.getElementById('session_msg').textContent = 'Editing #' + id;
}

// Patch createSession to handle update if editingSessionId is set
const origCreateSession = createSession;
async function createSession(ev) {
  ev.preventDefault();
  let payload = {
    exercise_id: Number(document.getElementById('session_exercise').value),
    date: document.getElementById('session_date').value,
    sets: Number(document.getElementById('session_sets').value) || null,
    reps: Number(document.getElementById('session_reps').value) || null,
    hold_sec: Number(document.getElementById('session_hold_sec').value) || null,
    pain_0_10: Number(document.getElementById('session_pain').value) || null
  };
  // For update, only send fields that are not null/empty (exclude unset)
  if (editingSessionId !== null) {
    Object.keys(payload).forEach(k => {
      if (payload[k] === null || payload[k] === '' || payload[k] === undefined) {
        delete payload[k];
      }
    });
  }
  let url = '/sessions';
  let method = 'POST';
  if (editingSessionId !== null) {
    url = `/sessions/${editingSessionId}`;
    method = 'PUT';
  }
  const res = await fetch(url, {
    method,
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    document.getElementById('sessionForm').reset();
    document.getElementById('session_msg').textContent = editingSessionId === null ? 'Session entry added ✓' : 'Session updated ✓';
    editingSessionId = null;
    document.getElementById('sessionFormSubmit').textContent = 'Log Session';
    fetchSessions();
  } else {
    const txt = await res.text();
    document.getElementById('session_msg').textContent = 'Error: ' + txt;
  }
  return false;
}

function resetSessionForm() {
  document.getElementById('sessionForm').reset();
  editingSessionId = null;
  document.getElementById('sessionFormSubmit').textContent = 'Log Session';
  document.getElementById('session_msg').textContent = '';
}

window.addEventListener('DOMContentLoaded', () => {
  // ...existing code...
  // Always attach cancel handler to Cancel button if present
  let cancelBtn = document.getElementById('sessionFormCancel');
  if (cancelBtn) {
    cancelBtn.onclick = resetSessionForm;
  }
});
async function fetchExercises() {
  const res = await fetch('/exercises');
  const data = await res.json();
  const tbody = document.querySelector('#exerciseTable tbody');
  tbody.innerHTML = '';
  data.forEach(ex => {
    const tr = document.createElement('tr');
    const targets = `${ex.target_sets ?? '-'}×${ex.target_reps ?? '-'} @ ${ex.target_hold_sec ?? 0}s`;
    const schedule = (ex.schedule_dow || []).sort().join(', ');
    tr.innerHTML = `
      <td>${ex.id}</td>
      <td>${ex.name}</td>
      <td><span class="badge">${ex.side}</span></td>
      <td><span class="badge">${ex.category}</span></td>
      <td>${targets}</td>
      <td>${schedule}</td>
      <td>
        <button class="action-del" onclick="deleteExercise(${ex.id})">Delete</button>
        <button onclick="editExercise(${ex.id})">Edit</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Populate session exercise dropdown
  const sessionExercise = document.getElementById('session_exercise');
  if (sessionExercise) {
    sessionExercise.innerHTML = '';
    data.forEach(ex => {
      const opt = document.createElement('option');
      opt.value = ex.id;
      opt.textContent = ex.name;
      sessionExercise.appendChild(opt);
    });
  }

  // --- Pie chart for category distribution ---
  renderCategoryPieChart(data);
}

// Pie chart rendering for exercise category distribution
let categoryPieChartInstance = null;
function renderCategoryPieChart(exercises) {
  const ctx = document.getElementById('categoryPieChart');
  if (!ctx) return;
  // Count categories
  const counts = { strength: 0, mobility: 0, balance: 0 };
  exercises.forEach(ex => {
    if (counts[ex.category] !== undefined) counts[ex.category]++;
  });
  const labels = ['Strength', 'Mobility', 'Balance'];
  const data = [counts.strength, counts.mobility, counts.balance];
  // Destroy previous chart if exists
  if (categoryPieChartInstance) {
    categoryPieChartInstance.destroy();
  }
  categoryPieChartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          'rgba(54, 162, 235, 0.7)', // strength
          'rgba(255, 206, 86, 0.7)', // mobility
          'rgba(75, 192, 192, 0.7)'  // balance
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom'
        },
        title: {
          display: true,
          text: 'Exercise Category Distribution'
        }
      }
    }
  });
}


async function deleteExercise(id) {
  const ok = confirm('Delete exercise #' + id + '?');
  if (!ok) return;
  const res = await fetch(`/exercises/${id}`, { method: 'DELETE' });
  if (res.status === 204) {
    await fetchExercises();
  } else {
    alert('Failed to delete (status ' + res.status + ')');
  }
}

function readCheckedDOW() {
  return Array.from(document.querySelectorAll('input[name="dow"]:checked'))
    .map(cb => Number(cb.value))
    .sort((a,b)=>a-b);
}


let editingExerciseId = null;

async function createOrUpdateExercise(ev) {
  ev.preventDefault();
  const payload = {
    name: document.getElementById('name').value.trim(),
    side: document.getElementById('side').value,
    category: document.getElementById('category').value,
    target_sets: Number(document.getElementById('target_sets').value) || null,
    target_reps: Number(document.getElementById('target_reps').value) || null,
    target_hold_sec: Number(document.getElementById('target_hold_sec').value) || null,
    schedule_dow: readCheckedDOW()
  };
  let url = '/exercises';
  let method = 'POST';
  if (editingExerciseId !== null) {
    url = `/exercises/${editingExerciseId}`;
    method = 'PUT';
  }
  const res = await fetch(url, {
    method,
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    document.getElementById('exerciseForm').reset();
    document.getElementById('msg').textContent = editingExerciseId === null ? 'Saved ✓' : 'Updated ✓';
    editingExerciseId = null;
    document.getElementById('exerciseFormSubmit').textContent = 'Add Exercise';
    fetchExercises();
  } else {
    const txt = await res.text();
    document.getElementById('msg').textContent = 'Error: ' + txt;
  }
  return false;
}

async function editExercise(id) {
  const res = await fetch(`/exercises/${id}`);
  if (!res.ok) {
    alert('Failed to fetch exercise');
    return;
  }
  const ex = await res.json();
  document.getElementById('name').value = ex.name;
  document.getElementById('side').value = ex.side;
  document.getElementById('category').value = ex.category;
  document.getElementById('target_sets').value = ex.target_sets ?? '';
  document.getElementById('target_reps').value = ex.target_reps ?? '';
  document.getElementById('target_hold_sec').value = ex.target_hold_sec ?? '';
  // Uncheck all DOW checkboxes first
  document.querySelectorAll('input[name="dow"]').forEach(cb => { cb.checked = false; });
  (ex.schedule_dow || []).forEach(dow => {
    const cb = document.querySelector(`input[name="dow"][value="${dow}"]`);
    if (cb) cb.checked = true;
  });
  editingExerciseId = id;
  document.getElementById('exerciseFormSubmit').textContent = 'Update Exercise';
  document.getElementById('msg').textContent = 'Editing #' + id;
}

function resetExerciseForm() {
  document.getElementById('exerciseForm').reset();
  editingExerciseId = null;
  document.getElementById('exerciseFormSubmit').textContent = 'Add Exercise';
  document.getElementById('msg').textContent = '';
}

window.addEventListener('DOMContentLoaded', () => {
  fetchExercises();
  // Attach new handler for form submit
  const form = document.getElementById('exerciseForm');
  if (form) {
    form.onsubmit = createOrUpdateExercise;
  }
  // Always attach cancel handler to Cancel button if present
  let cancelBtn = document.getElementById('exerciseFormCancel');
  if (cancelBtn) {
    cancelBtn.onclick = resetExerciseForm;
  } else if (form) {
    // fallback: add if not present
    cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.id = 'exerciseFormCancel';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.style.marginLeft = '10px';
    cancelBtn.onclick = resetExerciseForm;
    form.appendChild(cancelBtn);
  }

  // Session form handler
  const sessionForm = document.getElementById('sessionForm');
  if (sessionForm) {
    sessionForm.onsubmit = createSession;
  }
  fetchSessions();
  renderPainLineChart();
});

async function createSession(ev) {
  ev.preventDefault();
  const payload = {
    exercise_id: Number(document.getElementById('session_exercise').value),
    date: document.getElementById('session_date').value,
    sets: Number(document.getElementById('session_sets').value) || null,
    reps: Number(document.getElementById('session_reps').value) || null,
    hold_sec: Number(document.getElementById('session_hold_sec').value) || null,
    pain_0_10: Number(document.getElementById('session_pain').value) || null
  };
  const res = await fetch('/sessions', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    document.getElementById('sessionForm').reset();
    document.getElementById('session_msg').textContent = 'Session entry added ✓';
    fetchSessions();
  } else {
    const txt = await res.text();
    document.getElementById('session_msg').textContent = 'Error: ' + txt;
  }
  return false;
}

async function fetchSessions() {
  const res = await fetch('/sessions');
  const data = await res.json();
  // Get exercise names for mapping
  const exRes = await fetch('/exercises');
  const exData = await exRes.json();
  const exMap = {};
  exData.forEach(ex => { exMap[ex.id] = ex.name; });

  const tbody = document.querySelector('#sessionTable tbody');
  tbody.innerHTML = '';
  data.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.date}</td>
      <td>${exMap[s.exercise_id] || s.exercise_id}</td>
      <td>${s.sets ?? ''}</td>
      <td>${s.reps ?? ''}</td>
      <td>${s.hold_sec ?? ''}</td>
      <td>${s.pain_0_10 ?? ''}</td>
      <td>
        <button onclick="editSession(${s.id})">Edit</button>
        <button onclick="deleteSession(${s.id})">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  // Update pain line chart after sessions change
  renderPainLineChart();
}