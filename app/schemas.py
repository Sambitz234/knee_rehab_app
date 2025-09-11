from typing import Optional, List, Literal
from pydantic import BaseModel, Field, conint
from datetime import date

Side = Literal["left", "right", "both"]
Category = Literal["strength", "mobility", "balance"]

class ExerciseBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    side: Side
    category: Category
    target_sets: Optional[int] = None
    target_reps: Optional[int] = None
    target_hold_sec: Optional[int] = None
    # 0=Sun, 1=Mon, ... 6=Sat (choose any convention; just be consistent)
    schedule_dow: List[int] = Field(default_factory=list)  # e.g. [1,3,5]

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
    pain_0_10: Optional[conint(ge=0, le=10)] = None
    rom_deg: Optional[conint(ge=0, le=180)] = None
    notes: Optional[str] = None

class SessionCreate(SessionBase):
    pass

class SessionOut(SessionBase):
    id: int
    class Config:
        from_attributes = True

class WeeklyAdherenceOut(BaseModel):
    week_start: date
    week_end: date
    scheduled_count: int
    completed_count: int
    adherence_pct: float

class ProgressPoint(BaseModel):
    date: date
    value: Optional[float] = None

class ProgressSeriesOut(BaseModel):
    metric: str
    points: List[ProgressPoint]
