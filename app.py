# main Flask app
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    details = db.Column(db.Text)
    notes = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    completed_on = db.Column(db.Date)

    def days_taken(self):
        if self.completed_on:
            return (self.completed_on - self.start_date).days
        return None

    def is_overdue(self):
        return self.status != 'Completed' and date.today() > self.end_date

@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks, today=date.today())

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        task = Task(
            title=request.form['title'],
            details=request.form['details'],
            notes=request.form['notes'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            status=request.form['status']
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('task_form.html')

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get(task_id)
    task.status = 'Completed'
    task.completed_on = date.today()
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/export')
def export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Title', 'Details', 'Start', 'End', 'Status', 'Completed On', 'Days Taken', 'Spill Over'])

    for task in Task.query.all():
        days_taken = task.days_taken()
        spillover = (days_taken is not None and task.completed_on > task.end_date)
        writer.writerow([
            task.id, task.title, task.details, task.start_date,
            task.end_date, task.status, task.completed_on,
            days_taken, "Yes" if spillover else "No"
        ])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), download_name='tasks.csv', as_attachment=True)

# Add the reset route here
@app.route('/reset')
def reset_db():
    Task.query.delete()
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
