from app.core.config import settings
from supabase import Client, create_client

if not settings.resolved_supabase_key:
    raise RuntimeError(
        "Missing Supabase key. Set SUPABASE_SERVICE_ROLE_KEY (recommended) "
        "or SUPABASE_KEY/SUPABASE_ANON_KEY in .env"
    )

supabase: Client = create_client(settings.supabase_url, settings.resolved_supabase_key)


def get_supabase() -> Client:
    return supabase
