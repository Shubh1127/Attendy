# test_google.py
import httpx

print(httpx.get("https://www.google.com").status_code)