# AquaSentinel Backend — SIH Connected Prototype

A compact FastAPI backend designed for a **college-level SIH working prototype**. It intentionally avoids enterprise-only complexity and focuses on the flows visible in the AquaSentinel frontend.

## Connected flows
- Citizen register/login with JWT
- Citizen and family profiles
- Medical history
- Doctor and government register/login
- Public community concern submission
- Government community-report review (`UNDER_REVIEW`, `VERIFIED`, `REJECTED`)
- Doctor/government case entry
- B2-style surveillance: recent 7 days vs previous 4-week weekly average
- Public alert/surveillance endpoints
- Uploaded B1 environmental XGBoost model prediction
- Demo hospital directory and doctor directory

## Important architecture choice
The uploaded B1 model uses environmental, water, sanitation, demographic and seasonal inputs. It is **not** a symptom diagnosis model. The website therefore uses it on the Environmental Risk page and does not show a fake symptom diagnosis in AI Lab.

The old notebook B2 logic is intentionally not used because it treated the whole historical dataset as current data and used an arbitrary population formula. This backend uses simple case surveillance instead.

## Run on Windows PowerShell
```powershell
cd AquaSentinel-Backend-SIH-Complete
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Open:
- API health: `http://127.0.0.1:8000/api/health`
- Swagger: `http://127.0.0.1:8000/docs`

## Fresh database
If you previously ran another AquaSentinel schema, delete the old local SQLite file before first run:
```powershell
Remove-Item aquasentinel.db -ErrorAction SilentlyContinue
```
The tables are recreated automatically for the SIH demo.

## Demo limitation
Doctor/government registrations are recorded as `PENDING`, while role-gated demo screens remain usable so the team can demonstrate the workflow without building a full government verification authority. Do not describe these demo entries as officially verified public-health data.

## Before public deployment
Change `SECRET_KEY`, deploy the backend over HTTPS, update the frontend API base URL, and use a persistent database/storage service.
