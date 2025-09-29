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
  // Optionally, add a cancel button if not present
  let cancelBtn = document.getElementById('exerciseFormCancel');
  if (!cancelBtn && form) {
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
}