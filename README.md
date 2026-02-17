# My Fitness API (FastAPI + Supabase)

Backend for the Flutter app at `D:\Flutter Apps\my_fitness`.

## Supabase Configuration

This project reads environment values from `.env`.

Update these values with your actual Supabase project credentials:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_DB_URL` (Postgres connection string from Supabase)

The API is configured to use **Supabase Postgres only** via `SUPABASE_DB_URL`.
There is no SQLite fallback.

## Install and Run

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

## Docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Seeded Demo User

- Email: `demo@myfitness.app`
- Password: `demo1234`
