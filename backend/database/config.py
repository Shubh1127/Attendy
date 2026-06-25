from supabase import create_client

from core.config import settings

supabase = create_client(
    settings.supabase_url,
    settings.supabase_key
)