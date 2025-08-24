from fastapi import FastAPI

from . import models
from .database import engine
from .initial_data import init_db

models.Base.metadata.create_all(bind=engine)
init_db()

from .api import students, feedbacks, feedback_details, auth, grades

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(grades.router)
app.include_router(students.router)
app.include_router(feedbacks.router)
app.include_router(feedback_details.router)

@app.get("/")
def read_root():
    return {"message": "AI Feedback System API"}