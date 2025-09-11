from fastapi import FastAPI
from .database import Base, engine
from . import models
from .routers import exercises, sessions, stats

# Create tables on startup (simple dev approach)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knee Rehab Habit Tracker", version="0.1.0")

app.include_router(exercises.router)
app.include_router(sessions.router)
app.include_router(stats.router)

@app.get("/")
def root():
    return {"ok": True, "message": "See /docs for interactive API"}
