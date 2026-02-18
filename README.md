# My Fitness API (FastAPI)

Backend for the Flutter app at `D:\Flutter Apps\my_fitness`.

## Configuration

This project reads environment values from `.env`.

Required values:

- `SUPABASE_URL`
- `SUPABASE_KEY`

This backend now uses the **Supabase Python client directly** (REST/PostgREST) and does **not** require `SUPABASE_DB_URL`.

## Install and Run

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

## Docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Seeded Demo User

No automatic SQL seed runs on startup anymore. Create users via `/v1/auth/register` or directly in your Supabase tables.
