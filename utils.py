from datetime import datetime
import csv

def calculate_duration(task):
    if task.completed_date:
        return (task.completed_date - task.start_date).days
    return (datetime.now().date() - task.start_date).days

def calculate_spillover(task):
    if task.completed_date and task.completed_date > task.end_date:
        return (task.completed_date - task.end_date).days
    return 0

def export_tasks_to_csv(tasks):
    filename = "tasks_export.csv"
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Task", "Notes", "Start Date", "End Date", "Completed Date", "Status", "Duration", "Spillover"])
        for t in tasks:
            duration = calculate_duration(t)
            spillover = calculate_spillover(t)
            writer.writerow([t.title, t.notes, t.start_date, t.end_date, t.completed_date, t.status, duration, spillover])
    return filename
