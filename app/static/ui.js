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
      </td>
    `;
    tbody.appendChild(tr);
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

async function createExercise(ev) {
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
  const res = await fetch('/exercises', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    document.getElementById('exerciseForm').reset();
    document.getElementById('msg').textContent = 'Saved ✓';
    fetchExercises();
  } else {
    const txt = await res.text();
    document.getElementById('msg').textContent = 'Error: ' + txt;
  }
  return false;
}

window.addEventListener('DOMContentLoaded', fetchExercises);
