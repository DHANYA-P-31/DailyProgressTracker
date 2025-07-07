from flask import Flask, request, render_template_string, redirect, url_for, flash
from datetime import datetime, timedelta
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for flash messages

# SQLite database path (Windows-compatible)
DB_PATH = os.getenv('DB_PATH', r'C:\Users\Home\projects\Daily_tracker\tracker.db')

# Initialize SQLite database
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            day TEXT,
            task TEXT,
            target_hours REAL,
            time_spent REAL,
            completed TEXT,
            notes TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            task TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS schedule_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            task TEXT,
            target_hours REAL
        )''')
        conn.commit()

# Default weekly schedule
DEFAULT_SCHEDULE = {
    'Monday': [
        ('Problem-Solving', 1.5), ('Aptitude Practice', 1.0), ('Reading', 1.0),
        ('Udemy Course', 1.0), ('YouTube Lecture', 1.0), ('College Subjects', 2.0), ('Lab Work', 1.0)
    ],
    'Tuesday': [
        ('Problem-Solving', 1.5), ('Aptitude Practice', 1.0), ('Reading', 1.0),
        ('Udemy Course', 1.0), ('YouTube Lecture', 1.0), ('College Subjects', 2.0), ('Lab Work', 1.0)
    ],
    'Wednesday': [
        ('Problem-Solving', 1.5), ('Aptitude Practice', 1.0), ('Reading', 1.0),
        ('Udemy Course', 1.0), ('YouTube Lecture', 1.0), ('College Subjects', 2.0), ('Lab Work', 1.0)
    ],
    'Thursday': [
        ('Problem-Solving', 1.5), ('Aptitude Practice', 1.0), ('Reading', 1.0),
        ('Udemy Course', 1.0), ('YouTube Lecture', 1.0), ('College Subjects', 2.0), ('Lab Work', 1.0)
    ],
    'Friday': [
        ('Problem-Solving', 1.5), ('Aptitude Practice', 1.0), ('Reading', 1.0),
        ('Udemy Course', 1.0), ('YouTube Lecture', 1.0), ('College Subjects', 2.0), ('Lab Work', 1.0)
    ],
    'Saturday': [
        ('Problem-Solving', 2.0), ('Aptitude Practice', 1.0), ('Reading', 1.0),
        ('Udemy Course', 1.0), ('YouTube Lecture', 1.0), ('College Subjects', 2.0), ('Lab Work', 1.0)
    ],
    'Sunday': [
        ('Review/Problem-Solving', 1.0), ('College Subjects', 1.0), ('Reading', 0.5)
    ]
}

# Populate schedule template in DB if empty
def populate_default_schedule():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM schedule_template')
        if c.fetchone()[0] == 0:
            for day, tasks in DEFAULT_SCHEDULE.items():
                for task, hours in tasks:
                    c.execute('INSERT INTO schedule_template (day, task, target_hours) VALUES (?, ?, ?)',
                              (day, task, hours))
            conn.commit()

# HTML template with Bootstrap 5 and updated date format
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Placement Progress Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        body { background-color: #f8f9fa; }
        .navbar-brand { font-weight: bold; }
        .sidebar { height: 100vh; position: fixed; top: 0; left: 0; z-index: 1000; }
        .main-content { margin-left: 250px; }
        @media (max-width: 767.98px) {
            .sidebar { position: relative; height: auto; }
            .main-content { margin-left: 0; }
        }
        .toast { min-width: 200px; }
        .form-control.date-input { max-width: 200px; }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-md navbar-dark bg-primary sidebar">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Tracker</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showSection('dashboard')" id="nav-dashboard">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showSection('schedule')" id="nav-schedule">Manage Schedule</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showSection('progress')" id="nav-progress">Daily Progress</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showSection('report')" id="nav-report">Weekly Report</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showSection('reminders')" id="nav-reminders">Reminders</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Toast for Success and Errors -->
    <div class="toast-container position-fixed top-0 end-0 p-3">
        <div id="successToast" class="toast bg-success text-white" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-body"></div>
        </div>
        <div id="errorToast" class="toast bg-danger text-white" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-body">
                {% with messages = get_flashed_messages() %}
                {% if messages %}
                {% for message in messages %}
                <p>{{ message }}</p>
                {% endfor %}
                {% endif %}
                {% endwith %}
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <main class="main-content p-4">
        <!-- Dashboard Section -->
        <section id="dashboard" class="section">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h2 class="h4 mb-0">Dashboard</h2>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <div class="card h-100">
                                <div class="card-body">
                                    <h3 class="h5">Weekly Progress</h3>
                                    {% if report %}
                                    <p><strong>Total Tasks:</strong> {{ report.total_tasks }}</p>
                                    <p><strong>Completed:</strong> {{ report.completed_tasks }}</p>
                                    <p><strong>Uncompleted:</strong> {{ report.uncompleted_tasks }}</p>
                                    <p><strong>Completion Rate:</strong> {{ report.completion_rate }}%</p>
                                    {% else %}
                                    <p class="text-muted">Generate a weekly report to see progress.</p>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <div class="card h-100">
                                <div class="card-body">
                                    <h3 class="h5">Recent Reminders</h3>
                                    {% if reminders %}
                                    <ul class="list-group list-group-flush">
                                        {% for reminder in reminders %}
                                        {% if loop.index <= 5 %}
                                        <li class="list-group-item">{{ reminder.display_date }}: {{ reminder.task }}</li>
                                        {% endif %}
                                        {% endfor %}
                                    </ul>
                                    {% else %}
                                    <p class="text-muted">No reminders yet.</p>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                    <button class="btn btn-primary mt-3" onclick="showSection('progress')">Update Today's Progress</button>
                </div>
            </div>
        </section>

        <!-- Manage Schedule Section -->
        <section id="schedule" class="section d-none">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h2 class="h4 mb-0">Manage Schedule Template</h2>
                </div>
                <div class="card-body">
                    <div class="d-flex flex-column flex-md-row gap-2 mb-3">
                        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addTaskModal">Add Task</button>
                        <button class="btn btn-warning" data-bs-toggle="modal" data-bs-target="#renameTaskModal">Rename Task</button>
                        <button class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#deleteTaskModal">Delete Task</button>
                    </div>
                    <h3 class="h5">Current Schedule Template</h3>
                    {% for day in days %}
                    <div class="mt-2">
                        <h4 class="h6">{{ day }}</h4>
                        <ul class="list-group list-group-flush">
                            {% for task in schedule_tasks if task.day == day %}
                            <li class="list-group-item">{{ task.task }} ({{ task.target_hours }}h)</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endfor %}
                    <div class="mt-4">
                        <h3 class="h5">Generate Weekly Schedule</h3>
                        <div class="d-flex flex-column flex-md-row gap-2 align-items-md-center mt-2">
                            <input type="text" id="start_date" name="start_date" class="form-control date-input" 
                                   placeholder="DD-MM-YYYY" pattern="\d{2}-\d{2}-\d{4}" required>
                            <button class="btn btn-secondary" onclick="setTodayDate()">Set Today</button>
                            <button class="btn btn-primary" onclick="validateAndSubmit('add_schedule_form', 'start_date')">Generate</button>
                        </div>
                        <form id="add_schedule_form" method="POST" action="/add_schedule" class="d-none">
                            <input type="hidden" name="start_date" id="start_date_hidden">
                        </form>
                    </div>
                </div>
            </div>
        </section>

        <!-- Add Task Modal -->
        <div class="modal fade" id="addTaskModal" tabindex="-1" aria-labelledby="addTaskModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addTaskModalLabel">Add Task</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form method="POST" action="/add_task" onsubmit="showSuccessToast('Task added successfully!')">
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Day</label>
                                <select name="day" class="form-select" required>
                                    {% for day in days %}
                                    <option value="{{ day }}">{{ day }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Task Name</label>
                                <input type="text" name="task" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Target Hours</label>
                                <input type="number" step="0.1" name="target_hours" class="form-control" required min="0.1">
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Add Task</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Rename Task Modal -->
        <div class="modal fade" id="renameTaskModal" tabindex="-1" aria-labelledby="renameTaskModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="renameTaskModalLabel">Rename Task</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form method="POST" action="/rename_task" onsubmit="showSuccessToast('Task renamed successfully!')">
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Current Task</label>
                                <select name="task_id" class="form-select" required>
                                    {% for task in schedule_tasks %}
                                    <option value="{{ task.id }}">{{ task.day }}: {{ task.task }} ({{ task.target_hours }}h)</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">New Task Name</label>
                                <input type="text" name="new_task" class="form-control" required>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-warning">Rename Task</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Delete Task Modal -->
        <div class="modal fade" id="deleteTaskModal" tabindex="-1" aria-labelledby="deleteTaskModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="deleteTaskModalLabel">Delete Task</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form method="POST" action="/delete_task" onsubmit="showSuccessToast('Task deleted successfully!')">
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Task</label>
                                <select name="task_id" class="form-select" required>
                                    {% for task in schedule_tasks %}
                                    <option value="{{ task.id }}">{{ task.day }}: {{ task.task }} ({{ task.target_hours }}h)</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-danger">Delete Task</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Daily Progress Section -->
        <section id="progress" class="section d-none">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h2 class="h4 mb-0">Daily Progress</h2>
                </div>
                <div class="card-body">
                    <form method="POST" action="/update_task" onsubmit="showSuccessToast('Tasks updated successfully!')">
                        <div class="table-responsive">
                            <table class="table table-striped table-bordered">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Day</th>
                                        <th>Task</th>
                                        <th>Target Hours</th>
                                        <th>Time Spent</th>
                                        <th>Completed</th>
                                        <th>Notes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for task in tasks %}
                                    <tr>
                                        <td>{{ task.display_date }}</td>
                                        <td>{{ task.day }}</td>
                                        <td>{{ task.task }}</td>
                                        <td>{{ task.target_hours }}</td>
                                        <td>
                                            <input type="number" step="0.1" name="time_spent_{{ task.id }}"
                                                   value="{{ task.time_spent or '' }}"
                                                   class="form-control" min="0">
                                        </td>
                                        <td>
                                            <select name="completed_{{ task.id }}" class="form-select">
                                                <option value="Y" {% if task.completed == 'Y' %}selected{% endif %}>Yes</option>
                                                <option value="N" {% if task.completed == 'N' %}selected{% endif %}>No</option>
                                            </select>
                                        </td>
                                        <td>
                                            <input type="text" name="notes_{{ task.id }}" value="{{ task.notes or '' }}"
                                                   class="form-control">
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        <button type="submit" class="btn btn-success mt-3">Update Tasks</button>
                    </form>
                </div>
            </div>
        </section>

        <!-- Weekly Report Section -->
        <section id="report" class="section d-none">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h2 class="h4 mb-0">Weekly Report</h2>
                </div>
                <div class="card-body">
                    <div class="d-flex flex-column flex-md-row gap-2 align-items-md-center">
                        <input type="text" id="report_start_date" name="report_start_date"
                               class="form-control date-input" placeholder="DD-MM-YYYY" 
                               pattern="\d{2}-\d{2}-\d{4}" required>
                        <button class="btn btn-primary" onclick="validateAndSubmit('report_form', 'report_start_date')">Generate Report</button>
                    </div>
                    <form id="report_form" method="POST" action="/weekly_report" class="d-none">
                        <input type="hidden" name="report_start_date" id="report_start_date_hidden">
                    </form>
                    {% if report %}
                    <div class="card mt-3">
                        <div class="card-body">
                            <h3 class="h5">Report for {{ report.display_start_date }} to {{ report.display_end_date }}</h3>
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Total Tasks:</strong> {{ report.total_tasks }}</p>
                                    <p><strong>Completed Tasks:</strong> {{ report.completed_tasks }}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Uncompleted Tasks:</strong> {{ report.uncompleted_tasks }}</p>
                                    <p><strong>Completion Rate:</strong> {{ report.completion_rate }}%</p>
                                </div>
                            </div>
                            {% if report.uncompleted_list %}
                            <h4 class="h6 mt-3">Uncompleted Tasks:</h4>
                            <ul class="list-group list-group-flush">
                                {% for task in report.uncompleted_list %}
                                <li class="list-group-item">{{ task.display_date }}: {{ task.task }}</li>
                                {% endfor %}
                            </ul>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </section>

        <!-- Reminders Section -->
        <section id="reminders" class="section d-none">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h2 class="h4 mb-0">Daily Reminders (10:00 AM)</h2>
                </div>
                <div class="card-body">
                    <p class="text-muted">Uncompleted tasks from the previous day are listed here.</p>
                    {% if reminders %}
                    <ul class="list-group list-group-flush">
                        {% for reminder in reminders %}
                        <li class="list-group-item">{{ reminder.display_date }}: {{ reminder.task }}</li>
                        {% endfor %}
                    </ul>
                    {% else %}
                    <p class="text-muted">No reminders for today.</p>
                    {% endif %}
                </div>
            </div>
        </section>
    </main>

    <footer class="bg-primary text-white text-center py-3">
        <p>Placement Progress Tracker © 2025</p>
    </footer>

    <script>
        function showSection(sectionId) {
            document.querySelectorAll('.section').forEach(section => {
                section.classList.add('d-none');
            });
            document.getElementById(sectionId).classList.remove('d-none');
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            document.getElementById(`nav-${sectionId}`).classList.add('active');
        }

        function setTodayDate() {
            const today = new Date();
            const dd = String(today.getDate()).padStart(2, '0');
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const yyyy = today.getFullYear();
            const todayStr = `${dd}-${mm}-${yyyy}`;
            document.getElementById('start_date').value = todayStr;
            document.getElementById('report_start_date').value = todayStr;
        }

        function validateAndSubmit(formId, inputId) {
            const input = document.getElementById(inputId);
            const form = document.getElementById(formId);
            const datePattern = /^\d{2}-\d{2}-\d{4}$/;
            if (!input.value) {
                showErrorToast('Please enter a date.');
                return;
            }
            if (!datePattern.test(input.value)) {
                showErrorToast('Invalid date format. Use DD-MM-YYYY.');
                return;
            }
            // Convert DD-MM-YYYY to YYYY-MM-DD
            const parts = input.value.split('-');
            const convertedDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
            document.getElementById(inputId + '_hidden').value = convertedDate;
            form.submit();
        }

        function showSuccessToast(message) {
            const toast = new bootstrap.Toast(document.getElementById('successToast'));
            document.getElementById('successToast').querySelector('.toast-body').textContent = message;
            toast.show();
        }

        function showErrorToast(message) {
            const toast = new bootstrap.Toast(document.getElementById('errorToast'));
            document.getElementById('errorToast').querySelector('.toast-body').textContent = message;
            toast.show();
        }

        // Show dashboard by default
        document.addEventListener('DOMContentLoaded', () => {
            showSection('dashboard');
            // Show error toast if flash messages exist
            {% with messages = get_flashed_messages() %}
            {% if messages %}
            showErrorToast('');
            {% endif %}
            {% endwith %}
        });
    </script>
</body>
</html>
'''

# Initialize database and populate default schedule
init_db()
populate_default_schedule()

# Routes
@app.route('/')
def index():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM tasks ORDER BY date')
        tasks = [{'id': row[0], 'date': row[1], 'day': row[2], 'task': row[3],
                  'target_hours': row[4], 'time_spent': row[5], 'completed': row[6], 'notes': row[7],
                  'display_date': datetime.strptime(row[1], '%Y-%m-%d').strftime('%d %b %Y') if row[1] else ''}
                 for row in c.fetchall()]
        c.execute('SELECT * FROM reminders ORDER BY date')
        reminders = [{'date': row[1], 'task': row[2],
                      'display_date': datetime.strptime(row[1], '%Y-%m-%d').strftime('%d %b %Y') if row[1] else ''}
                     for row in c.fetchall()]
        c.execute('SELECT * FROM schedule_template ORDER BY day')
        schedule_tasks = [{'id': row[0], 'day': row[1], 'task': row[2], 'target_hours': row[3]}
                          for row in c.fetchall()]
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Generate a default report for the dashboard (current week)
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
        c.execute('SELECT * FROM tasks WHERE date BETWEEN ? AND ? ORDER BY date', (start_date, end_date))
        report_tasks = [{'date': row[1], 'task': row[3], 'completed': row[6],
                         'display_date': datetime.strptime(row[1], '%Y-%m-%d').strftime('%d %b %Y') if row[1] else ''}
                        for row in c.fetchall()]
        total_tasks = len(report_tasks)
        completed_tasks = sum(1 for task in report_tasks if task['completed'] == 'Y')
        uncompleted_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        uncompleted_list = [task for task in report_tasks if task['completed'] == 'N']
        report = {
            'start_date': start_date,
            'display_start_date': datetime.strptime(start_date, '%Y-%m-%d').strftime('%d %b %Y'),
            'end_date': end_date,
            'display_end_date': datetime.strptime(end_date, '%Y-%m-%d').strftime('%d %b %Y'),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'uncompleted_tasks': uncompleted_tasks,
            'completion_rate': round(completion_rate, 2),
            'uncompleted_list': uncompleted_list
        }
        
    return render_template_string(HTML_TEMPLATE, tasks=tasks, reminders=reminders,
                                 schedule_tasks=schedule_tasks, days=days, report=report)

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    start_date = request.form.get('start_date')
    if not start_date:
        flash('Please enter a start date.')
        return redirect(url_for('index'))
    try:
        # Try DD-MM-YYYY first, then YYYY-MM-DD
        try:
            start_date = datetime.strptime(start_date, '%d-%m-%Y').strftime('%Y-%m-%d')
        except ValueError:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format. Use DD-MM-YYYY.')
        return redirect(url_for('index'))

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM schedule_template')
        schedule_tasks = [{'day': row[1], 'task': row[2], 'target_hours': row[3]} for row in c.fetchall()]
        for i in range(7):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            day = (start_date + timedelta(days=i)).strftime('%A')
            for task in schedule_tasks:
                if task['day'] == day:
                    c.execute('INSERT INTO tasks (date, day, task, target_hours, completed) VALUES (?, ?, ?, ?, ?)',
                              (date, day, task['task'], task['target_hours'], 'N'))
        conn.commit()
    flash('Weekly schedule generated successfully!')
    return redirect(url_for('index'))

@app.route('/update_task', methods=['POST'])
def update_task():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        for key, value in request.form.items():
            if key.startswith('time_spent_'):
                task_id = key.split('_')[2]
                try:
                    value = float(value) if value else None
                except ValueError:
                    continue
                c.execute('UPDATE tasks SET time_spent = ? WHERE id = ?', (value, task_id))
            elif key.startswith('completed_'):
                task_id = key.split('_')[1]
                c.execute('UPDATE tasks SET completed = ? WHERE id = ?', (value, task_id))
            elif key.startswith('notes_'):
                task_id = key.split('_')[1]
                c.execute('UPDATE tasks SET notes = ? WHERE id = ?', (value, task_id))
        conn.commit()
    flash('Tasks updated successfully!')
    return redirect(url_for('index'))

@app.route('/weekly_report', methods=['POST'])
def weekly_report():
    start_date = request.form.get('report_start_date')
    if not start_date:
        flash('Please enter a start date.')
        return redirect(url_for('index'))
    try:
        # Try DD-MM-YYYY first, then YYYY-MM-DD
        try:
            start_date = datetime.strptime(start_date, '%d-%m-%Y').strftime('%Y-%m-%d')
        except ValueError:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = (start_date + timedelta(days=6)).strftime('%Y-%m-%d')
    except ValueError:
        flash('Invalid date format. Use DD-MM-YYYY.')
        return redirect(url_for('index'))

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM tasks WHERE date BETWEEN ? AND ? ORDER BY date',
                  (start_date.strftime('%Y-%m-%d'), end_date))
        tasks = [{'date': row[1], 'task': row[3], 'completed': row[6],
                  'display_date': datetime.strptime(row[1], '%Y-%m-%d').strftime('%d %b %Y') if row[1] else ''}
                 for row in c.fetchall()]
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task['completed'] == 'Y')
        uncompleted_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        uncompleted_list = [task for task in tasks if task['completed'] == 'N']
        
        report = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'display_start_date': start_date.strftime('%d %b %Y'),
            'end_date': end_date,
            'display_end_date': datetime.strptime(end_date, '%Y-%m-%d').strftime('%d %b %Y'),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'uncompleted_tasks': uncompleted_tasks,
            'completion_rate': round(completion_rate, 2),
            'uncompleted_list': uncompleted_list
        }
        
        c.execute('SELECT * FROM tasks ORDER BY date')
        tasks = [{'id': row[0], 'date': row[1], 'day': row[2], 'task': row[3],
                  'target_hours': row[4], 'time_spent': row[5], 'completed': row[6], 'notes': row[7],
                  'display_date': datetime.strptime(row[1], '%Y-%m-%d').strftime('%d %b %Y') if row[1] else ''}
                 for row in c.fetchall()]
        c.execute('SELECT * FROM reminders ORDER BY date')
        reminders = [{'date': row[1], 'task': row[2],
                      'display_date': datetime.strptime(row[1], '%Y-%m-%d').strftime('%d %b %Y') if row[1] else ''}
                     for row in c.fetchall()]
        c.execute('SELECT * FROM schedule_template ORDER BY day')
        schedule_tasks = [{'id': row[0], 'day': row[1], 'task': row[2], 'target_hours': row[3]}
                          for row in c.fetchall()]
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
    flash('Weekly report generated successfully!')
    return render_template_string(HTML_TEMPLATE, tasks=tasks, report=report, reminders=reminders,
                                 schedule_tasks=schedule_tasks, days=days)

@app.route('/add_task', methods=['POST'])
def add_task():
    day = request.form.get('day')
    task = request.form.get('task')
    target_hours = request.form.get('target_hours')
    if not day or not task or not target_hours:
        flash('All fields are required.')
        return redirect(url_for('index'))
    try:
        target_hours = float(target_hours)
        if target_hours <= 0:
            raise ValueError
    except ValueError:
        flash('Target hours must be a positive number.')
        return redirect(url_for('index'))
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO schedule_template (day, task, target_hours) VALUES (?, ?, ?)',
                  (day, task, target_hours))
        conn.commit()
    flash('Task added successfully!')
    return redirect(url_for('index'))

@app.route('/rename_task', methods=['POST'])
def rename_task():
    task_id = request.form.get('task_id')
    new_task = request.form.get('new_task')
    if not task_id or not new_task.strip():
        flash('Task selection and new name are required.')
        return redirect(url_for('index'))
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('UPDATE schedule_template SET task = ? WHERE id = ?', (new_task, task_id))
        conn.commit()
    flash('Task renamed successfully!')
    return redirect(url_for('index'))

@app.route('/delete_task', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id')
    if not task_id:
        flash('Please select a task to delete.')
        return redirect(url_for('index'))
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM schedule_template WHERE id = ?', (task_id,))
        conn.commit()
    flash('Task deleted successfully!')
    return redirect(url_for('index'))

def check_reminders():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        c.execute('SELECT date, task FROM tasks WHERE date = ? AND completed = ?', (yesterday, 'N'))
        uncompleted_tasks = c.fetchall()
        for date, task in uncompleted_tasks:
            c.execute('INSERT INTO reminders (date, task) VALUES (?, ?)', (yesterday, task))
        conn.commit()

# Schedule daily reminder at 10:00 AM IST
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'cron', hour=10, minute=0, timezone='Asia/Kolkata')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)