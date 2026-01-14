@echo off
start http://localhost:8000
cd backend
call ..\venv\Scripts\activate.bat
python manage.py runserver