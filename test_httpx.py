import httpx

try:
    r = httpx.get("https://nskrwzvisbimahlvwbza.supabase.co")
    print(r.status_code)
except Exception as e:
    print(type(e).__name__, e)