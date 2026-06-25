# Snap Class Python Backend

FastAPI backend for the Snap Class Next.js frontend.

## What it provides now
- `POST /auth/face-login`
- `POST /auth/voice-login`
- `POST /enrollment/face`
- `POST /enrollment/voice`
- `GET /me`
- `GET /health`

## Setup
1. Copy `.env.example` to `.env` and fill in your Supabase credentials.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API from the `backend` folder:
   ```bash
   uvicorn app:app --reload --port 8000
   ```

## Frontend integration
Set your Next.js API base URL to `http://localhost:8000`.

The frontend sends face and audio capture as `multipart/form-data`.
