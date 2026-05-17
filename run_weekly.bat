@echo off
cd C:\Users\HP\Downloads\github-candidate-agent\github-candidate-agent
call venv\Scripts\activate
python main.py >> logs\weekly_run.log 2>&1