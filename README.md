<<<<<<< HEAD
# AI Study Assistant

An intermediate full-stack AI project for college assignments. It lets students register, upload PDF notes, generate summaries and MCQ quizzes, ask questions about uploaded material, and evaluate written answers.

## Stack
- Frontend: React + Vite
- Backend: Node.js + Express
- Database: MongoDB (Mongoose)
- AI: Google Gemini API (REST)
- PDF extraction: `pdf-parse`
- Authentication: JWT + bcrypt

## Requirements
- Node.js 18+
- npm
- MongoDB running locally, or a MongoDB Atlas connection string
- Gemini API key

## 1. Configure the backend

Open a terminal in `backend/`:

```bash
cp .env.example .env
npm install
```

Edit `.env`:

```env
PORT=5000
MONGODB_URI=mongodb://127.0.0.1:27017/ai_study_assistant
JWT_SECRET=replace_this_with_a_long_random_secret
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
CLIENT_ORIGIN=http://localhost:5173
```

Get a Gemini API key from Google AI Studio. Keep it only in the backend `.env` file. Never put it in the React frontend.

Start the backend:

```bash
npm run dev
```

The API runs at `http://localhost:5000`. Check `http://localhost:5000/api/health`.

## 2. Configure the frontend

Open another terminal in `frontend/`:

```bash
npm install
cp .env.example .env
npm run dev
```

The frontend runs at `http://localhost:5173`.

## 3. Use the app
1. Register an account.
2. Sign in.
3. Upload a text-based PDF (maximum 10 MB).
4. Open the document from your library.
5. Generate a summary, ask questions, create a quiz, or evaluate an answer.

## API overview
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Sign in |
| GET | `/api/documents` | List your documents |
| POST | `/api/documents/upload` | Upload and extract PDF text |
| GET | `/api/documents/:id` | Get document and extracted text |
| DELETE | `/api/documents/:id` | Delete a document |
| POST | `/api/ai/:id/summarize` | Generate summary |
| POST | `/api/ai/:id/chat` | Ask a question about a PDF |
| POST | `/api/ai/:id/quiz` | Generate MCQs |
| POST | `/api/ai/:id/evaluate` | Evaluate a written answer |

All document and AI routes require `Authorization: Bearer <token>`.

## Notes and troubleshooting
- **MongoDB connection error:** start your local MongoDB service or use a valid Atlas URI.
- **Gemini error:** verify `GEMINI_API_KEY`, model availability, quota, and internet access.
- **PDF has no text:** scanned/image-only PDFs need OCR, which this starter project does not include.
- **CORS error:** ensure `CLIENT_ORIGIN` matches the Vite URL.
- **Port conflict:** change `PORT` in backend `.env` and `VITE_API_URL` in frontend `.env`.
- The AI output is generated and can be incorrect. Verify important study answers against your course material.

## Project structure
```text
ai-study-assistant/
  backend/
    src/
      config/
      middleware/
      models/
      routes/
      services/
      utils/
    server.js
  frontend/
    src/
      components/
      pages/
      services/
      App.jsx
      main.jsx
```

## Academic extension ideas
- Add OCR for scanned PDFs.
- Add spaced-repetition flashcards.
- Add document search using embeddings and vector retrieval (RAG).
- Add quiz history and progress charts.
=======
# AI-Study-Assistant
>>>>>>> origin/main
