# 🧠 aireportlab — AI-Powered Document & Dataset Analysis Platform

<div align="center">

![aireportlab Banner](https://img.shields.io/badge/aireportlab-AI%20Report%20Generator-1A4A8A?style=for-the-badge&logo=python&logoColor=white)

[![Live Demo](https://img.shields.io/badge/🌐%20Live%20Demo-aireportlab-1A4A8A?style=for-the-badge)](https://aireportlab-in-hzxn.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-farzeen--05-181717?style=for-the-badge&logo=github)](https://github.com/farzeen-05/aireportlab.in)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)

**Upload any file. Get a professional AI-generated report instantly.**  
*No coding required. No setup. Just upload and analyze.*

[🚀 Try Live Demo](https://aireportlab-in-hzxn.onrender.com) · [📸 Screenshots](#screenshots) · [⚙️ Features](#features) · [🛠️ Tech Stack](#tech-stack)

</div>

---

## 📌 Overview

**aireportlab** is a full-stack AI-powered web platform that automatically analyzes uploaded data files and documents, generating comprehensive analytical reports with visualizations, NLP insights, ML anomaly detection, and downloadable PDF reports — all without writing a single line of code.

> Built as a complete production-ready SaaS application with Google OAuth, email integration, cloud deployment, and a custom visualization engine.

---

## ✨ Features

### 📁 Multi-Format File Support
| Format | Analysis Type |
|--------|--------------|
| **CSV / Excel** | Statistical analysis, 15+ auto-generated charts, anomaly detection |
| **JSON** | Auto-detects tabular or text format, handles both pipelines |
| **PDF** | Text extraction, NLP summarization, page-wise breakdown |
| **DOCX** | Word document analysis, section extraction |
| **TXT** | Plain text summarization, keyword extraction |

### 📊 Custom Visualization Engine
- **Auto-detects column types** — Numeric, Categorical, Binary, DateTime, ID, Text
- **15+ chart types** generated automatically:
  - Distribution plots (Histogram + KDE + Box plot)
  - Correlation heatmaps
  - Trend / time-series charts
  - Pie + Bar categorical breakdowns
  - Violin plots (Binary vs Numeric)
  - Scatter plots (top correlated pairs)
  - Stacked bar charts (proportional)
- **Domain-specific charts** for Healthcare, Sales, Delivery, Weather datasets
- **Dataset Overview Card** — Missing values, column types, summary stats

### 🧠 AI Analysis Pipeline
- **ML** — IQR-based statistical anomaly detection
- **NLP** — TF-IDF keyword extraction, sentiment analysis, readability scoring (Flesch-Kincaid)
- **Deep Linguistic Analysis** — Lexical diversity, sentence complexity, topic coherence
- **Domain Detection** — 9 document types: Academic, Research, Business, Legal, Medical, Security, Financial, Technical, Resume

### 📄 Professional PDF Reports
- Executive Summary (domain-aware)
- Key Insights
- Visual Dashboard (embedded charts)
- Column-wise / Page-wise Breakdown
- Recommendations
- Stored as binary in database — no filesystem dependency

### 🔐 User Authentication
- Email/Password with bcrypt hashing
- **Google OAuth 2.0** single sign-on
- Forgot password with secure email reset (Resend API)
- Session management with Flask sessions

### 🗂️ Report History
- All reports saved per user
- View, download, and search previous reports
- Re-download PDF at any time

---

## 🖥️ Screenshots

> *(Add screenshots here after taking them)*

| Upload Page | Analysis Report | Visual Dashboard |
|-------------|----------------|-----------------|
| ![upload](screenshots/upload.png) | ![report](screenshots/report.png) | ![charts](screenshots/charts.png) |

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **Python 3.11+** | Core language |
| **Flask** | Web framework |
| **SQLite** | Database |
| **Gunicorn** | Production WSGI server |

### AI / Data Science
| Library | Purpose |
|---------|---------|
| **Pandas & NumPy** | Data processing and cleaning |
| **Matplotlib & Seaborn** | Chart generation |
| **Scikit-learn** | ML anomaly detection |
| **NLTK** | NLP tokenization, stopword removal |
| **ReportLab** | PDF generation |

### File Processing
| Library | Purpose |
|---------|---------|
| **PyPDF2** | PDF text extraction |
| **python-docx** | Word document reading |
| **openpyxl** | Excel file processing |

### Auth & Email
| Service | Purpose |
|---------|---------|
| **Authlib** | Google OAuth 2.0 |
| **Werkzeug** | Password hashing (bcrypt) |
| **Resend API** | Email delivery |

### Deployment
| Tool | Purpose |
|------|---------|
| **Render** | Cloud hosting |
| **GitHub** | Version control + auto-deploy |

---

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.11+
pip
Git
```

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/farzeen-05/aireportlab.in.git
cd aireportlab.in
```

**2. Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the project root:
```env
SECRET_KEY=your-random-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
RESEND_API_KEY=your-resend-api-key
```

**5. Initialize the database**
```bash
python init_db.py
```

**6. Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` 🎉

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
│   ├── insights.py             # AI insight generation
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

## 🔄 How It Works

```
📤 User uploads file
         ↓
🔍 File type detected (CSV/Excel/PDF/DOCX/JSON/TXT)
         ↓
📥 Raw content extracted (PyPDF2 / python-docx / pandas)
         ↓
🧹 Data preprocessed & cleaned
         ↓
┌─────────────────────────────────────┐
│         Analysis Pipeline           │
│  🤖 ML  → Anomaly detection (IQR)  │
│  📝 NLP → TF-IDF keywords, topics  │
│  🧮 DL  → Linguistic analysis      │
└─────────────────────────────────────┘
         ↓
📊 Visualization Engine generates 15+ charts
         ↓
📋 Report Generator assembles insights
         ↓
📄 PDF exported via ReportLab (stored as DB bytes)
         ↓
💾 Saved to SQLite database
         ↓
✅ Report displayed + available for download
```

---

## ⚙️ Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask session secret | ✅ |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | ✅ |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | ✅ |
| `RESEND_API_KEY` | Resend email API key | ✅ |

### Gunicorn (Production)
```python
# gunicorn.conf.py
workers = 1           # single worker (memory optimized)
threads = 2           # concurrent request handling
timeout = 120         # 2 minutes for large files
max_requests = 50     # auto-restart to prevent memory leaks
```

---

## 🌐 Deployment on Render

**1. Push to GitHub**
```bash
git add .
git commit -m "your message"
git push origin main
```

**2. Connect to Render**
- Go to [render.com](https://render.com)
- New Web Service → Connect GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --config gunicorn.conf.py`

**3. Add Environment Variables**
- Go to Render dashboard → Environment
- Add all variables from the table above

**4. Auto-deploys on every push** ✅

---

## 📊 Supported Dataset Domains

The visualization engine auto-detects and generates domain-specific charts for:

| Domain | Special Charts |
|--------|---------------|
| 🏥 Healthcare | Stroke by risk factors, BMI/Glucose violin plots |
| 📦 Logistics | Delivery time vs distance, traffic impact |
| 🌤️ Weather | Temperature range bands, precipitation trends |
| 💰 Sales | Revenue by product line, monthly trend, deal size |
| 🫁 Medical | Condition vs clinical indicators |

---

## 📝 Document Domains Detected

The Text Analysis Engine detects 9 document domains for context-aware summaries:

`Academic` · `Research` · `Business` · `Legal` · `Medical` · `Security` · `Financial` · `Technical` · `Resume`

---

## 🔒 Security Features

- ✅ Passwords hashed with **bcrypt** (Werkzeug)
- ✅ **Google OAuth 2.0** secure sign-in
- ✅ **Session-based** authentication
- ✅ Secure random **password reset tokens** (32-byte)
- ✅ Token expiry (1 hour)
- ✅ File type & size validation (max 10MB)
- ✅ Parameterized SQL queries (injection prevention)
- ✅ All secrets in **environment variables**

---

## 🤝 Contributing

Contributions are welcome!

```bash
# Fork the repo
# Create your feature branch
git checkout -b feature/AmazingFeature

# Commit your changes
git commit -m 'Add AmazingFeature'

# Push to branch
git push origin feature/AmazingFeature

# Open a Pull Request
```

---

## 📈 Future Enhancements

- [ ] BERT-based document summarization
- [ ] LSTM time-series forecasting
- [ ] Natural language dataset querying
- [ ] Real-time collaborative reports
- [ ] REST API for developers
- [ ] Mobile app (iOS/Android)
- [ ] Support for XML and SQL dump files
- [ ] Dashboard builder (drag-and-drop charts)

---

## 👩‍💻 Author

**Farzeen Abdul Khadir**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-farzeenabdul--khader-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/farzeenabdul-khader-8921ba2a1)
[![GitHub](https://img.shields.io/badge/GitHub-farzeen--05-181717?style=flat&logo=github)](https://github.com/farzeen-05)
[![Email](https://img.shields.io/badge/Email-farzeen98453@gmail.com-EA4335?style=flat&logo=gmail)](mailto:farzeen98453@gmail.com)

*Electronics & Communication Engineering Student | ML & Python Developer | IoT & Embedded Systems*

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**⭐ If you found this project helpful, please give it a star!**

Made with ❤️ by [Farzeen Abdul Khadir](https://github.com/farzeen-05)

[![Live Demo](https://img.shields.io/badge/🌐%20Try%20Live%20Demo-aireportlab-1A4A8A?style=for-the-badge)](https://aireportlab-in-hzxn.onrender.com)

</div>

