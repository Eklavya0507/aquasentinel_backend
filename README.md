# AquaSentinel Backend

Production-oriented starter backend for the AquaSentinel SIH project.

## Included

- FastAPI REST API
- PostgreSQL-ready SQLAlchemy database
- JWT authentication
- Roles: `USER`, `DOCTOR`, `GOVERNMENT`, `ADMIN`
- User/family profiles
- Primary + current residence
- Preferred languages
- Previous disease history
- Medical document upload
- Doctor profiles, languages, hospitals and schedules
- Government official profiles
- Hospital locations, hours, schedule exceptions and specialists
- Doctor recommendation scoring
- Doctor reviews + language feedback
- Community concern reports
- Verified-case workflow
- Regional alerts
- Model A prediction endpoint
- Model B prediction/snapshot endpoint
- Model files are **not faked**: missing models return HTTP 503
- API docs at `/docs`

## 1. Setup

```powershell
cd aquasentinel_backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a strong `SECRET_KEY`.

## 2. Start PostgreSQL

If Docker Desktop is installed:

```powershell
docker compose up -d
```

Or use your own PostgreSQL instance and change `DATABASE_URL`.

For a quick local test without PostgreSQL, set:

```env
DATABASE_URL=sqlite:///./aquasentinel.db
```

## 3. Run

```powershell
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

## 4. First admin account

Register a normal account using `/api/auth/register`, then run:

```powershell
python scripts/promote_admin.py your-email@example.com
```

## 5. AI model files

Put validated files under `app/ml/`, for example:

```text
app/ml/model_a.pkl
app/ml/model_a_label_encoder.pkl
app/ml/model_a_features.pkl
app/ml/model_b.pkl
app/ml/model_b_features.pkl
```

Then update `.env`:

```env
MODEL_A_PATH=app/ml/model_a.pkl
MODEL_A_LABEL_ENCODER_PATH=app/ml/model_a_label_encoder.pkl
MODEL_A_FEATURES_PATH=app/ml/model_a_features.pkl

MODEL_B_PATH=app/ml/model_b.pkl
MODEL_B_FEATURES_PATH=app/ml/model_b_features.pkl
```

The prediction endpoints deliberately return `503 Model not configured` until a model is actually present.

## Important integration rule

The frontend should not calculate fake AI scores. It should call these backend endpoints.

Model A:

```http
POST /api/ai/model-a/predict
```

Model B:

```http
POST /api/ai/model-b/predict
```

## Core API groups

```text
/api/auth
/api/profiles
/api/doctors
/api/hospitals
/api/reviews
/api/cases
/api/reports
/api/alerts
/api/ai
```

## Notes for SIH prototype

This starter uses `Base.metadata.create_all()` for fast development. Before a real production deployment, add Alembic migrations, managed object storage for medical files, rate limiting, stronger audit/event logging, secrets management, encryption policies, and legal/privacy review for health information.
