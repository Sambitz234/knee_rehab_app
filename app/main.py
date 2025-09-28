from fastapi import FastAPI
from .database import Base, engine
from . import models
from .routers import exercises, sessions, stats
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

# Create tables 
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knee Rehab Habit Tracker", version="0.1.0")

app.include_router(exercises.router)
app.include_router(sessions.router)
app.include_router(stats.router)

@app.get("/")
@app.get("/", include_in_schema=False)
def root():
  return RedirectResponse(url="/ui")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/ui", response_class=HTMLResponse)
def ui_page():
    return """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Knee Rehab Habit Tracker</title>
<link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header><h1>Knee Rehab Habit Tracker</h1></header>

  <section class="card">
    <h2>Create Exercise</h2>
    <form id="exerciseForm">
      <div class="grid">
        <label>Name
          <input id="name" required placeholder="Heel Slides">
        </label>
        <label>Side
          <select id="side">
            <option value="left">left</option>
            <option value="right">right</option>
            <option value="both">both</option>
          </select>
        </label>
        <label>Category
          <select id="category">
            <option value="strength">strength</option>
            <option value="mobility" selected>mobility</option>
            <option value="balance">balance</option>
          </select>
        </label>
        <label>Target sets
          <input id="target_sets" type="number" min="0" value="3">
        </label>
        <label>Target reps
          <input id="target_reps" type="number" min="0" value="12">
        </label>
        <label>Target hold (sec)
          <input id="target_hold_sec" type="number" min="0" value="2">
        </label>
      </div>

      <fieldset class="dow">
        <legend>Days of Week (0=Sun … 6=Sat)</legend>
        <label><input type="checkbox" name="dow" value="0"> Sun</label>
        <label><input type="checkbox" name="dow" value="1"> Mon</label>
        <label><input type="checkbox" name="dow" value="2"> Tue</label>
        <label><input type="checkbox" name="dow" value="3"> Wed</label>
        <label><input type="checkbox" name="dow" value="4"> Thu</label>
        <label><input type="checkbox" name="dow" value="5"> Fri</label>
        <label><input type="checkbox" name="dow" value="6"> Sat</label>
      </fieldset>

      <button type="submit" id="exerciseFormSubmit">Add Exercise</button>
      <span id="msg" class="msg"></span>
      <!-- Cancel button will be injected by JS if not present -->
    </form>
  </section>

  <section class="card">
    <h2>Create Session</h2>
    <form id="sessionForm">
      <div class="grid">
        <label>Date
          <input id="session_date" type="date" required>
        </label>
        <label>Exercise
          <select id="session_exercise" required></select>
        </label>
        <label>Sets
          <input id="session_sets" type="number" min="0">
        </label>
        <label>Reps
          <input id="session_reps" type="number" min="0">
        </label>
        <label>Hold (sec)
          <input id="session_hold_sec" type="number" min="0">
        </label>
        <label>Pain (0-10)
          <input id="session_pain" type="number" min="0" max="10">
        </label>
        <label>ROM (deg)
          <input id="session_rom" type="number" min="0" max="180">
        </label>
        <label>Notes
          <input id="session_notes" type="text">
        </label>
      </div>
      <button type="submit" id="sessionFormSubmit">Add Session Entry</button>
      <span id="session_msg" class="msg"></span>
    </form>
  </section>

  <section class="card">
    <h2>Sessions</h2>
    <table id="sessionTable">
      <thead>
        <tr>
          <th>Date</th><th>Exercise</th><th>Sets</th><th>Reps</th><th>Hold</th><th>Pain</th><th>ROM</th><th>Notes</th><th>Actions</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </section>

  <section class="card">
    <h2>Exercises</h2>
    <table id="exerciseTable">
      <thead>
        <tr>
          <th>ID</th><th>Name</th><th>Side</th><th>Category</th>
          <th>Targets</th><th>Schedule</th><th>Actions</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </section>

  <script src="/static/ui.js"></script>
</body>
</html>
    """
