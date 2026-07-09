@echo off
echo Starting AI Medical Consultant Backend...
call "%~dp0.venv\Scripts\activate.bat"
python -m uvicorn main:app --reload --port 8000
pause
