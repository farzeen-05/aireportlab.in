# 📊 aireportlab — AI-Powered Document & Dataset Analysis Platform

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-ML-F7931E?logo=scikitlearn)
![NLTK](https://img.shields.io/badge/NLTK-NLP-green)
![Groq](https://img.shields.io/badge/Groq-LLM%20Q%26A-F55036)
![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Export-red)
![OAuth](https://img.shields.io/badge/Google-OAuth%202.0-4285F4?logo=google)
![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render)
![License](https://img.shields.io/badge/License-MIT-yellow)

> Upload any CSV, Excel, PDF, DOCX, JSON, or TXT file and instantly get a professional, AI-generated analytical report — 15+ auto-selected visualizations, NLP keyword extraction, ML anomaly detection, a Groq-powered AI chat to ask follow-up questions about your data, and a downloadable PDF. No coding required.

🔗 **Live Demo:** [https://aireportlab-in-hzxn.onrender.com/](https://aireportlab-in-hzxn.onrender.com/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Core Engines](#core-engines)
- [AI Q&A & Chat](#ai-qa--chat)
- [Project Structure](#Project-Structure)
- [Module Breakdown](#module-breakdown)
- [Authentication](#authentication)
- [Deployment](#deployment)
- [Challenges & Solutions](#challenges--solutions)
- [Key Numbers](#key-numbers)
- [Getting Started](#getting-started)

---

## Overview

Most data analysis tools require a user to already know how to code. **aireportlab** removes that barrier — a user uploads a file, and the platform automatically detects its type and domain, runs the appropriate ML/NLP pipeline, generates charts and insights, and produces a polished PDF report, with zero manual configuration.

**What it does:**
- Accepts 6 file types: CSV, Excel, PDF, DOCX, JSON, TXT
- Auto-detects column types and dataset domain (healthcare, sales, finance, logistics, generic)
- Generates 15+ context-aware visualizations
- Runs domain-aware NLP analysis on documents (9 domain templates: academic, research, business, legal, medical, security, financial, technical, resume)
- Detects statistical anomalies in tabular data
- Generates a dual executive summary — an AI-written version (Groq) alongside the template-based one, toggleable side by side
- Lets you ask free-form follow-up questions about your data or document through an AI chat, on both a fresh upload and any previously saved report
- Exports a complete PDF report, stored directly in the database
- Supports Google OAuth and email/password authentication

---

## Architecture

```
User uploads file (CSV / Excel / PDF / DOCX / JSON / TXT)
              │
              ▼
      Flask receives file
              │
              ▼
      File Reader → extracts raw content
              │
              ▼
      Preprocessor → cleans & profiles data
              │
              ▼
   ┌─────────────────────────────────┐
   │      Analysis Pipeline          │
   │  ├── ML   (IQR anomaly detect)  │
   │  ├── NLP  (TF-IDF, keyphrases)  │
   │  └── DL   (linguistic analysis) │
   └─────────────────────────────────┘
              │
              ▼
      Visualization Engine → 15+ charts
              │
              ▼
      Report Generator → dual executive summary (AI + template)
              │
              ▼
      PDF Export (ReportLab, in-memory)
              │
              ▼
      Saved as BLOB in SQLite → served to user
              │
              ▼
      AI Chat (Groq) → ask follow-up questions anytime
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask, Gunicorn |
| Database | SQLite |
| Data Processing | Pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Machine Learning | Scikit-learn, IQR-based anomaly detection |
| NLP | NLTK, custom TF-IDF implementation |
| LLM / Chat | Groq API (`openai/gpt-oss-20b`) |
| PDF Generation | ReportLab (in-memory, no disk writes) |
| Authentication | Authlib (Google OAuth 2.0), Werkzeug (bcrypt password hashing) |
| Email | Resend API |
| Deployment | Render (free tier, memory-optimized) |

---

## Core Engines

### 🎨 VisualizationEngine (custom-built)
Automatically profiles every column — `id`, `datetime`, `numeric`, `binary`, `categorical`, `text` — using name patterns, data types, and cardinality, then selects the right chart type per column:

| Column Type | Chart(s) |
|-------------|----------|
| Numeric | Histogram + KDE, box plot |
| Categorical (≤6 values) | Pie + bar chart |
| Categorical (>6 values) | Horizontal bar chart |
| DateTime | Area + line trend |
| Binary vs Numeric | Violin plot |
| Binary vs Categorical | Stacked bar (proportion) |
| Numeric pairs | Scatter plot (top 3 correlated) |
| All numeric columns | Correlation heatmap |

Also generates **domain-specific charts** — e.g. stroke-by-hypertension for healthcare data, revenue-by-product-line for sales data — plus a dataset overview card (missing values, column type breakdown, summary stats).

### 📝 TextAnalysisEngine (custom-built)
For PDF/DOCX/TXT/JSON documents:
- **Domain detection** across 9 categories using keyword scoring
- **Custom TF-IDF** (pure Python, no sklearn dependency) for keyword extraction
- **Keyphrase extraction** (bigrams/trigrams) for more meaningful topics
- **Structure extraction** — detects section headings via regex (numbered, ALL CAPS, title-case)
- **Flesch-Kincaid readability scoring**
- **Sentiment analysis** via curated positive/negative word lists
- **Domain-aware summary generation** — different templates per document type

### 🤖 LLM Q&A Engine (Groq-powered)
Wraps the Groq API to add a conversational layer on top of the template-based analysis:
- **Dual executive summaries** — an AI-generated summary alongside the deterministic template one, so results stay explainable even when the AI call fails or is disabled
- **Suggested questions** generated per report to jump-start the conversation
- **Context-aware chat** — grounded in the actual extracted text or dataset summary, not a generic prompt, with the last 6 turns of conversation history sent per request
- **Two entry points** — live chat on a report right after upload, and chat on any previously saved report pulled back from the database

---

## AI Q&A & Chat

Every generated report includes an **"Ask AI About This Dataset/Document"** panel:

- Type a free-form question, or tap one of the AI-suggested starter questions
- Answers come back with a confidence indicator (✓ Confident / ⚠ Low confidence)
- Works two ways depending on where you are:
  - **`/api/qna`** — on a report you just generated, grounded in the live extracted text/data
  - **`/api/qna/<report_id>`** — on any report pulled from History, grounded in what was saved to the database (summary, key insights, recommendations, keywords)
- The executive summary itself is dual-mode — toggle between the **🤖 AI** version and the **📋 Template** version to compare

---

## 📁 Project Structure

```
aireportlab.in/
│
├── app.py                      # Main Flask application
├── visualization_engine.py     # Custom chart generation engine
├── text_analysis_engine.py     # Custom NLP & domain analysis engine
├── gunicorn.conf.py            # Production server config
├── requirements.txt
│
├── utils/
│   ├── file_reader.py          # Multi-format file extraction
│   ├── preprocess.py           # Data cleaning & preprocessing
│   ├── insights.py             # AI insight generation (template + LLM)
│   ├── llm_engine.py           # Groq API wrapper — summaries, Q&A, suggested questions
│   ├── breakdown.py            # Column/page breakdown summaries
│   ├── ml_model.py             # Anomaly detection
│   ├── nlp_model.py            # NLP analysis
│   ├── dl_model.py             # Deep linguistic analysis
│   ├── report_generator.py     # Final report assembly
│   ├── export_report.py        # PDF generation (ReportLab)
│   ├── document_classifier.py  # Document type detection
│   ├── research_parser.py      # Research paper section extraction
│   └── db.py                   # Database operations
│
├── templates/
│   ├── base.html
│   ├── landing.html
│   ├── upload.html
│   ├── report.html
│   ├── view_report.html
│   ├── history.html
│   ├── settings.html
│   ├── login.html
│   ├── register.html
│   └── ...
│
├── static/
│   ├── charts/                 # Generated chart images
│   ├── css/
│   ├── js/
│   └── img/
│
└── database.db                 # SQLite database
```

---

## Module Breakdown

| Module | Responsibility |
|--------|----------------|
| `utils/file_reader.py` | Extracts raw content per file type (CSV, Excel, PDF, DOCX, JSON, TXT) |
| `utils/preprocess.py` | Cleans data, fills missing values, detects column roles and dataset domain |
| `visualization_engine.py` | Column profiling and automatic chart generation |
| `text_analysis_engine.py` | Domain detection, TF-IDF, keyphrases, structure, readability, sentiment |
| `utils/ml_model.py` | IQR-based anomaly detection for tabular data |
| `utils/nlp_model.py` | Runs TextAnalysisEngine for text files |
| `utils/llm_engine.py` | Groq wrapper: dual summaries, suggested questions, chat Q&A |
| `utils/report_generator.py` | Combines all analysis into an executive summary + recommendations |
| `utils/export_report.py` | Builds the PDF entirely in memory using ReportLab |
| `utils/db.py` | SQLite schema — `users`, `upload_history`, `app_settings` |

**Why IQR over Isolation Forest:** IQR is pure math with no heavy ML dependency, and works reliably for statistical outliers across healthcare, sales, and financial datasets.

**Why in-memory PDF generation:** Render's filesystem is ephemeral — anything written to disk is lost on redeploy. PDFs are built directly into a `BytesIO` buffer and stored as a BLOB in SQLite, so downloads are served straight from the database.

---

## Authentication

- **Email/Password** — passwords hashed with Werkzeug's `generate_password_hash` (bcrypt), never stored in plain text
- **Google OAuth 2.0** — handled via Authlib; auto-creates an account for new users and stores their profile picture in session
- **Forgot Password** — 32-byte secure token via `secrets.token_urlsafe`, 1-hour expiry, reset link sent through the Resend API
- **Stale-session recovery** — since the database resets on every redeploy (see below), a session pointing at a `user_id` that no longer exists is detected and the user is transparently signed out and asked to log back in, instead of hitting a raw foreign-key error

---

## Deployment

**Pipeline:** Local → GitHub → Render (auto-deploy on push)

**Memory optimization for Render's 512MB limit:**
- Single Gunicorn worker, 2 threads (`workers=1, threads=2`)
- Worker timeout of 120s to handle large files, `max_requests=50` to recycle workers and prevent memory leaks
- Datasets sampled above 5,000 rows, capped at 20 columns
- Chart DPI reduced to 72
- `plt.close('all')` and `gc.collect()` called after every chart-heavy operation
- Heavy ML/NLP libraries imported lazily, only when needed

---

## Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| 512MB RAM limit on Render | Dataset sampling, lower chart DPI, lazy imports, aggressive `gc.collect()` |
| Render blocks SMTP port 587 | Switched to the Resend API over HTTPS (port 443) |
| Chart images lost on redeploy | Charts regenerated per upload; PDFs stored permanently as DB BLOBs |
| Ephemeral filesystem resets the SQLite DB on redeploy | `user_exists()` check in the auth decorator + a caught `IntegrityError` on upload — stale sessions are cleared and the user is re-prompted to log in, instead of a raw 500 |
| Different file types need different pipelines | Type-detection router splits into tabular vs. text analysis paths |
| Generic reports for all documents | Built a 9-domain-template TextAnalysisEngine |
| TF-IDF surfacing stopwords as keywords | Custom stopword set + minimum word length filter |
| Hosted LLM model IDs get deprecated over time | Single `MODEL` constant in `llm_engine.py` — one-line change to migrate when a provider retires a model |

---

## Key Numbers

| Metric | Value |
|--------|-------|
| File types supported | 6 (CSV, Excel, PDF, DOCX, JSON, TXT) |
| Chart types generated | 15+ |
| Document domains detected | 9 |
| ML algorithm | IQR anomaly detection |
| NLP algorithm | Custom TF-IDF + NLTK tokenization |
| Max file size | 10 MB |
| Dataset row limit | 5,000 (sampled) |
| Password security | bcrypt hashing |
| Reset token expiry | 1 hour |
| Server RAM limit | 512 MB (Render free tier) |

---

## Getting Started

### Prerequisites
- Python 3.11+
- pip

### Local Setup

```bash
# Clone the repository
git clone https://github.com/farzeen-05/aireportlab.in.git
cd aireportlab.in

# Install dependencies
pip install -r requirements.txt

# Set environment variables (.env)
# GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, RESEND_API_KEY, SECRET_KEY, GROQ_API_KEY, etc.

# Run the app
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Author

**Farzeen Abdul Khadir**
ECE Graduate | ML & Full-Stack Developer | MLOps & Cloud

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?logo=linkedin)](https://www.linkedin.com/in/farzeen-abdul-khadir-8921ba2a1)

[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github)](https://github.com/farzeen-05)

[![Email](https://img.shields.io/badge/Email-farzeen99453@gmail.com-EA4335?style=flat&logo=gmail)](mailto:farzeen99453@gmail.com)


---

## License

This project is licensed under the MIT License.
