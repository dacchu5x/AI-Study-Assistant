
# AI Study Assistant — Python Backend

This is a Python/FastAPI replacement for the original Node.js/Express backend.

The React + Vite frontend does not need to be rewritten. This backend keeps the same API paths, HTTP methods, bearer-token authentication, upload field name (`pdf`), and response property names used by the original backend.

## Requirements

- Python 3.10 or newer
- MongoDB Atlas connection string
- Gemini API key and an API-enabled Gemini model

## Setup (Windows PowerShell)

Open a terminal in this folder:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and fill in your real MongoDB URI, JWT secret and Gemini API key.

Do not share `.env` or upload it to GitHub.

## Run

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

Keep the frontend's API base URL as `http://localhost:5000` if that is what it currently uses.

Backend health check: http://localhost:5000/api/health

Interactive API documentation: http://localhost:5000/docs

## API Compatibility

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/documents`
- `POST /api/documents/upload` (multipart field: `pdf`; optional field: `title`)
- `GET /api/documents/{id}`
- `DELETE /api/documents/{id}`
- `POST /api/ai/{id}/summarize`
- `POST /api/ai/{id}/chat`
- `POST /api/ai/{id}/quiz`
- `POST /api/ai/{id}/evaluate`

Protected routes use `Authorization: Bearer <token>`, matching the Express backend.

MongoDB uses the same `users` and `documents` collections and field names, so existing records can be reused. Back up your database before switching servers.

## DNS Note

If this Windows environment needs Google's DNS resolver for MongoDB SRV lookup, the connection setup can be configured separately.

This backend uses PyMongo. If `mongodb+srv://` DNS resolution fails, first test the Python environment's DNS resolution and network policy.

Do not replace the Atlas URI with guessed hostnames or expose database credentials.
