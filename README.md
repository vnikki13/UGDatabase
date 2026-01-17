# Ultrasound Guidance Database
This codebase includes the postgres database, api endpoints and admin portal for Ultrasound Guidance.

## Run FastAPI
- Ensure you're in the `backend` folder
- Run `fastapi dev app/main.py`

## Run Vite
- Ensure you're in the `admin-portal` folder
- Run `npm run dev`

## Migrations
- Ensure you're in the `backend` folder
- Make changes to the models
- Run `alembic revision --autogenerate -m "<Migration message>"`
- Confirm migration file looks correct
- Run `alembic upgrade head`
- Confirm migration changes are correct

- Use `alembic downgrade -1` (where `-1` is the number of versions) to downgrade


## Docker
- Build images with `docker compose up --build -d`

## Installing dependencies
- The backend uses [uv]() to manage dependencies. When getting setup for the first time, navigate to `backend` and run `uv sync`. This will download Python if necessary, create the `.venv` directory, and install dependencies from `pyproject.toml`.
- When adding new dependencies to the backend, add them with `uv pip add <package_name>`.