Backend Django server for AGRO AI

Quick start (Windows PowerShell):

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run migrations and populate diseases (creates 2000 placeholder diseases):

```powershell
python manage.py migrate
python manage.py populate_diseases
```

4. Run the dev server:

```powershell
python manage.py runserver
```

API endpoints:
- `POST /api/predict/` accepts form-data `image` file and returns JSON with `is_plant`, `is_healthy`, `disease` and `confidence`.
- `GET /api/diseases/` lists diseases in the DB.

Note: This backend includes a placeholder classifier in `api/classifier.py`. Replace with your trained model or a proper inference pipeline for accurate results.
