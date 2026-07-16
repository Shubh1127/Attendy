from supabase import create_client

from core.config import settings

from core.config import settings

print("SUPABASE_URL:", repr(settings.supabase_url))
print("SUPABASE_KEY exists:", bool(settings.supabase_key))
supabase = create_client(
    settings.supabase_url,
    settings.supabase_key
)

admin_supabase = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key or settings.supabase_key
)