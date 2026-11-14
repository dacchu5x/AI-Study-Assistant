import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
import requests
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient
from pypdf import PdfReader
from io import BytesIO

# Load .env from this backend folder, regardless of the terminal's current directory.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

PORT = int(os.getenv("PORT", "5000"))
MONGODB_URI = os.getenv("MONGODB_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
CLIENT_ORIGIN = os.getenv("CLIENT_ORIGIN", "http://localhost:5173")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is missing. Create backend/.env using .env.example.")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing. Add it to backend/.env.")

mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=15000)
mongo_client.admin.command("ping")
try:
    db = mongo_client.get_default_database()
except Exception:
    # If the URI has no database name, use the same application database explicitly.
    db = mongo_client["ai_study_assistant"]
if db is None:
    db = mongo_client["ai_study_assistant"]

users = db["users"]
documents = db["documents"]
users.create_index("email", unique=True)
documents.create_index([("user", 1), ("createdAt", -1)])

app = FastAPI(title="AI Study Assistant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    # Keep the original Express API's { "message": "..." } error response shape.
    return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail)})

def utc_now():
    return datetime.now(timezone.utc)

def serialize_doc(doc, omit_text=False):
    if not doc:
        return None
    result = dict(doc)
    result["_id"] = str(result["_id"])
    result["user"] = str(result["user"]) if isinstance(result.get("user"), ObjectId) else result.get("user")
    if omit_text:
        result.pop("extractedText", None)
    return result

def make_token(user_id):
    payload = {"userId": str(user_id), "exp": utc_now() + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in first.")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("userId")
        if not user_id or not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user id")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")

def get_owned_document(document_id: str, user_id: str):
    if not ObjectId.is_valid(document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    doc = documents.find_one({"_id": ObjectId(document_id), "user": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini API key is missing. Add GEMINI_API_KEY to backend/.env.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    try:
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=90,
        )
        data = response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}")
    except ValueError:
        raise HTTPException(status_code=502, detail="Gemini returned an invalid response.")
    if not response.ok:
        message = data.get("error", {}).get("message", "Gemini request failed.")
        raise HTTPException(status_code=response.status_code, detail=message)
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    return text or "No response generated."

class RegisterBody(BaseModel):
    name: str
    email: str
    password: str

class LoginBody(BaseModel):
    email: str
    password: str

class ChatBody(BaseModel):
    question: str

class EvaluateBody(BaseModel):
    question: str
    answer: str

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI Study Assistant API"}

@app.post("/api/auth/register", status_code=201)
def register(body: RegisterBody):
    name = body.name.strip()
    email = body.email.strip().lower()
    password = body.password
    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Name, email and password are required.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")
    user = {"name": name, "email": email, "password": password_hash, "createdAt": utc_now(), "updatedAt": utc_now()}
    inserted = users.insert_one(user)
    return {"token": make_token(inserted.inserted_id), "user": {"id": str(inserted.inserted_id), "name": name, "email": email}}

@app.post("/api/auth/login")
def login(body: LoginBody):
    email = body.email.lower().strip()
    user = users.find_one({"email": email})
    valid = False
    if user:
        try:
            valid = bcrypt.checkpw(body.password.encode("utf-8"), user["password"].encode("utf-8"))
        except (ValueError, KeyError):
            valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"token": make_token(user["_id"]), "user": {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}}

@app.get("/api/documents")
def list_documents(user_id: str = Depends(current_user)):
    docs = documents.find({"user": ObjectId(user_id)}).sort("createdAt", -1)
    return [serialize_doc(doc, omit_text=True) for doc in docs]

@app.post("/api/documents/upload", status_code=201)
async def upload_document(
    pdf: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    user_id: str = Depends(current_user),
):
    filename = pdf.filename or "upload.pdf"
    content_type = pdf.content_type or ""
    if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    content = await pdf.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
    try:
        reader = PdfReader(BytesIO(content))
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read this PDF file.")
    if len(extracted_text) < 40:
        raise HTTPException(status_code=422, detail="No readable text found. This may be a scanned PDF; OCR is not included.")
    clean_title = (title or "").strip() or filename.rsplit(".", 1)[0]
    now = utc_now()
    record = {
        "user": ObjectId(user_id),
        "title": clean_title,
        "originalName": filename,
        "extractedText": extracted_text,
        "summary": "",
        "createdAt": now,
        "updatedAt": now,
    }
    inserted = documents.insert_one(record)
    return {"_id": str(inserted.inserted_id), "title": clean_title, "originalName": filename, "createdAt": now}

@app.get("/api/documents/{document_id}")
def get_document(document_id: str, user_id: str = Depends(current_user)):
    doc = get_owned_document(document_id, user_id)
    return serialize_doc(doc)

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str, user_id: str = Depends(current_user)):
    doc = get_owned_document(document_id, user_id)
    documents.delete_one({"_id": doc["_id"], "user": ObjectId(user_id)})
    return {"message": "Document deleted."}

@app.post("/api/ai/{document_id}/summarize")
def summarize(document_id: str, user_id: str = Depends(current_user)):
    doc = get_owned_document(document_id, user_id)
    notes = doc["extractedText"][:24000]
    summary = ask_gemini(
        "You are a helpful study tutor. Summarize these study notes using clear headings, key definitions, and concise bullet points. Do not invent facts.\n\nNOTES:\n"
        + notes
    )
    documents.update_one({"_id": doc["_id"]}, {"$set": {"summary": summary, "updatedAt": utc_now()}})
    return {"summary": summary}

@app.post("/api/ai/{document_id}/chat")
def chat(document_id: str, body: ChatBody, user_id: str = Depends(current_user)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Enter a question.")
    doc = get_owned_document(document_id, user_id)
    answer = ask_gemini(
        "Answer the student's question using the supplied notes. If the answer is not in the notes, say so clearly. Use simple student-friendly language.\n\nNOTES:\n"
        + doc["extractedText"][:24000]
        + "\n\nQUESTION: "
        + question[:1000]
    )
    return {"answer": answer}

@app.post("/api/ai/{document_id}/quiz")
def quiz(document_id: str, user_id: str = Depends(current_user)):
    doc = get_owned_document(document_id, user_id)
    raw = ask_gemini(
        'Create 5 multiple-choice questions from these notes. Return ONLY valid JSON in this exact shape: {"questions":[{"question":"...","options":["A...","B...","C...","D..."],"answer":0,"explanation":"..."}]}. answer must be the zero-based index of the correct option. Avoid trick questions.\n\nNOTES:\n'
        + doc["extractedText"][:24000]
    )
    import json, re
    try:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        result = json.loads(clean)
        if not isinstance(result.get("questions"), list):
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=502, detail="The AI returned an unreadable quiz. Please try again.")
    return result

@app.post("/api/ai/{document_id}/evaluate")
def evaluate(document_id: str, body: EvaluateBody, user_id: str = Depends(current_user)):
    question = body.question.strip()
    answer = body.answer.strip()
    if not question or not answer:
        raise HTTPException(status_code=400, detail="Enter both the question and your answer.")
    doc = get_owned_document(document_id, user_id)
    feedback = ask_gemini(
        "Evaluate this student's answer based on the notes. Give a score out of 10, what is correct, what is missing, and an improved model answer. Be encouraging and fair.\n\nNOTES:\n"
        + doc["extractedText"][:24000]
        + "\n\nQUESTION: "
        + question[:1000]
        + "\nSTUDENT ANSWER: "
        + answer[:4000]
    )
    return {"feedback": feedback}
