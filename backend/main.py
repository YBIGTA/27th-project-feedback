from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .initial_data import init_db

models.Base.metadata.create_all(bind=engine)
init_db()

from .api import students, feedbacks, feedback_details, auth, grades, teachers

app = FastAPI()

origins = [
    "https://jiy0-0nv.github.io",
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "null"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(grades.router)
app.include_router(students.router)
app.include_router(feedbacks.router)
app.include_router(feedback_details.router)
app.include_router(teachers.router)

@app.get("/")
def read_root():
    return {"message": "AI Feedback System API"}