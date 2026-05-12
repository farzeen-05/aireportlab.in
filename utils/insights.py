import re
from collections import Counter


# ─── Domain-specific insight templates ───────────────────────────────────────

DOMAIN_CONFIG = {
    "academic": {
        "label":   "Academic / Educational Document",
        "summary": (
            "This academic document covers {topics}. "
            "It is structured across {pages} pages with {words:,} words, "
            "suitable for student review, exam preparation, and concept understanding."
        ),
        "insights": [
            "Document contains {pages} pages covering academic content.",
            "Key concepts identified: {topics}.",
            "Average page length: {avg_words} words — suitable for structured study.",
            "Content is organized for educational delivery and examination preparation.",
            "Top subject keywords: {keywords}.",
        ],
        "recommendations": [
            "Use the keyword list as a quick revision guide.",
            "Review page summaries before reading full content to save time.",
            "Focus on sections covering {top_keyword} for core understanding.",
            "Create flashcards from the top extracted keywords for exam preparation.",
        ]
    },

    "security": {
        "label":   "Cybersecurity / Network Security Document",
        "summary": (
            "This cybersecurity document discusses {topics} across {pages} pages. "
            "Key threat areas and security mechanisms are identified. "
            "The document is suitable for security professionals, students, and IT teams."
        ),
        "insights": [
            "Document spans {pages} pages with {words:,} words on security topics.",
            "Key threat areas identified: {topics}.",
            "Security mechanisms and countermeasures are discussed.",
            "Top security keywords: {keywords}.",
            "Content suitable for security audits, awareness training, and study.",
        ],
        "recommendations": [
            "Prioritize sections on {top_keyword} for immediate action.",
            "Cross-reference identified threats with your current security posture.",
            "Share relevant sections with IT and security teams.",
            "Use keyword list to identify gaps in your security policy.",
        ]
    },

    "medical": {
        "label":   "Medical / Healthcare Document",
        "summary": (
            "This medical document covers {topics} across {pages} pages with {words:,} words. "
            "Clinical content has been extracted and key medical terms identified. "
            "Suitable for healthcare professionals, researchers, and medical students."
        ),
        "insights": [
            "Document contains {pages} pages of medical/clinical content.",
            "Key medical topics: {topics}.",
            "Top clinical keywords: {keywords}.",
            "Content is structured for professional medical interpretation.",
            "Average section length: {avg_words} words.",
        ],
        "recommendations": [
            "Consult a qualified medical professional for clinical decisions.",
            "Use keyword index to locate specific conditions or treatments.",
            "Review diagnosis and treatment sections carefully.",
            "Cross-reference with latest clinical guidelines.",
        ]
    },

    "legal": {
        "label":   "Legal Document",
        "summary": (
            "This legal document covers {topics} across {pages} pages. "
            "Key clauses, obligations, and legal terms have been extracted. "
            "Professional legal review is recommended before acting on this document."
        ),
        "insights": [
            "Document spans {pages} pages of legal content with {words:,} words.",
            "Key legal topics identified: {topics}.",
            "Top legal terms: {keywords}.",
            "Document contains structured legal language requiring careful interpretation.",
            "Multiple sections identified covering rights, obligations and procedures.",
        ],
        "recommendations": [
            "Consult a qualified lawyer before making decisions based on this document.",
            "Pay special attention to sections on {top_keyword}.",
            "Identify all parties, dates, and obligations mentioned.",
            "Flag ambiguous clauses for legal clarification.",
        ]
    },

    "financial": {
        "label":   "Financial Document",
        "summary": (
            "This financial document covers {topics} across {pages} pages with {words:,} words. "
            "Key financial metrics, performance indicators, and fiscal data have been extracted."
        ),
        "insights": [
            "Document contains {pages} pages of financial content.",
            "Key financial topics: {topics}.",
            "Top financial terms: {keywords}.",
            "Content is suitable for financial review and performance analysis.",
            "Average section length: {avg_words} words.",
        ],
        "recommendations": [
            "Focus on {top_keyword} sections for key financial indicators.",
            "Cross-reference figures with supporting schedules and annexures.",
            "Consult a financial advisor for investment decisions.",
            "Use keyword extraction to quickly locate specific financial items.",
        ]
    },

    "research": {
        "label":   "Research Paper / Academic Paper",
        "summary": (
            "This research paper covers {topics} across {pages} pages with {words:,} words. "
            "Key research findings, methodology, and conclusions have been identified."
        ),
        "insights": [
            "Research document spans {pages} pages with {words:,} words.",
            "Core research topics: {topics}.",
            "Top research keywords: {keywords}.",
            "Paper contains structured research sections — abstract, methodology, findings.",
            "Suitable for literature review, citation analysis, and academic research.",
        ],
        "recommendations": [
            "Read the abstract and conclusion first for quick understanding.",
            "Focus on methodology section to evaluate research validity.",
            "Use keyword list to assess relevance to your research area.",
            "Cross-reference citations for further reading.",
        ]
    },

    "business": {
        "label":   "Business Document",
        "summary": (
            "This business document covers {topics} across {pages} pages with {words:,} words. "
            "Key business strategies, operational insights, and market information have been extracted."
        ),
        "insights": [
            "Document contains {pages} pages of business content.",
            "Key business topics: {topics}.",
            "Top business keywords: {keywords}.",
            "Content is suitable for strategic planning and business decision-making.",
            "Average section length: {avg_words} words.",
        ],
        "recommendations": [
            "Prioritize sections on {top_keyword} for strategic insights.",
            "Share with relevant department heads for aligned decision-making.",
            "Use extracted keywords to identify key business priorities.",
            "Review recommendations section for actionable next steps.",
        ]
    },

    "technology": {
        "label":   "Technology / Technical Document",
        "summary": (
            "This technical document covers {topics} across {pages} pages with {words:,} words. "
            "Key technical concepts, system components, and implementation details are identified."
        ),
        "insights": [
            "Technical document spans {pages} pages with {words:,} words.",
            "Core technical topics: {topics}.",
            "Top technical keywords: {keywords}.",
            "Content covers system architecture, implementation, and technical specifications.",
            "Suitable for developers, architects, and technical teams.",
        ],
        "recommendations": [
            "Focus on {top_keyword} sections for implementation guidance.",
            "Use keyword list as a technical glossary reference.",
            "Cross-reference with official documentation for accuracy.",
            "Share with development team for technical alignment.",
        ]
    },

    "hr": {
        "label":   "HR / Human Resources Document",
        "summary": (
            "This HR document covers {topics} across {pages} pages with {words:,} words. "
            "Key HR policies, employee guidelines, and workforce management content extracted."
        ),
        "insights": [
            "HR document contains {pages} pages with {words:,} words.",
            "Key HR topics: {topics}.",
            "Top HR keywords: {keywords}.",
            "Content covers employee policies, procedures, and HR guidelines.",
            "Suitable for HR teams, managers, and employees.",
        ],
        "recommendations": [
            "Ensure all employees are aware of policies on {top_keyword}.",
            "Review compliance requirements with HR leadership.",
            "Update policies based on current labor regulations.",
            "Use keyword extraction to quickly locate specific HR policies.",
        ]
    },

    "invoice": {
        "label":   "Invoice / Billing Document",
        "summary": (
            "This invoice document spans {pages} pages with {words:,} words. "
            "Key billing information, amounts, and payment terms have been extracted."
        ),
        "insights": [
            "Invoice document contains {pages} pages.",
            "Key billing terms identified: {keywords}.",
            "Document contains financial transaction details.",
            "Payment terms and amounts are the primary content.",
            "Suitable for accounts payable and financial reconciliation.",
        ],
        "recommendations": [
            "Verify all amounts and tax calculations before payment.",
            "Cross-reference with purchase orders and delivery receipts.",
            "Ensure payment due dates are noted and met.",
            "Archive invoice for financial audit purposes.",
        ]
    },

    "resume": {
        "label":   "Resume / CV Document",
        "summary": (
            "This resume/CV covers {topics} across {pages} pages with {words:,} words. "
            "Key skills, experience, and qualifications have been extracted."
        ),
        "insights": [
            "Resume spans {pages} pages with {words:,} words.",
            "Key profile areas: {topics}.",
            "Top skills and keywords: {keywords}.",
            "Document covers professional experience, education, and achievements.",
            "Suitable for HR screening, candidate evaluation, and ATS matching.",
        ],
        "recommendations": [
            "Match extracted keywords with job description requirements.",
            "Evaluate candidate strength in {top_keyword} area.",
            "Use keyword list for ATS compatibility scoring.",
            "Focus on achievements section for candidate assessment.",
        ]
    },

    "manual": {
        "label":   "User Manual / Guide Document",
        "summary": (
            "This manual covers {topics} across {pages} pages with {words:,} words. "
            "Step-by-step instructions, procedures, and operational guidance extracted."
        ),
        "insights": [
            "Manual spans {pages} pages with {words:,} words.",
            "Key operational topics: {topics}.",
            "Top procedural keywords: {keywords}.",
            "Content is structured as step-by-step instructions and guidelines.",
            "Suitable for end users, operators, and support teams.",
        ],
        "recommendations": [
            "Read safety and warning sections before operating.",
            "Follow procedures in sequence for {top_keyword}.",
            "Use keyword index to quickly find specific procedures.",
            "Keep manual accessible for reference during operation.",
        ]
    },

    "news": {
        "label":   "News / Media Document",
        "summary": (
            "This news document covers {topics} across {pages} pages with {words:,} words. "
            "Key events, statements, and news themes have been extracted."
        ),
        "insights": [
            "News document contains {pages} pages with {words:,} words.",
            "Key news topics: {topics}.",
            "Top news keywords: {keywords}.",
            "Content covers current events and news reporting.",
            "Suitable for media monitoring and news analysis.",
        ],
        "recommendations": [
            "Cross-reference with other news sources for balanced perspective.",
            "Focus on {top_keyword} for the main news angle.",
            "Verify facts with official sources before sharing.",
            "Use keyword extraction for topic tracking and monitoring.",
        ]
    },

    "government": {
        "label":   "Government / Policy Document",
        "summary": (
            "This government document covers {topics} across {pages} pages with {words:,} words. "
            "Key policies, regulations, and government directives have been extracted."
        ),
        "insights": [
            "Government document spans {pages} pages with {words:,} words.",
            "Key policy topics: {topics}.",
            "Top policy keywords: {keywords}.",
            "Content covers government regulations, schemes, and directives.",
            "Suitable for compliance review, policy analysis, and public administration.",
        ],
        "recommendations": [
            "Ensure compliance with regulations on {top_keyword}.",
            "Consult legal counsel for regulatory interpretation.",
            "Track implementation deadlines mentioned in the document.",
            "Share relevant sections with compliance and legal teams.",
        ]
    },

    "general": {
        "label":   "General Document",
        "summary": (
            "This document covers {topics} across {pages} pages with {words:,} words. "
            "Key themes and content have been extracted using NLP analysis."
        ),
        "insights": [
            "Document contains {pages} pages with {words:,} words.",
            "Key topics identified: {topics}.",
            "Top keywords: {keywords}.",
            "Content has been preprocessed and key terms extracted.",
            "Suitable for general review, summarization, and keyword analysis.",
        ],
        "recommendations": [
            "Use extracted keywords as a quick content overview.",
            "Review page summaries to navigate the document efficiently.",
            "Focus on {top_keyword} sections for core content.",
            "Cross-reference with related documents for deeper understanding.",
        ]
    },
}


# ─── TF-IDF keyword extractor ─────────────────────────────────────────────────

def extract_keywords_tfidf(text, n=15):
    """Extract top N keywords using TF-IDF scoring."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(
            max_features=n,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        vectorizer.fit_transform([text])
        return vectorizer.get_feature_names_out().tolist()
    except Exception:
        # Fallback to frequency-based
        import re
        from nltk.corpus import stopwords
        try:
            stops = set(stopwords.words('english'))
        except Exception:
            stops = set()
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        words = [w for w in words if w not in stops]
        freq  = Counter(words)
        return [w for w, _ in freq.most_common(n)]


def extract_topics(text, n=5):
    """Extract top N topic phrases (bigrams + single words)."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(
            max_features=n,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=1
        )
        vectorizer.fit_transform([text])
        return [t.title() for t in vectorizer.get_feature_names_out().tolist()]
    except Exception:
        return extract_keywords_tfidf(text, n)


def extract_headings(pages):
    """Extract section headings from page content."""
    headings = []
    for page in pages:
        lines = page.split('\n')
        for line in lines:
            line = line.strip()
            if (10 < len(line) < 100
                    and not line.endswith('.')
                    and not line.startswith('•')
                    and not line.startswith('-')
                    and sum(1 for c in line if c.isupper()) >= 3):
                headings.append(line)
    # Deduplicate
    seen = set()
    unique = []
    for h in headings:
        key = h[:30].lower()
        if key not in seen:
            seen.add(key)
            unique.append(h)
    return unique[:6]


# ─── Main insights generator ──────────────────────────────────────────────────

def generate_insights(file_type, processed, document_type=None):
    """
    Generates rich, domain-specific insights for any document type.
    Works for PDF, DOCX, TXT, JSON text, and tabular CSV/Excel.
    """

    # ── Tabular data ──────────────────────────────────────────────────────────
    if file_type in ['csv', 'excel', 'json_tabular']:
        return _generate_tabular_insights(processed)

    # ── Text-based documents ──────────────────────────────────────────────────
    text  = processed.get("cleaned_text", "")
    pages = processed.get("raw_pages", [])

    if not text.strip():
        return {
            "executive_summary": "No readable content could be extracted from this document.",
            "key_insights":      ["Document appears to be empty or unreadable."],
            "recommendations":   ["Try uploading a different version of the file."]
        }

    words     = text.split()
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 30]
    keywords  = extract_keywords_tfidf(text, 15)
    topics    = extract_topics(text, 5)
    headings  = extract_headings(pages)

    n_pages   = len(pages)
    n_words   = len(words)
    avg_words = n_words // max(n_pages, 1)
    top_kw    = keywords[0] if keywords else "the main topic"
    topics_str = ", ".join(topics[:4]) if topics else "various topics"
    kw_str     = ", ".join(keywords[:8]) if keywords else "extracted terms"

    # Get domain config
    domain = document_type or "general"
    config = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG["general"])

    # Fill templates
    fmt = dict(
        topics=topics_str,
        pages=n_pages,
        words=n_words,
        avg_words=avg_words,
        keywords=kw_str,
        top_keyword=top_kw,
    )

    executive_summary = config["summary"].format(**fmt)

    # Add heading context if available
    if headings:
        executive_summary += (
            f" Key sections include: {', '.join(headings[:3])}."
        )

    key_insights = []
    for tmpl in config["insights"]:
        try:
            key_insights.append(tmpl.format(**fmt))
        except Exception:
            key_insights.append(tmpl)

    # Add heading insight if available
    if headings:
        key_insights.append(
            f"Major sections identified: {', '.join(headings[:4])}."
        )

    recommendations = []
    for tmpl in config["recommendations"]:
        try:
            recommendations.append(tmpl.format(**fmt))
        except Exception:
            recommendations.append(tmpl)

    return {
        "executive_summary": executive_summary,
        "key_insights":      [i for i in key_insights if i],
        "recommendations":   [r for r in recommendations if r],
    }


# ─── Tabular insights ─────────────────────────────────────────────────────────

def _generate_tabular_insights(processed):
    """Generate insights for CSV/Excel/JSON tabular data."""
    import pandas as pd

    df      = processed.get("cleaned_data")
    summary = processed.get("summary", {})
    roles   = summary.get("column_roles", {})
    domain  = summary.get("dataset_domain", "generic")

    if df is None or df.empty:
        return {
            "executive_summary": "No data could be extracted from this file.",
            "key_insights":      ["File appears to be empty."],
            "recommendations":   ["Please upload a valid data file."]
        }

    n_rows   = len(df)
    n_cols   = len(df.columns)
    num_cols = roles.get("numeric_columns", [])
    cat_cols = roles.get("categorical_columns", [])
    dt_cols  = roles.get("date_columns", [])
    missing  = df.isnull().sum().sum()
    miss_pct = round((missing / max(df.size, 1)) * 100, 1)

    # Anomaly count from ml_result if available
    exec_summary = (
        f"This {domain} dataset contains {n_rows:,} records across {n_cols} attributes, "
        f"with primary numerical indicators including {', '.join(num_cols[:3])} "
        f"and category dimensions such as {', '.join(cat_cols[:2])}. "
        f"{'Time-based analysis is supported through ' + ', '.join(dt_cols[:2]) + '. ' if dt_cols else ''}"
        f"Data quality was improved through duplicate removal and missing-value treatment. "
        f"Missing values: {miss_pct}% of total data. "
        f"Overall, the dataset is suitable for trend analysis, segmentation, and performance monitoring."
    )

    insights = [
        f"The dataset includes {n_rows:,} rows and {n_cols} columns.",
        f"Key measurable metrics include {', '.join(num_cols[:3])}." if num_cols else "No numeric columns detected.",
        f"Primary segmentation dimensions include {', '.join(cat_cols[:3])}." if cat_cols else "No categorical columns detected.",
        f"Time-series analysis enabled through {', '.join(dt_cols[:2])}." if dt_cols else "No date columns detected.",
        f"Missing data rate: {miss_pct}% — {'minimal impact.' if miss_pct < 5 else 'requires attention.'}",
        "Duplicates were removed and missing values handled using datatype-aware preprocessing.",
    ]

    recommendations = [
        f"Prioritize metrics such as {', '.join(num_cols[:3])} for focused analysis." if num_cols else "Add numeric columns for quantitative analysis.",
        f"Use dimensions such as {', '.join(cat_cols[:2])} for segmentation and comparison." if cat_cols else "Add categorical columns for segmentation.",
        f"Use {dt_cols[0]} to monitor trends over time and improve forecasting accuracy." if dt_cols else "Add date columns to enable time-series analysis.",
        "Compare key numeric relationships to identify hidden trends and performance patterns.",
        "Consider segment-level aggregation to simplify analysis across large-scale records." if n_rows > 1000 else "Use caution when generalizing insights due to small dataset size.",
    ]

    return {
        "executive_summary": exec_summary,
        "key_insights":      [i for i in insights if i],
        "recommendations":   [r for r in recommendations if r],
    }
