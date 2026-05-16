.venv\Scripts\Activate.ps1

python create_admin.py

uvicorn main:app --reload --host 0.0.0.0 --port 8000