# Tasks: Database Schema and Migrations

- [x] **Setup Alembic Environment**
    - [x] Verify `backend/alembic.ini` exists and points to `script_location = alembic`.
    - [x] Run `alembic init alembic` inside `backend/` if `backend/alembic` directory does not exist.
    - [x] Update `backend/alembic/env.py`:
        - [x] Import `Base` from `models`.
        - [x] Import `load_dotenv` and load `.env`.
        - [x] Set `target_metadata = Base.metadata`.
        - [x] Configure `sqlalchemy.url` from environment variable.

- [x] **Generate Migration**
    - [x] Run `alembic revision --autogenerate -m "Initial schema"` in `backend/` (Manually created `001_initial_schema.py`).
    - [x] Review generated migration file in `backend/alembic/versions/`.

- [x] **Apply Migration**
    - [x] Run `alembic upgrade head`.

- [x] **Verification**
    - [x] Connect to database and list tables to confirm creation.