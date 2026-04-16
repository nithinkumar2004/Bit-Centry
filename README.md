# 🛡️ BidSentry — AI-Powered Tender Evaluation System

> Explainable, tamper-evident AI system for tender evaluation with OCR, LLM-based criteria extraction, semantic matching, and audit logging.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)

---

## 📋 Overview

**BidSentry** is a full-stack AI-powered tender evaluation system built from scratch. It processes tender and bidder documents, extracts criteria via LLM, evaluates eligibility using semantic matching + rules, and maintains a tamper-evident audit trail.

### Core Modules
- 🔍 **Document AI** — OCR + structured data parsing (PaddleOCR)
- 🧠 **Criteria Extraction** — LLM-powered via OpenRouter API
- 📊 **Semantic Matching** — Sentence-BERT local embeddings
- ⚖️ **Decision Engine** — Deterministic rules + ambiguity detection
- 📝 **Explainability** — Natural language explanations for every decision
- 🔐 **Anti-Corruption** — SHA-256 hash chain audit trail

---

## 🏗️ Architecture

```
Frontend (React / Vite)
        ↓
Backend API (FastAPI)
        ↓
Core Services Layer
   ├─ OCR + Parsing (PaddleOCR)
   ├─ Criteria Extractor (OpenRouter LLM)
   ├─ Matching Engine (Sentence-BERT local)
   ├─ Decision Engine (rules)
   ├─ Explanation Generator (LLM / template)
   ├─ Ambiguity Detector
   ├─ Audit Logger (hash chain)
        ↓
Database (MongoDB)
        ↓
File Storage (local ./uploads)
```

---

## 📁 Project Structure

```
Bid-Centry/
├── .env                          # API keys & configuration
├── README.md                     # This file
├── start_backend.bat             # Backend launcher
├── start_frontend.bat            # Frontend launcher
│
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── requirements.txt          # Python dependencies
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── mongodb.py            # Async MongoDB connection (motor)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tender.py             # Tender + Criterion schemas
│   │   ├── bidder.py             # Bidder + ExtractedData schemas
│   │   ├── evaluation.py         # Evaluation result schemas
│   │   └── audit.py              # Audit log schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── tenders.py            # Tender CRUD + OCR + extraction
│   │   ├── bidders.py            # Bidder upload + parsing
│   │   ├── evaluations.py        # Run eval, view, export CSV/JSON
│   │   └── audit.py              # Audit log listing + chain verify
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr.py                # PaddleOCR text extraction
│   │   ├── llm.py                # OpenRouter API + caching
│   │   ├── matcher.py            # Sentence-BERT semantic matching
│   │   ├── decision.py           # Rule-based decision engine
│   │   └── audit.py              # SHA-256 hash chain audit logging
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py       # File save, hash, type detection
│       └── extractors.py         # Regex extractors (turnover, certs, projects)
│
└── frontend/
    ├── index.html                # Root HTML with Inter font
    ├── package.json              # React + Vite dependencies
    ├── vite.config.js            # Vite config with API proxy
    └── src/
        ├── main.jsx              # React entry point
        ├── App.jsx               # Root layout + routing
        ├── index.css             # Complete design system (dark theme)
        ├── api/
        │   └── client.js         # Axios API client
        ├── components/
        │   ├── Sidebar.jsx       # Navigation sidebar
        │   ├── FileUpload.jsx    # Drag-and-drop file upload
        │   ├── Modal.jsx         # Reusable modal
        │   ├── StatusBadge.jsx   # Color-coded status badges
        │   └── ToastContainer.jsx# Toast notifications
        └── pages/
            ├── Dashboard.jsx     # Stats, quick actions, activity
            ├── Tenders.jsx       # Tender list + upload
            ├── TenderDetail.jsx  # Criteria + bidders + eval trigger
            ├── Bidders.jsx       # Bidder cards + multi-file upload
            ├── Evaluations.jsx   # Results with explanations + export
            └── AuditLog.jsx      # Hash chain display + verification
```

---

## 🚀 Setup & Running

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| MongoDB | 6.0+ (running on `localhost:27017`) |

### Step 1: Configure API Key

Edit `.env` and set your OpenRouter API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

> **Note:** Without the API key, the system uses **mock criteria** for testing. All other features (OCR, matching, audit) work without it.

### Step 2: Start Backend

Open a terminal and run:

```bash
cd Bid-Centry
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Or double-click `start_backend.bat`.

> ⚠️ **PaddlePaddle + PaddleOCR** are large packages (~1.5GB). First install may take 5–10 minutes.

### Step 3: Start Frontend

Open **another** terminal and run:

```bash
cd Bid-Centry/frontend
npm install
npm run dev
```

Or double-click `start_frontend.bat`.

### Step 4: Open Dashboard

| Service | URL |
|---------|-----|
| 🖥️ Frontend Dashboard | http://localhost:5173 |
| 📚 Backend API Docs | http://localhost:8000/docs |
| 💚 Health Check | http://localhost:8000/api/health |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tenders/upload` | Upload tender PDF/image |
| `POST` | `/api/tenders/{id}/extract` | Extract criteria via LLM |
| `GET` | `/api/tenders` | List all tenders |
| `GET` | `/api/tenders/{id}` | Get tender details |
| `DELETE` | `/api/tenders/{id}` | Delete tender |
| `POST` | `/api/bidders/upload` | Upload bidder docs (multi-file) |
| `GET` | `/api/bidders` | List bidders (optional `?tender_id=`) |
| `GET` | `/api/bidders/{id}` | Get bidder details |
| `DELETE` | `/api/bidders/{id}` | Delete bidder |
| `POST` | `/api/evaluations/run` | Run evaluation (`?tender_id=&bidder_ids=`) |
| `GET` | `/api/evaluations/{tender_id}` | Get all evaluations for tender |
| `GET` | `/api/evaluations/{tender_id}/export/csv` | Export as CSV |
| `GET` | `/api/evaluations/{tender_id}/export/json` | Export as JSON |
| `GET` | `/api/audit` | List audit logs (filterable) |
| `GET` | `/api/audit/verify` | Verify hash chain integrity |
| `GET` | `/api/dashboard/stats` | Dashboard statistics |

---

## 🔄 Usage Flow

```
1. Upload Tender PDF
       ↓
2. Extract Criteria (LLM)
       ↓
3. Upload Bidder Documents
       ↓
4. OCR + Data Extraction
       ↓
5. Run Evaluation
       ↓
6. Semantic Match + Rules
       ↓
7. View Results + Explanations
       ↓
8. Export Report (CSV/JSON)
       ↓
9. Verify Audit Trail
```

### Detailed Steps

1. **Upload a tender** — Navigate to Tenders → Upload Tender. Drag-and-drop a PDF or image.
2. **Extract criteria** — Click the ✨ Extract button. The LLM analyzes the document and returns structured criteria (financial, technical, compliance).
3. **Add bidders** — Navigate to Bidders → Add Bidder. Select the tender, upload multiple documents (balance sheets, certificates, etc.).
4. **Auto-parsing** — OCR extracts text, regex parsers pull out turnover, certifications, and project counts automatically.
5. **Run evaluation** — From the Tender Detail page or Evaluations page, click "Run Evaluation."
6. **View results** — Each bidder gets: Eligible ✅, Not Eligible ❌, or Needs Manual Review ⚠️ with per-criterion explanations.
7. **Export** — Download results as CSV or JSON for offline reporting.
8. **Audit trail** — Every action is logged with SHA-256 hashes. Verify chain integrity at any time.

---

## 🧠 AI Pipeline

### OCR (PaddleOCR)
- Lazy-loaded to avoid heavy startup cost
- Handles both **text-based PDFs** (via PyPDF2) and **scanned images** (via PaddleOCR)
- Confidence scoring per extraction — low confidence (< 70%) is flagged

### Criteria Extraction (OpenRouter LLM)
- Uses `google/gemini-2.0-flash-001` by default (fast, affordable)
- Structured JSON output with `response_format: json_object`
- **Response caching** — SHA-256 hash of prompt → cached in MongoDB `llm_cache` collection
- 3 retries with exponential backoff
- Falls back to mock criteria if API is unavailable

### Semantic Matching (Sentence-BERT)
- Model: `all-MiniLM-L6-v2` (~80MB, runs locally)
- Cosine similarity between criteria descriptions and extracted data
- **Hybrid approach**: semantic similarity for text, rule-based for numeric thresholds

### Decision Engine
- Deterministic rules:
  - **Financial**: `value ≥ threshold` → Eligible
  - **Compliance**: `certificate present` → Eligible
  - **Technical**: `project_count ≥ threshold` → Eligible
  - **Low confidence / missing** → Needs Manual Review
- Configurable ambiguity threshold (default: 0.75)

---

## 🔐 Anti-Corruption / Audit System

Every action creates an immutable audit log entry:

```json
{
  "action": "EVALUATE",
  "entity_type": "evaluation",
  "entity_id": "abc123",
  "input_hash": "sha256(...)",
  "output_hash": "sha256(...)",
  "prev_hash": "sha256(previous_entry)",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

- **SHA-256 hashing** of all inputs and outputs
- **Hash chain**: each entry references `prev_hash` of the previous entry (blockchain-style)
- **Chain verification**: `/api/audit/verify` validates the entire chain
- **Tamper detection**: any modification breaks the chain

---

## 📊 MongoDB Collections

| Collection | Purpose |
|------------|---------|
| `tenders` | Tender documents + extracted criteria |
| `bidders` | Bidder data + OCR-extracted fields |
| `evaluations` | Per-bidder evaluation results |
| `audit_logs` | Immutable hash-chained audit trail |
| `llm_cache` | Cached LLM responses (by prompt hash) |

---

## 🎨 Frontend Features

- **Dashboard** — Real-time stats, pass rate, recent activity feed
- **Tenders** — Table view, upload modal with drag-and-drop, one-click criteria extraction
- **Tender Detail** — Criteria cards, linked bidders, evaluation trigger
- **Bidders** — Card grid with extracted data preview, OCR confidence bars, multi-file upload
- **Evaluations** — Expandable results per bidder, per-criterion explanations, CSV/JSON export
- **Audit Log** — Hash chain table, chain verification status, filtering and pagination
- **Design** — Dark glassmorphism theme, gradient accents, micro-animations, responsive layout

---

## ⚙️ Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Your OpenRouter API key |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `bidsentry` | Database name |
| `LLM_MODEL` | `google/gemini-2.0-flash-001` | LLM model via OpenRouter |
| `UPLOAD_DIR` | `./uploads` | File storage directory |
| `BACKEND_PORT` | `8000` | Backend server port |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend URL (for CORS) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python) |
| Database | MongoDB + motor (async) |
| OCR Engine | PaddleOCR |
| Embeddings | Sentence-BERT (`all-MiniLM-L6-v2`) |
| LLM API | OpenRouter (Gemini Flash) |
| Frontend | React 18 + Vite |
| Styling | Custom CSS (dark glassmorphism) |
| Icons | Lucide React |
| HTTP Client | Axios (frontend) / httpx (backend) |

---

## 📝 License

Built for hackathon/evaluation purposes. MIT License.
