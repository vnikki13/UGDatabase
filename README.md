# Ultrasound Guidance Database
This codebase includes the postgres database, api endpoints and admin portal for Ultrasound Guidance.

## Local Development

### Postgres
- Change POSTGRES_SERVER to "localhost"
- Clear CLOUD_SQL_CONNECTION_NAME so the backend uses TCP instead of the Cloud SQL socket path
- Use local database credentials instead of the Cloud Run secret-backed values

### Docker
- Build images with `docker compose up --build -d`

## Run API endpoints
- Ensure you're in the `backend` folder
- Run `gcloud auth application-default login`
- Run `fastapi dev app/main.py`

## Run Admin Portal
- Ensure you're in the `admin-portal` folder
- Run `npm run dev`

## Run Tests
- Ensure you're in the `backend` folder
- Activate the backend virtual environment: `source .venv/bin/activate`
- Run tests with the active interpreter: `python -m pytest tests/ -v`
- Run a single test file: `python -m pytest tests/test_audit_questions.py -v`

Using `python -m pytest` ensures tests run with the selected environment and avoids import path issues.

## Migrations
- Ensure you're in the `backend` folder
- Make changes to the models
- Run `alembic revision --autogenerate -m "<Migration message>"`
- Confirm migration file looks correct
- Run `alembic upgrade head`
- Confirm migration changes are correct
- Use `alembic downgrade -1` (where `-1` is the number of versions) to downgrade

## Prod updates
- The admin portal and api endpoints are hosted on Google Cloud Run
- The backend now uses private IP to reach Cloud SQL through the `backend-connector` Serverless VPC connector
- Sensitive credentials are stored in Secret Manager: `backend-postgres-password` (DB password) and `backend-ghost-admin-key` (Ghost admin key)
- Deploy the backend from the `backend` folder with `bash scripts/deploy-cloud-run.sh`
- Optional env var overrides when deploying: `GCS_BUCKET_NAME`, `GCS_PROJECT_ID`, `GHOST_URL`, `ALLOWED_ORIGINS`, `DEBUG`, or `GHOST_ADMIN_KEY_SECRET` (if using a different secret name)
- The deploy script now passes runtime config explicitly, so Cloud Run no longer depends on a packaged `.env` file
- The database is hosted on Google Cloud SQL
- Run upgrades and downgrades through a path that has private access to the instance

## Cloud Run Deployment

### Backend deploy
- Ensure you are in the `backend` folder
- Deploy with:

```bash
bash scripts/deploy-cloud-run.sh
```

- To allow a deployed frontend origin (CORS), pass `ADMIN_PORTAL_ORIGIN`:

```bash
ADMIN_PORTAL_ORIGIN=https://admin-portal-<hash>-<region>.run.app bash scripts/deploy-cloud-run.sh
```

- Useful backend overrides:

```bash
PROJECT_ID=ultrasound-guidance \
REGION=us-east1 \
SERVICE_NAME=backend \
ALLOWED_ORIGINS=https://admin-portal-<hash>-<region>.run.app,http://localhost:5173 \
bash scripts/deploy-cloud-run.sh
```

### Admin portal deploy
- Ensure you are in the repo root or `admin-portal` folder
- The admin portal deploy script requires both build-time variables:
	- `VITE_API_URL` (must include `/api/v1`)
	- `VITE_GCS_CLIENT_ID` (Google OAuth Web client ID)

```bash
VITE_API_URL=https://backend-<hash>-<region>.run.app/api/v1 \
VITE_GCS_CLIENT_ID=<web-client-id>.apps.googleusercontent.com \
./admin-portal/scripts/deploy-cloud-run.sh
```

### Google OAuth setup for admin portal
- In Google Cloud Console > APIs & Services > Credentials > OAuth 2.0 Client IDs (Web client):
	- Add the deployed admin portal URL to **Authorized JavaScript origins**
	- Keep local dev origin if needed: `http://localhost:5173`
- If the consent screen is in Testing mode, add your account under **OAuth consent screen > Test users**

### Common deploy pitfalls
- If admin portal build fails with missing `routeTree.gen.ts`, ensure `admin-portal/.gcloudignore` exists and includes `!src/routeTree.gen.ts`
- If admin portal cannot call backend after deploy, redeploy backend with `ADMIN_PORTAL_ORIGIN=<admin portal URL>` or update `ALLOWED_ORIGINS`

## Production Resources
- Permanent backend resources: Cloud Run service `backend`, Cloud SQL instance `ug-instance`, VPC connector `backend-connector`, Secret Manager secret `backend-postgres-password`, and the default VPC peering/private range used by Cloud SQL private IP

## Installing dependencies
- The backend uses [uv]() to manage dependencies. When getting setup for the first time, navigate to `backend` and run `uv sync`. This will download Python if necessary, create the `.venv` directory, and install dependencies from `pyproject.toml`.
- When adding new dependencies to the backend, add them with `uv pip add <package_name>`.