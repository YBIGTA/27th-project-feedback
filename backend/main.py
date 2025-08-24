from fastapi import FastAPI
from .api import students, feedbacks, feedback_details, auth 

app = FastAPI()

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(feedbacks.router)
app.include_router(feedback_details.router)

@app.get("/")
def read_root():
    return {"message": "AI Feedback System API"}