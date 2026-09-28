# Billing 2.0

Automated billing management system foundation.

## 1. Project Purpose
Billing 2.0 is designed to streamline duty slip ingestion, automated data extraction, billing reconciliation, and document generation (e.g. Word/PDF). 

This repository currently contains the initial architectural **foundation** only. Business logic, OCR, AI extraction, and document generation workflows will be enabled incrementally in subsequent steps.

---

## 2. Current Architecture

```
Frontend (React + Vite + Tailwind CSS)
    ↓ REST API (JSON)
Backend (Python + FastAPI)
    ↓
Service Layer (Storage / Database abstractions)
    ↓
MongoDB (PyMongo Client) & Local/Cloud Storage Abstraction
```

### Directory Layout
```text
.
├── .gitignore
├── README.md
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   ├── router.py
│       │   └── endpoints/
│       │       ├── health.py
│       │       └── auth.py (placeholder)
│       ├── core/
│       │   ├── config.py
│       │   └── database.py
│       ├── models/
│       ├── schemas/
│       │   ├── auth.py
│       │   └── health.py
│       └── services/
│           └── storage/
│               ├── base.py
│               └── local.py
└── frontend/
    ├── .env.example
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── index.css
        ├── api/
        │   └── client.js
        ├── components/
        │   ├── common/
        │   │   └── Header.jsx
        │   └── layout/
        │       └── AppLayout.jsx
        ├── pages/
        │   └── Dashboard.jsx
        └── router/
            └── index.jsx
```

---

## 3. Environment Variables

### Backend (`backend/.env`)
| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | Name of the FastAPI application | `"Billing 2.0 API"` |
| `APP_ENV` | Environment mode (`development`, `production`) | `"development"` |
| `DEBUG` | Enable debug logs & reload | `true` |
| `PORT` | Backend listening port | `8000` |
| `HOST` | Backend host | `127.0.0.1` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:5173,http://127.0.0.1:5173` |
| `MONGODB_URI` | MongoDB connection URI | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Target MongoDB database | `billing_db` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Placeholder |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration in minutes | `60` |
| `STORAGE_TYPE` | Storage provider (`local`) | `local` |
| `LOCAL_STORAGE_BASE_DIR` | Base directory for local files | `./storage` |

### Frontend (`frontend/.env`)
| Variable | Description | Default |
|---|---|---|
| `VITE_APP_TITLE` | Web title in browser | `Billing 2.0` |
| `VITE_API_BASE_URL` | Base endpoint for REST API | `http://localhost:8000/api/v1` |

---

## 4. Setup and Running

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB instance (local or MongoDB Atlas)

### Backend Setup
1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # Linux/macOS
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment:
   ```bash
   cp .env.example .env
   ```
5. Start the backend:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   * Health check endpoint: `http://127.0.0.1:8000/api/v1/health`
   * Interactive API docs: `http://127.0.0.1:8000/docs`

### Frontend Setup
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure environment:
   ```bash
   cp .env.example .env
   ```
4. Start the frontend:
   ```bash
   npm run dev
   ```
   * App URL: `http://localhost:5173`

---

## 5. MongoDB Setup Requirements
- The application connects to MongoDB using PyMongo.
- Ensure MongoDB server is running on `mongodb://localhost:27017` or specify your remote URI in `backend/.env` under `MONGODB_URI`.
- The database connection is dynamically verified via the health endpoint (`/api/v1/health`). If MongoDB is not yet running, the FastAPI service will continue to run with `database_connected: false` reported cleanly.

---

## 6. What Is Intentionally NOT Implemented Yet
As part of the initial Step 2 foundation, the following modules are intentionally omitted and reserved for subsequent steps:
- **No OCR engine or processing** (Tesseract / EasyOCR / Vision APIs).
- **No AI extraction or LLM prompt pipelines**.
- **No billing calculation or business rule logic**.
- **No duty-slip upload/processing workflow**.
- **No Word/DOCX document generation (`python-docx`)**.
- **No full JWT authentication or user authorization logic** (scaffolded only).
- **No mock business data or dummy invoices**.
