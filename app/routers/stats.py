from fastapi import APIRouter
from ..database import get_db

router = APIRouter(prefix="/stats", tags=["stats"])

# Note: This router is kept for potential future stats endpoints
# Current stats are handled directly in the frontend using /exercises and /sessions data
