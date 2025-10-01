from fastapi import FastAPI
from .database import Base, engine
from . import models
from .routers import exercises, sessions
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

# Create tables 
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knee Rehab Habit Tracker", version="0.1.0")

app.include_router(exercises.router)
app.include_router(sessions.router)


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
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Knee Rehab Tracker</title>
  <link rel=\"stylesheet\" href=\"/static/styles.css?v=4\">
</head>
<body>
  <header>
    <div style=\"display:flex;align-items:center;justify-content:center;gap:1.2em;\">
      <div style=\"background:#fff;border-radius:50%;padding:0.7em;box-shadow:0 2px 8px rgba(25,118,210,0.13);display:flex;align-items:center;justify-content:center;\">
        <svg width=\"36\" height=\"36\" fill=\"none\" viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"12\" fill=\"#1976d2\"/><path d=\"M12 7v5l4 2\" stroke=\"#fff\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>
      </div>
      <div>
        <h1 style=\"margin:0;font-size:2.1rem;font-weight:700;letter-spacing:0.02em;\">Knee Rehab Tracker</h1>
        <div class=\"subtitle\">Your recovery journey</div>
      </div>
    </div>
  </header>
  <nav>
    <button class=\"nav-btn active\" id=\"nav-exercises\"><span>🏋️‍♂️</span> Exercises</button>
    <button class=\"nav-btn\" id=\"nav-sessions\"><span>📅</span> Sessions</button>
    <button class=\"nav-btn\" id=\"nav-stats\"><span>📊</span> Statistics</button>
  </nav>
  <div class=\"main-container\">
  <section class=\"card\" id=\"card-exercises\"> 
      <div class=\"section-title\">Exercise Library <span class=\"accent\"></span></div>
      <form id="exerciseForm">
        <div class="grid" style="grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1.2em 2em; margin-bottom: 0.5em;">
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
        </div>
        <div class="grid" style="grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1.2em 2em; margin-bottom: 0.5em;">
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
          <legend>Days of Week</legend>
          <label><input type="checkbox" name="dow" value="0"> Sun</label>
          <label><input type="checkbox" name="dow" value="1"> Mon</label>
          <label><input type="checkbox" name="dow" value="2"> Tue</label>
          <label><input type="checkbox" name="dow" value="3"> Wed</label>
          <label><input type="checkbox" name="dow" value="4"> Thu</label>
          <label><input type="checkbox" name="dow" value="5"> Fri</label>
          <label><input type="checkbox" name="dow" value="6"> Sat</label>
        </fieldset>
        <button type="submit" class="btn-primary" id="exerciseFormSubmit">Add Exercise</button>
        <button type="button" class="btn-outline" id="exerciseFormCancel" style="margin-left:10px">Cancel</button>
        <span id="msg" class="msg"></span>
      </form>
    </section>
  <section class=\"card\" id=\"card-exercise-table\"> 
      <div class=\"section-title\">Exercises <span class=\"accent\"></span></div>
      <table id=\"exerciseTable\" class=\"table\">
        <thead>
          <tr>
            <th>ID</th><th>Name</th><th>Side</th><th>Category</th>
            <th>Targets</th><th>Schedule</th><th>Actions</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </section>
  <section class=\"card\" id=\"card-quicklog\"> 
      <div class=\"section-title\">Quick Log <span class=\"accent\"></span></div>
      <form id="sessionForm">
        <div class="grid" style="grid-template-columns: repeat(2, minmax(0,1fr)); gap: 1.2em 2em; margin-bottom: 0.5em;">
          <label>Date
            <input id="session_date" type="date" required>
          </label>
          <label>Exercise
            <select id="session_exercise" required></select>
          </label>
        </div>
        <div class="grid" style="grid-template-columns: repeat(2, minmax(0,1fr)); gap: 1.2em 2em; margin-bottom: 0.5em;">
          <label>Sets
            <input id="session_sets" type="number" min="0">
          </label>
          <label>Reps
            <input id="session_reps" type="number" min="0">
          </label>
        </div>
        <div class="grid" style="grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1.2em 2em; margin-bottom: 0.5em;">
          <label>Hold (sec)
            <input id="session_hold_sec" type="number" min="0">
          </label>
          <label>Pain (0-10)
            <input id="session_pain" type="number" min="0" max="10">
          </label>
          <label>ROM (degrees)
            <input id="session_rom" type="number" min="0" max="180">
          </label>
        </div>
        <button type="submit" class="btn-primary" id="sessionFormSubmit">Log Session</button>
        <button type="button" class="btn-outline" id="sessionFormCancel" style="margin-left:10px">Cancel</button>
        <span id="session_msg" class="msg"></span>
      </form>
    </section>
  <section class=\"card\" id=\"card-sessions\"> 
      <div class=\"section-title\">Session History <span class=\"accent\"></span></div>
      <table id=\"sessionTable\" class=\"table\">
        <thead>
          <tr>
            <th>Date</th><th>Exercise</th><th>Sets</th><th>Reps</th><th>Hold</th><th>Pain</th><th>ROM</th><th>Actions</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </section>
  <section class=\"card\" id=\"card-stats\"> 
      <div class=\"section-title\">Stats / Progress <span class=\"accent\"></span></div>
      <div style=\"display:flex;gap:2em;align-items:flex-start;justify-content:center;flex-wrap:wrap;\">
        <div style=\"flex:1 1 350px;max-width:420px;\">
          <canvas id=\"categoryPieChart\" width=\"400\" height=\"300\"></canvas>
        </div>
        <div style=\"flex:1 1 350px;max-width:520px;\">
          <h3 style=\"margin-bottom:0.5em;font-size:1.1em;\">Pain Over Time</h3>
          <canvas id=\"painLineChart\" width=\"400\" height=\"300\"></canvas>
        </div>
      </div>
    </section>
  </div>
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
  <script src=\"/static/ui.js?v=4\"></script>
  <script>
    // Tab navigation: scroll to card and highlight active
    document.addEventListener('DOMContentLoaded', function() {
      const navs = [
        {btn: 'nav-exercises', card: 'card-exercises'},
        {btn: 'nav-sessions', card: 'card-sessions'},
        {btn: 'nav-stats', card: 'card-stats'}
      ];
      navs.forEach((nav) => {
        const btn = document.getElementById(nav.btn);
        const card = document.getElementById(nav.card);
        btn.addEventListener('click', function() {
          // Remove active from all
          document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          // Scroll to card
          if (card) {
            card.scrollIntoView({behavior: 'smooth', block: 'start'});
          }
        });
      });
    });
  </script>
</body>
</html>
    """
