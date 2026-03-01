# main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models import Task, TaskCreate
from database import SessionLocal, engine, Base
from utils import calculate_duration, calculate_spillover, export_tasks_to_csv
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def index(request: Request):
    db = next(get_db())
    tasks = db.query(Task).all()
    for task in tasks:
        task.duration = calculate_duration(task)
        task.spillover = calculate_spillover(task)
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})

@app.post("/add")
def add_task(request: Request, title: str = Form(...), notes: str = Form(""), start_date: str = Form(...), end_date: str = Form(...)):
    db = next(get_db())
    task = Task(title=title, notes=notes, start_date=start_date, end_date=end_date, status="Pending")
    db.add(task)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/complete/{task_id}")
def complete_task(task_id: int):
    db = next(get_db())
    task = db.query(Task).get(task_id)
    if task:
        task.status = "Completed"
        task.completed_date = datetime.now().date()
        db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/export")
def export():
    db = next(get_db())
    tasks = db.query(Task).all()
    path = export_tasks_to_csv(tasks)
    return FileResponse(path, media_type='text/csv', filename='tasks_export.csv')
