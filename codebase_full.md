# Knee Rehab Habit Tracker

## app/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./rehab.db"

# Needed for SQLite in single-threaded dev servers
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## app/models.py

```python
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(120),
        nullable=False,
        unique=False,
        index=True,
    )
    side = Column(
        String(10),
        nullable=False,
    )
    category = Column(
        String(20),
        nullable=False,
    )
    target_sets = Column(Integer, nullable=True)
    target_reps = Column(Integer, nullable=True)
    target_hold_sec = Column(Integer, nullable=True)
    schedule_dow = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship(
        "ExerciseSession",
        back_populates="exercise",
        cascade="all, delete",
    )

class ExerciseSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(
        Integer,
        ForeignKey("exercises.id"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False)
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    hold_sec = Column(Integer, nullable=True)
    pain_0_10 = Column(Integer, nullable=True)  
    rom_deg = Column(Integer, nullable=True)   
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    exercise = relationship("Exercise", back_populates="sessions")
```

## app/main.py

```python
from fastapi import FastAPI, Request
from .database import Base, engine
from .routers import exercises, sessions, health
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import time
from prometheus_client import Counter, Histogram

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knee Rehab Habit Tracker", version="0.1.0")

app.include_router(exercises.router)
app.include_router(sessions.router)
app.include_router(health.router)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)
ERROR_COUNT = Counter(
    "http_request_errors_total",
    "Total HTTP request errors",
    ["method", "path", "status"],
)


@app.get("/")
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui")


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    method = request.method
    path = request.url.path
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    except Exception:
        # increment error counter and re-raise
        ERROR_COUNT.labels(method=method, path=path, status="500").inc()
        raise
    finally:
        # Observe latency and increment counters
        elapsed = time.perf_counter() - start
        # If response is available in finally, get status; otherwise default to 500
        try:
            status = str(response.status_code)
        except Exception:
            status = "500"
        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)


@app.get("/ui", response_class=HTMLResponse)
def ui_page():
    return FileResponse("app/static/ui.html", media_type="text/html")
```

## app/services/exercises.py

```python
import json
from sqlalchemy.orm import Session
from .. import models
from .. import schemas


def create_exercise(
    db: Session, payload: schemas.ExerciseCreate
) -> schemas.ExerciseOut:
    ex = models.Exercise(
        name=payload.name,
        side=payload.side,
        category=payload.category,
        target_sets=payload.target_sets,
        target_reps=payload.target_reps,
        target_hold_sec=payload.target_hold_sec,
        schedule_dow=json.dumps(payload.schedule_dow or []),
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return schemas.ExerciseOut(
        id=ex.id,
        name=ex.name,
        side=ex.side,
        category=ex.category,
        target_sets=ex.target_sets,
        target_reps=ex.target_reps,
        target_hold_sec=ex.target_hold_sec,
        schedule_dow=json.loads(ex.schedule_dow or "[]"),
    )


def list_exercises(db: Session) -> list[schemas.ExerciseOut]:
    items = db.query(models.Exercise).order_by(models.Exercise.id).all()
    result: list[schemas.ExerciseOut] = []
    for ex in items:
        result.append(
            schemas.ExerciseOut(
                id=ex.id,
                name=ex.name,
                side=ex.side,
                category=ex.category,
                target_sets=ex.target_sets,
                target_reps=ex.target_reps,
                target_hold_sec=ex.target_hold_sec,
                schedule_dow=json.loads(ex.schedule_dow or "[]"),
            )
        )
    return result


def get_exercise(db: Session, exercise_id: int) -> schemas.ExerciseOut | None:
    ex = db.get(models.Exercise, exercise_id)
    if not ex:
        return None
    return schemas.ExerciseOut(
        id=ex.id,
        name=ex.name,
        side=ex.side,
        category=ex.category,
        target_sets=ex.target_sets,
        target_reps=ex.target_reps,
        target_hold_sec=ex.target_hold_sec,
        schedule_dow=json.loads(ex.schedule_dow or "[]"),
    )


def update_exercise(
    db: Session,
    exercise_id: int,
    payload: schemas.ExerciseUpdate,
) -> schemas.ExerciseOut | None:
    ex = db.get(models.Exercise, exercise_id)
    if not ex:
        return None
    data = payload.model_dump(exclude_unset=True)
    # apply updates
    for field, value in data.items():
        if field == "schedule_dow":
            setattr(ex, field, json.dumps(value))
        else:
            setattr(ex, field, value)
    db.commit()
    db.refresh(ex)
    return schemas.ExerciseOut(
        id=ex.id,
        name=ex.name,
        side=ex.side,
        category=ex.category,
        target_sets=ex.target_sets,
        target_reps=ex.target_reps,
        target_hold_sec=ex.target_hold_sec,
        schedule_dow=json.loads(ex.schedule_dow or "[]"),
    )


def delete_exercise(db: Session, exercise_id: int) -> bool:
    ex = db.get(models.Exercise, exercise_id)
    if not ex:
        return False
    db.delete(ex)
    db.commit()
    return True
```

## app/services/sessions.py

```python
from sqlalchemy.orm import Session
from .. import models
from .. import schemas


def get_session(db: Session, id: int) -> schemas.SessionOut | None:
    s = db.get(models.ExerciseSession, id)
    if not s:
        return None
    return s


def update_session(
    db: Session,
    id: int,
    payload: schemas.SessionUpdate,
) -> schemas.SessionOut | None:
    s = db.get(models.ExerciseSession, id)
    if not s:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s


def delete_session(db: Session, id: int) -> bool:
    s = db.get(models.ExerciseSession, id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


def create_session(
    db: Session, payload: schemas.SessionCreate
) -> schemas.SessionOut:
    # Ensure exercise exists
    if not db.get(models.Exercise, payload.exercise_id):
        return None
    s = models.ExerciseSession(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def list_sessions(db: Session, from_date=None, to_date=None, exercise_id=None):
    q = db.query(models.ExerciseSession)
    if from_date:
        q = q.filter(models.ExerciseSession.date >= from_date)
    if to_date:
        q = q.filter(models.ExerciseSession.date <= to_date)
    if exercise_id:
        q = q.filter(models.ExerciseSession.exercise_id == exercise_id)
    return q.order_by(
        models.ExerciseSession.date.desc(),
        models.ExerciseSession.id.desc(),
    ).all()
```

## app/routers/health.py

```python
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import get_db
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """Return basic health status and check DB with a simple query."""
    try:
        # simple lightweight DB check
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        return {"status": "ok", "db": "error"}


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics in text format."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
```

## app/routers/sessions.py

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from .. import schemas
from ..services import sessions as session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{id}", response_model=schemas.SessionOut)
def get_session(id: int, db: Session = Depends(get_db)):
    s = session_service.get_session(db, id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


@router.put("/{id}", response_model=schemas.SessionOut)
def update_session(
    id: int,
    payload: schemas.SessionUpdate,
    db: Session = Depends(get_db),
):
    s = session_service.update_session(db, id, payload)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


@router.delete("/{id}", status_code=204)
def delete_session(id: int, db: Session = Depends(get_db)):
    ok = session_service.delete_session(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("", response_model=schemas.SessionOut)
def create_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    s = session_service.create_session(db, payload)
    if not s:
        raise HTTPException(status_code=400, detail="Exercise does not exist")
    return s


@router.get(
    "",
    response_model=list[schemas.SessionOut],
)
def list_sessions(
    db: Session = Depends(get_db),
    from_date: date = Query(default=None),
    to_date: date = Query(default=None),
    exercise_id: int | None = Query(default=None),
):
    return session_service.list_sessions(db, from_date, to_date, exercise_id)
```

## app/schemas.py

```python
from __future__ import annotations

from typing import Optional, List, Literal
from datetime import date

from pydantic import BaseModel, Field, conint

PainInt = Optional[conint(ge=0, le=10)]
ROMInt = Optional[conint(ge=0, le=180)]

Side = Literal["left", "right", "both"]
Category = Literal["strength", "mobility", "balance"]

class ExerciseBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    side: Side
    category: Category
    target_sets: Optional[int] = None
    target_reps: Optional[int] = None
    target_hold_sec: Optional[int] = None
    # 0=Sun, 1=Mon, ... 6=Sat
    schedule_dow: List[int] = Field(default_factory=list)  

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    side: Optional[Side] = None
    category: Optional[Category] = None
    target_sets: Optional[int] = None
    target_reps: Optional[int] = None
    target_hold_sec: Optional[int] = None
    schedule_dow: Optional[List[int]] = None

class ExerciseOut(ExerciseBase):
    id: int
    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    exercise_id: int
    date: date
    sets: Optional[int] = None
    reps: Optional[int] = None
    hold_sec: Optional[int] = None
    pain_0_10: PainInt = None
    rom_deg: ROMInt = None
class SessionUpdate(BaseModel):
    exercise_id: Optional[int] = None
    date: Optional[date] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    hold_sec: Optional[int] = None
    pain_0_10: PainInt = None
    rom_deg: ROMInt = None

class SessionCreate(SessionBase):
    pass

class SessionOut(SessionBase):
    id: int
    class Config:
        from_attributes = True
```

## app/routers/exercises.py

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas
from ..services import exercises as exercise_service

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("", response_model=schemas.ExerciseOut)
def create_exercise(payload: schemas.ExerciseCreate, db: Session = Depends(get_db)):
    return exercise_service.create_exercise(db, payload)


@router.get(
    "",
    response_model=list[schemas.ExerciseOut],
)
def list_exercises(db: Session = Depends(get_db)):
    return exercise_service.list_exercises(db)


@router.get("/{exercise_id}", response_model=schemas.ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    out = exercise_service.get_exercise(db, exercise_id)
    if not out:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return out


@router.put("/{exercise_id}", response_model=schemas.ExerciseOut)
def update_exercise(
    exercise_id: int,
    payload: schemas.ExerciseUpdate,
    db: Session = Depends(get_db),
):
    out = exercise_service.update_exercise(db, exercise_id, payload)
    if not out:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return out


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    ok = exercise_service.delete_exercise(db, exercise_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Exercise not found")
```

---
## app/static/ui.html
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Knee Rehab Tracker</title>
  <link rel="stylesheet" href="/static/styles.css?v=4">
</head>
<body>
  <header>
    <div style="display:flex;align-items:center;justify-content:center;gap:1.2em;">
      <div style="background:#fff;border-radius:50%;padding:0.7em;box-shadow:0 2px 8px rgba(25,118,210,0.13);display:flex;align-items:center;justify-content:center;">
        <svg width="36" height="36" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="#1976d2"/><path d="M12 7v5l4 2" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
      <div>
        <h1 style="margin:0;font-size:2.1rem;font-weight:700;letter-spacing:0.02em;">Knee Rehab Tracker</h1>
        <div class="subtitle">Your recovery journey</div>
      </div>
    </div>
  </header>
  <nav>
    <button class="nav-btn active" id="nav-exercises"><span>🏋️‍♂️</span> Exercises</button>
    <button class="nav-btn" id="nav-sessions"><span>📅</span> Sessions</button>
    <button class="nav-btn" id="nav-stats"><span>📊</span> Statistics</button>
  </nav>
  <div class="main-container">
  <section class="card" id="card-exercises"> 
      <div class="section-title">Exercise Library <span class="accent"></span></div>
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
  <section class="card" id="card-exercise-table"> 
      <div class="section-title">Exercises <span class="accent"></span></div>
      <table id="exerciseTable" class="table">
        <thead>
          <tr>
            <th>ID</th><th>Name</th><th>Side</th><th>Category</th>
            <th>Targets</th><th>Schedule</th><th>Actions</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </section>
  <section class="card" id="card-quicklog"> 
      <div class="section-title">Quick Log <span class="accent"></span></div>
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
  <section class="card" id="card-sessions"> 
      <div class="section-title">Session History <span class="accent"></span></div>
      <table id="sessionTable" class="table">
        <thead>
          <tr>
            <th>Date</th><th>Exercise</th><th>Sets</th><th>Reps</th><th>Hold</th><th>Pain</th><th>ROM</th><th>Actions</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </section>
  <section class="card" id="card-stats"> 
      <div class="section-title">Stats / Progress <span class="accent"></span></div>
      <div style="display:flex;gap:2em;align-items:flex-start;justify-content:center;flex-wrap:wrap;">
        <div style="flex:1 1 350px;max-width:420px;">
          <canvas id="categoryPieChart" width="400" height="300"></canvas>
        </div>
        <div style="flex:1 1 350px;max-width:520px;">
          <h3 style="margin-bottom:0.5em;font-size:1.1em;">Pain Over Time</h3>
          <canvas id="painLineChart" width="400" height="300"></canvas>
        </div>
      </div>
    </section>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="/static/ui.js?v=4"></script>
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
```

---
## app/static/styles.css
```css
:root {
	--primary-blue: #1976d2;
	--primary-blue-light: #2196f3;
	--accent-green: #4caf50;
	--accent-orange: #ff9800;
	--bg-light: #f5f7fa;
	--bg-gray: #e0e3e7;
	--white: #fff;
	--text-main: #222;
	--text-muted: #666;
	--shadow: 0 2px 8px rgba(25, 118, 210, 0.08);
	--radius: 16px;
	--transition: 0.3s cubic-bezier(.4,0,.2,1);
	--font-main: 'Inter', 'Segoe UI', Arial, sans-serif;
}

body {
	font-family: var(--font-main);
	background: var(--bg-light);
	color: var(--text-main);
	margin: 0;
	min-height: 100vh;
}

header {
	background: linear-gradient(90deg, var(--primary-blue), var(--primary-blue-light));
	color: var(--white);
	padding: 2rem 0 1rem 0;
	box-shadow: 0 2px 8px rgba(25, 118, 210, 0.15);
	position: sticky;
	top: 0;
	z-index: 100;
	text-align: center;
}
header h1 {
	font-size: 2.2rem;
	font-weight: 700;
	margin: 0 0 0.2em 0;
	letter-spacing: 0.02em;
}
header .subtitle {
	font-size: 1.1rem;
	font-weight: 400;
	opacity: 0.85;
	margin-bottom: 0.5em;
}

nav {
	display: flex;
	justify-content: center;
	background: var(--white);
	border-bottom: 1px solid var(--bg-gray);
	position: sticky;
	top: 70px;
	z-index: 99;
	box-shadow: 0 1px 4px rgba(25, 118, 210, 0.04);
}
nav .nav-btn {
	display: flex;
	align-items: center;
	gap: 0.5em;
	font-size: 1.1rem;
	color: var(--text-muted);
	background: none;
	border: none;
	padding: 1em 2em;
	cursor: pointer;
	transition: var(--transition);
	border-radius: 0 0 var(--radius) var(--radius);
	font-weight: 500;
}
nav .nav-btn.active {
	background: var(--primary-blue);
	color: var(--white);
	box-shadow: 0 2px 8px rgba(25, 118, 210, 0.10);
}
nav .nav-btn:not(.active):hover {
	background: var(--primary-blue-light);
	color: var(--white);
}

.main-container {
	max-width: 1100px;
	margin: 2.5rem auto;
	padding: 0 1.5rem;
}
.section-title {
	font-size: 1.5rem;
	font-weight: 700;
	margin-bottom: 0.2em;
	display: flex;
	align-items: center;
	gap: 0.5em;
}
.section-title .accent {
	display: inline-block;
	width: 32px;
	height: 4px;
	background: var(--primary-blue);
	border-radius: 2px;
	margin-left: 0.5em;
}

.card {
	background: linear-gradient(120deg, var(--white) 80%, var(--bg-gray) 100%);
	border-radius: var(--radius);
	box-shadow: var(--shadow);
	padding: 2rem 2rem 1.5rem 2rem;
	margin-bottom: 2rem;
	transition: box-shadow var(--transition), transform var(--transition);
}
.card:hover {
	box-shadow: 0 6px 24px rgba(25, 118, 210, 0.13);
	transform: translateY(-2px) scale(1.01);
}

.btn-primary {
	background: linear-gradient(90deg, var(--primary-blue), var(--primary-blue-light));
	color: var(--white);
	border: none;
	border-radius: 8px;
	padding: 0.7em 2em;
	font-size: 1.1rem;
	font-weight: 600;
	cursor: pointer;
	box-shadow: 0 2px 8px rgba(25, 118, 210, 0.10);
	transition: var(--transition);
}
.btn-primary:hover {
	background: linear-gradient(90deg, var(--primary-blue-light), var(--primary-blue));
	box-shadow: 0 4px 16px rgba(25, 118, 210, 0.15);
}
.btn-outline {
	background: none;
	color: var(--primary-blue);
	border: 2px solid var(--primary-blue);
	border-radius: 8px;
	padding: 0.7em 2em;
	font-size: 1.1rem;
	font-weight: 600;
	cursor: pointer;
	transition: var(--transition);
}
.btn-outline:hover {
	background: var(--primary-blue-light);
	color: var(--white);
}

input, select, textarea {
	font-family: inherit;
	font-size: 1rem;
	border: 1.5px solid var(--bg-gray);
	border-radius: 6px;
	padding: 0.5em 1em;
	margin-bottom: 0.7em;
	background: var(--white);
	transition: border-color var(--transition);
}
input:focus, select:focus, textarea:focus {
	border-color: var(--primary-blue);
	outline: none;
}
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
	-webkit-appearance: none;
	margin: 0;
}

label {
	font-weight: 500;
	color: var(--text-muted);
	margin-bottom: 0.2em;
	display: block;
}

.grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	gap: 1.2em 2em;
	margin-bottom: 1.2em;
}

fieldset.dow {
	border: none;
	margin: 0 0 1em 0;
	padding: 0;
	display: flex;
	gap: 1em;
	flex-wrap: wrap;
}
fieldset.dow legend {
	font-size: 1rem;
	font-weight: 600;
	color: var(--primary-blue);
	margin-bottom: 0.5em;
}

.badge {
	display: inline-block;
	padding: 0.2em 0.8em;
	border-radius: 12px;
	font-size: 0.95em;
	font-weight: 600;
	margin-right: 0.3em;
	background: var(--bg-gray);
	color: var(--primary-blue);
}
.badge.strength {
	background: var(--primary-blue);
	color: var(--white);
}
.badge.mobility {
	background: var(--accent-green);
	color: var(--white);
}
.badge.balance {
	background: var(--accent-orange);
	color: var(--white);
}
.badge.side {
	border: 1.5px solid var(--primary-blue);
	background: var(--white);
	color: var(--primary-blue);
}

.table {
	width: 100%;
	border-collapse: separate;
	border-spacing: 0 0.5em;
	margin-bottom: 1.5em;
	table-layout: fixed;
}

#sessionTable th:nth-child(1) { width: 15%; } /* Date */
#sessionTable th:nth-child(2) { width: 25%; } /* Exercise */
#sessionTable th:nth-child(3) { width: 10%; } /* Sets */
#sessionTable th:nth-child(4) { width: 10%; } /* Reps */
#sessionTable th:nth-child(5) { width: 10%; } /* Hold */
#sessionTable th:nth-child(6) { width: 10%; } /* Pain */
#sessionTable th:nth-child(7) { width: 10%; } /* ROM */
#sessionTable th:nth-child(8) { width: 10%; } /* Actions */
.table th, .table td {
	padding: 0.8em 1em;
	background: var(--white);
	border-radius: 8px;
	text-align: left;
}
.table th {
	background: var(--bg-gray);
	color: var(--primary-blue);
	font-weight: 700;
	font-size: 1.05em;
}

.action-del {
	color: #e53935;
	border: 1.5px solid #e53935;
	background: none;
	border-radius: 6px;
	padding: 0.3em 1em;
	font-weight: 600;
	cursor: pointer;
	margin-right: 0.5em;
	transition: var(--transition);
}
.action-del:hover {
	background: #e53935;
	color: var(--white);
}

.msg {
	color: var(--accent-green);
	font-weight: 500;
	margin-left: 1em;
}

@media (max-width: 800px) {
	.main-container {
		padding: 0 0.5rem;
	}
	.card {
		padding: 1.2rem 0.7rem 1rem 0.7rem;
	}
	.grid {
		grid-template-columns: 1fr;
	}
}

@media (max-width: 500px) {
	header h1 {
		font-size: 1.3rem;
	}
	.section-title {
		font-size: 1.1rem;
	}
	.card {
		padding: 0.7rem 0.2rem 0.7rem 0.2rem;
	}
}


```

---
## app/static/ui.js
```javascript
// --- Pain Line Chart ---
let painLineChartInstance = null;
async function renderPainLineChart() {
  const res = await fetch('/sessions');
  const sessions = await res.json();
  const exRes = await fetch('/exercises');
  const exercises = await exRes.json();
  const exMap = {};
  exercises.forEach(ex => { exMap[ex.id] = ex.name; });
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
  // Sort by exercise date
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
  document.getElementById('session_rom').value = s.rom_deg ?? '';
  editingSessionId = id;
  document.getElementById('sessionFormSubmit').textContent = 'Update Session';
  document.getElementById('session_msg').textContent = 'Editing #' + id;
}

// Handle both create and update operations for sessions
async function createSession(ev) {
  ev.preventDefault();
  const romValue = document.getElementById('session_rom').value;
  
  let payload = {
    exercise_id: Number(document.getElementById('session_exercise').value),
    date: document.getElementById('session_date').value,
    sets: Number(document.getElementById('session_sets').value) || null,
    reps: Number(document.getElementById('session_reps').value) || null,
    hold_sec: Number(document.getElementById('session_hold_sec').value) || null,
    pain_0_10: Number(document.getElementById('session_pain').value) || null,
    rom_deg: romValue ? Number(romValue) : null
  };
  console.log('ROM value from form:', romValue);
  console.log('Payload being sent:', payload);
  // For update, only send non-null optional fields (keep exercise_id and date always)
  if (editingSessionId !== null) {
    // Keep exercise_id and date, only remove null optional fields
    const optionalFields = ['sets', 'reps', 'hold_sec', 'pain_0_10', 'rom_deg'];
    optionalFields.forEach(field => {
      if (payload[field] === null || payload[field] === '' || payload[field] === undefined) {
        delete payload[field];
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
    console.log('Session data:', s); // Debug log
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.date}</td>
      <td>${exMap[s.exercise_id] || s.exercise_id}</td>
      <td>${s.sets ?? ''}</td>
      <td>${s.reps ?? ''}</td>
      <td>${s.hold_sec ?? ''}</td>
      <td>${s.pain_0_10 ?? ''}</td>
      <td>${s.rom_deg ?? ''}</td>
      <td>
        <button onclick="editSession(${s.id})">Edit</button>
        <button onclick="deleteSession(${s.id})">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  // Update chart
  renderPainLineChart();
}
```

---
## monitoring/prometheus.yml
```yaml
# Prometheus configuration for knee_rehab_app
# Scrapes metrics from the FastAPI app

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'knee_rehab_app'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

---
## monitoring/grafana-dashboard.json
```json
{
  "dashboard": {
    "id": null,
    "uid": "knee-rehab-metrics",
    "title": "Knee Rehab - Metrics",
    "panels": [
      {
        "type": "graph",
        "title": "Request rate (r/s)",
        "gridPos": {"x":0,"y":0,"w":12,"h":6},
        "targets": [
          {"expr": "sum(rate(http_requests_total[1m]))", "legendFormat": "requests/s"}
        ]
      },
      {
        "type": "graph",
        "title": "Request latency (p95, avg)",
        "gridPos": {"x":12,"y":0,"w":12,"h":6},
        "targets": [
          {"expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))", "legendFormat": "p95"},
          {"expr": "sum(rate(http_request_duration_seconds_sum[5m])) / sum(rate(http_request_duration_seconds_count[5m]))", "legendFormat": "avg"}
        ]
      },
      {
        "type": "graph",
        "title": "Errors (r/s)",
        "gridPos": {"x":0,"y":6,"w":24,"h":6},
        "targets": [
          {"expr": "sum(rate(http_request_errors_total[1m]))", "legendFormat": "errors/s"}
        ]
      }
    ],
    "schemaVersion": 16,
    "version": 1
  },
  "overwrite": true
}

```

---
## tests/test_exercises.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_exercise():
    payload = {
        "name": "Heel Slides",
        "side": "left",
        "category": "mobility",
        "target_sets": 3,
        "target_reps": 12,
        "target_hold_sec": 2,
        "schedule_dow": [1,3,5]
    }
    response = client.post("/exercises", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Heel Slides"
    assert data["side"] == "left"
    assert data["category"] == "mobility"

def test_get_exercises():
    response = client.get("/exercises")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---
## tests/test_main.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
```

---
## tests/test_models.py
```python
from app.models import Exercise, ExerciseSession

def test_exercise_model():
    ex = Exercise(name="Test", side="left", category="mobility")
    assert ex.name == "Test"
    assert ex.side == "left"
    assert ex.category == "mobility"

def test_session_model():
    sess = ExerciseSession(exercise_id=1, date="2023-01-01")
    assert sess.exercise_id == 1
    assert sess.date == "2023-01-01"
```

---
## tests/test_schemas.py
```python
from app.schemas import ExerciseCreate, ExerciseSessionCreate

def test_exercise_create_schema():
    ex = ExerciseCreate(name="Test", side="right", category="strength", target_sets=2, target_reps=10, target_hold_sec=1, schedule_dow=[1,2])
    assert ex.name == "Test"
    assert ex.side == "right"
    assert ex.category == "strength"
    assert ex.target_sets == 2
    assert ex.schedule_dow == [1,2]

def test_session_create_schema():
    sess = ExerciseSessionCreate(exercise_id=1, date="2023-01-01", sets=3, reps=10, hold_sec=2, pain_0_10=5, rom_deg=120)
    assert sess.exercise_id == 1
    assert sess.date == "2023-01-01"
    assert sess.sets == 3
    assert sess.pain_0_10 == 5
```

---
## tests/test_sessions.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_session():
    # First, create an exercise
    ex_payload = {
        "name": "Quad Sets",
        "side": "right",
        "category": "strength",
        "target_sets": 2,
        "target_reps": 10,
        "target_hold_sec": 3,
        "schedule_dow": [2,4]
    }
    ex_res = client.post("/exercises", json=ex_payload)
    ex_id = ex_res.json()["id"]
    sess_payload = {
        "exercise_id": ex_id,
        "date": "2023-01-02",
        "sets": 2,
        "reps": 10,
        "hold_sec": 3,
        "pain_0_10": 4,
        "rom_deg": 110
    }
    response = client.post("/sessions", json=sess_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["exercise_id"] == ex_id
    assert data["date"] == "2023-01-02"
    assert data["pain_0_10"] == 4

def test_get_sessions():
    response = client.get("/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---
## tests/conftest.py
```python
import pytest
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)
```

---
## tests/test_day3_edgecases.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_exercise_missing_fields():
    payload = {"name": "", "side": "left", "category": "mobility"}
    response = client.post("/exercises", json=payload)
    assert response.status_code == 422

def test_create_session_invalid_exercise():
    payload = {"exercise_id": 999, "date": "2023-01-01"}
    response = client.post("/sessions", json=payload)
    assert response.status_code == 400
```

---
## tests/test_exercises_api.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_exercise_crud():
    payload = {
        "name": "Bridge",
        "side": "both",
        "category": "strength",
        "target_sets": 2,
        "target_reps": 10,
        "target_hold_sec": 5,
        "schedule_dow": [0,2,4]
    }
    # Create
    res = client.post("/exercises", json=payload)
    assert res.status_code == 200
    ex_id = res.json()["id"]
    # Get
    res = client.get(f"/exercises/{ex_id}")
    assert res.status_code == 200
    # Update
    update = {"name": "Bridge Updated"}
    res = client.put(f"/exercises/{ex_id}", json=update)
    assert res.status_code == 200
    assert res.json()["name"] == "Bridge Updated"
    # Delete
    res = client.delete(f"/exercises/{ex_id}")
    assert res.status_code == 204
```

---
## tests/test_sessions_api.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_session_crud():
    # Create exercise
    ex_payload = {
        "name": "Step Ups",
        "side": "right",
        "category": "mobility",
        "target_sets": 1,
        "target_reps": 8,
        "target_hold_sec": 2,
        "schedule_dow": [1,3]
    }
    ex_res = client.post("/exercises", json=ex_payload)
    ex_id = ex_res.json()["id"]
    # Create session
    sess_payload = {
        "exercise_id": ex_id,
        "date": "2023-01-03",
        "sets": 1,
        "reps": 8,
        "hold_sec": 2,
        "pain_0_10": 3,
        "rom_deg": 100
    }
    res = client.post("/sessions", json=sess_payload)
    assert res.status_code == 200
    sess_id = res.json()["id"]
    # Get
    res = client.get(f"/sessions/{sess_id}")
    assert res.status_code == 200
    # Update
    update = {"pain_0_10": 2}
    res = client.put(f"/sessions/{sess_id}", json=update)
    assert res.status_code == 200
    assert res.json()["pain_0_10"] == 2
    # Delete
    res = client.delete(f"/sessions/{sess_id}")
    assert res.status_code == 204
```

---
## tests/test_services_exercises.py
```python
from app.services import exercises
from app.schemas import ExerciseCreate
from app.models import Exercise
from sqlalchemy.orm import Session
import pytest

@pytest.fixture
def fake_db():
    class FakeDB:
        def __init__(self):
            self.items = {}
            self.next_id = 1
        def add(self, obj):
            obj.id = self.next_id
            self.items[obj.id] = obj
            self.next_id += 1
        def commit(self): pass
        def refresh(self, obj): pass
        def query(self, model):
            return list(self.items.values())
        def get(self, model, id):
            return self.items.get(id)
        def delete(self, obj):
            del self.items[obj.id]
    return FakeDB()

def test_create_exercise(fake_db):
    payload = ExerciseCreate(name="Test", side="left", category="mobility", target_sets=1, target_reps=10, target_hold_sec=2, schedule_dow=[1,2])
    out = exercises.create_exercise(fake_db, payload)
    assert out.name == "Test"
    assert out.side == "left"
    assert out.category == "mobility"

def test_list_exercises(fake_db):
    payload = ExerciseCreate(name="Test2", side="right", category="strength", target_sets=2, target_reps=8, target_hold_sec=3, schedule_dow=[3,4])
    exercises.create_exercise(fake_db, payload)
    result = exercises.list_exercises(fake_db)
    assert len(result) >= 1
```

---
## tests/test_services_sessions.py
```python
from app.services import sessions
from app.schemas import SessionCreate
from app.models import ExerciseSession
import pytest

@pytest.fixture
def fake_db():
    class FakeDB:
        def __init__(self):
            self.items = {}
            self.next_id = 1
        def add(self, obj):
            obj.id = self.next_id
            self.items[obj.id] = obj
            self.next_id += 1
        def commit(self): pass
        def refresh(self, obj): pass
        def query(self, model):
            return list(self.items.values())
        def get(self, model, id):
            return self.items.get(id)
        def delete(self, obj):
            del self.items[obj.id]
    return FakeDB()

def test_create_session(fake_db):
    # Simulate exercise exists
    fake_db.items[1] = object()
    payload = SessionCreate(exercise_id=1, date="2023-01-01", sets=1, reps=10, hold_sec=2, pain_0_10=5, rom_deg=120)
    out = sessions.create_session(fake_db, payload)
    assert out.exercise_id == 1
    assert out.date == "2023-01-01"

def test_list_sessions(fake_db):
    result = sessions.list_sessions(fake_db)
    assert isinstance(result, list)
```


---
## docker-compose.monitoring.yml
```yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: knee_rehab_app:local
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro

  grafana:
    image: grafana/grafana:9.5.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
      - app
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```


---
## docker-compose.yml
```yml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - .:/app:ro

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:

```

---
## Dockerfile
```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app

# Install build deps needed for some wheels (kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

EXPOSE 8000

# Run the FastAPI app with Uvicorn bound to all interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

---
## .github/workflows/cd.yml
```yml
name: CD Pipeline

on:
  push:
    branches: [ main, "fixing-cd" ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    env:
      PYTHONPATH: ${{ github.workspace }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dev dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

  build-and-push:
    name: Build and Push Image
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name != 'pull_request'

    permissions:
      contents: read
      packages: write

    outputs:
      image-tag: ${{ github.sha }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
    
      - name: Set image repo lower-case and Setup Docker Buildx
        run: |
          # make repository name lower-case for registry compatibility
          IMAGE_NAME_LC=$(echo "${{ github.repository }}" | tr '[:upper:]' '[:lower:]')
          echo "IMAGE_NAME_LC=$IMAGE_NAME_LC" >> $GITHUB_ENV

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }} # if GHCR write blocked, create PAT and store as GHCR_TOKEN

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_LC }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy to VM via SSH
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/fixing-cd'
    environment: production

    steps:
      - name: Deploy to VM via SSH
        uses: appleboy/ssh-action@v1.0.3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          host: ${{ vars.VM_HOST }}
          username: ${{ vars.VM_USERNAME }}
          key: ${{ secrets.VM_SSH_PRIVATE_KEY }}
          envs: REGISTRY,IMAGE_NAME,IMAGE_NAME_LC,GITHUB_TOKEN
          script: |
            set -euo pipefail

            # Ensure docker available; if docker needs sudo, uncomment next line:
            # SUDO="sudo"
            SUDO="sudo"

            # ensure image name is lowercase on the remote side (GHCR requires lowercase)
            IMAGE_NAME_LC=$(echo "${IMAGE_NAME}" | tr '[:upper:]' '[:lower:]')
            export IMAGE_NAME_LC

            echo "Logging in to GHCR"
            echo "$GITHUB_TOKEN" | ${SUDO} docker login ghcr.io -u "${{ github.actor }}" --password-stdin

            IMAGE="${REGISTRY}/${IMAGE_NAME_LC}:latest"
            echo "Pulling image $IMAGE"
            ${SUDO} docker pull "$IMAGE"

            echo "Stopping existing container (if any)"
            ${SUDO} docker stop kneerehab_app || true
            ${SUDO} docker rm kneerehab_app || true

            echo "Starting container"
            ${SUDO} docker run -d \
              --name kneerehab_app \
              --restart unless-stopped \
              -p 8000:8000 \
              -e APP_VERSION="${{ github.sha }}" \
              "$IMAGE"

            echo "Cleaning up dangling images"
            ${SUDO} docker image prune -f

            for i in $(seq 1 60); do
             if curl -sfS "http://${{ vars.VM_HOST }}:8000/health" >/dev/null 2>&1; then
               echo "App healthy after $i seconds"
               break
             fi
             sleep 1
            done

            if ! curl -sfS "http://${{ vars.VM_HOST }}:8000/health" >/dev/null 2>&1; then
             echo "Final health check failed"
             ${SUDO} docker logs kneerehab_app || true
             exit 1
            fi

            echo "Deployment Finished"

      - name: Deployment summary
        run: |
          echo "## Deployment Complete!" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Image:** \`${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest\`" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Application URL:** http://${{ vars.VM_HOST }}:8000" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### Endpoints" >> $GITHUB_STEP_SUMMARY
          echo "- Health: http://${{ vars.VM_HOST }}:8000/health" >> $GITHUB_STEP_SUMMARY
          echo "- Metrics: http://${{ vars.VM_HOST }}:8000/metrics" >> $GITHUB_STEP_SUMMARY
```

---
## .github/workflows/ci.yml
```yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    name: Test (pytest + coverage)
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          # Ensure TestClient dependency is available for FastAPI tests
          pip install httpx

      - name: Optional lint (ruff)
        run: |
          if command -v ruff >/dev/null 2>&1; then ruff check . || true; else echo "ruff not installed"; fi

      - name: Run tests with coverage
        run: |
          mkdir -p reports
          PYTHONPATH=. pytest --cov=app --cov-fail-under=70 --cov-report=xml --cov-report=html:htmlcov --junitxml=reports/junit.xml

      - name: Upload coverage.xml
        uses: actions/upload-artifact@v4
        with:
          name: coverage-xml
          path: coverage.xml

      - name: Upload coverage HTML
        uses: actions/upload-artifact@v4
        with:
          name: coverage-html
          path: htmlcov

      - name: Upload junit report
        uses: actions/upload-artifact@v4
        with:
          name: junit-report
          path: reports/junit.xml

  build-image:
    name: Build Docker image (verify)
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          docker build -t knee_rehab_app:ci .

  lint:
    name: Lint (ruff)
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install ruff
        run: |
          python -m pip install --upgrade pip
          pip install ruff

      - name: Run ruff
        run: |
          ruff check .

  smoke-test:
    name: Smoke tests (start app and check /health /metrics)
    runs-on: ubuntu-latest
    needs: [test]
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Start uvicorn in background
        run: |
          # start uvicorn and capture logs
          python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &> uvicorn.log &
          echo $! > uvicorn.pid

      - name: Wait for server and run checks
        run: |
          retries=20
          until curl -sS -f http://127.0.0.1:8000/health || [ $retries -le 0 ]; do
            retries=$((retries-1))
            echo "Waiting for app... retries left: $retries"
            sleep 1
          done
          if [ $retries -le 0 ]; then
            echo "App did not start in time"
            cat uvicorn.log || true
            exit 1
          fi

          echo "Health check OK"
          # Check metrics
          curl -sS -f http://127.0.0.1:8000/metrics | head -n 40

      - name: Stop uvicorn
        if: always()
        run: |
          PID=$(cat uvicorn.pid || true)
          if [ -n "$PID" ]; then kill $PID || true; fi
```

---
## requirements.txt
```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
SQLAlchemy==2.0.32
pydantic==2.8.2
python-multipart==0.0.9

pytest
pytest-cov

ruff==0.0.289
coverage==7.3.2
httpx
prometheus-client
```
