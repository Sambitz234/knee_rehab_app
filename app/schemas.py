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
