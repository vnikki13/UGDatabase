# Ultrasound Guidance Database
This codebase includes the postgres database, api endpoints and admin portal for Ultrasound Guidance.

## Run FastAPI
- Ensure you're in the `backend` folder
- Run `fastapi dev app/main.py`

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