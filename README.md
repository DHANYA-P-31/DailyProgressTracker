# Daily Progress Tracker

A Flask-based web application for placement preparation, tracking daily tasks, generating weekly schedules, updating progress, viewing weekly reports, and receiving daily reminders at 10:00 AM IST.

## Features
- **Dashboard**: View weekly progress and recent reminders.
- **Manage Schedule**: Add, rename, or delete tasks; generate weekly schedules.
- **Daily Progress**: Update task completion, time spent, and notes.
- **Weekly Report**: Generate reports with completion statistics.
- **Reminders**: Uncompleted tasks from the previous day at 10:00 AM IST.
- **Date Format**: Input as `DD-MM-YYYY` (e.g., `07-07-2025`); display as `DD MMM YYYY` (e.g., `07 Jul 2025`).
- **UI**: Responsive Bootstrap 5 interface with sidebar, modals, and toasts.

## Prerequisites
- Python 3.10.14
- Git
- A modern web browser

## Local Setup (Windows)
1. Clone the repository:
   ```bash
   git clone https://github.com/DHANYA-P-31/DailyProgressTracker.git
   cd DailyProgressTracker
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the app:
   - flask Server
   ```bash
   python tracker.py
   ```
   - Waitress
   ```bash
   waitress-serve --port=8000 tracker:app
   ```
6. Access at http://127.0.0.1:5000 (Flask) or http://127.0.0.1:8000 (Waitress).