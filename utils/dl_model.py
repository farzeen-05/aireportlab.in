"""
utils/dl_model.py
=================
Deep linguistic analysis using TextAnalysisEngine mathematical methods.
Performs: lexical diversity scoring, term weighting (TF-IDF mathematics),
multi-layer text feature extraction, and document complexity scoring.
"""

import re
import math
from collections import Counter
from text_analysis_engine import TextAnalysisEngine, _compute_tfidf, STOPWORDS

TEXT_TYPES    = ['pdf', 'docx', 'txt', 'json_text']
TABULAR_TYPES = ['csv', 'excel', 'json_tabular']

_engine = TextAnalysisEngine()


def run_dl_analysis(file_type, processed, document_type=None, research_sections=None):

    if file_type in TEXT_TYPES:
        text  = processed.get("cleaned_text", "")
        pages = processed.get("raw_pages", [])

        if not text:
            return {"dl_summary": "", "dl_result": ""}

        # ── Layer 1: TF-IDF weighted term extraction ──────────────────────────
        tfidf = _compute_tfidf(pages or [text])
        top_terms = list(tfidf.keys())[:10]

        # ── Layer 2: Lexical diversity score (vocabulary richness) ────────────
        words    = re.findall(r'\b[a-z]{3,}\b', text.lower())
        filtered = [w for w in words if w not in STOPWORDS]
        unique   = len(set(filtered))
        total    = len(filtered) or 1
        lex_diversity = round(unique / total, 3)

        # ── Layer 3: Term density scoring ────────────────────────────────────
        term_density = {}
        for term in top_terms[:5]:
            count = text.lower().count(term)
            density = round(count / (total / 1000), 2)  # per 1000 words
            term_density[term] = density

        # ── Layer 4: Sentence complexity scoring ─────────────────────────────
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        avg_len   = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        complexity = "High" if avg_len > 25 else "Medium" if avg_len > 15 else "Low"

        # ── Layer 5: Topic coherence score ───────────────────────────────────
        # Measures how consistently top terms appear across pages
        if len(pages) > 1:
            term_page_counts = Counter()
            for page in pages:
                page_words = set(re.findall(r'\b[a-z]{4,}\b', page.lower()))
                for term in top_terms:
                    if term in page_words:
                        term_page_counts[term] += 1
            coherence = round(
                sum(term_page_counts.values()) / (len(top_terms) * len(pages)), 3
            ) if top_terms else 0
        else:
            coherence = 1.0

        # ── Generate DL summary ───────────────────────────────────────────────
        dl_summary = (
            f"Deep linguistic analysis completed. "
            f"TF-IDF weighted key terms: {', '.join(top_terms[:5])}. "
            f"Lexical diversity score: {lex_diversity} "
            f"({'rich' if lex_diversity > 0.7 else 'moderate' if lex_diversity > 0.4 else 'repetitive'} vocabulary). "
            f"Sentence complexity: {complexity} (avg {avg_len:.0f} words/sentence). "
            f"Topic coherence across pages: {coherence:.2f} "
            f"({'strong' if coherence > 0.5 else 'moderate'} thematic consistency). "
            f"Dominant term density: {list(term_density.items())[0][0] if term_density else 'N/A'} "
            f"({list(term_density.values())[0] if term_density else 0} occurrences per 1000 words)."
        )

        return {
            "dl_summary":    dl_summary,
            "dl_result":     dl_summary,
            "top_terms":     top_terms,
            "lex_diversity": lex_diversity,
            "complexity":    complexity,
            "coherence":     coherence,
            "term_density":  term_density,
        }

    elif file_type in TABULAR_TYPES:
        # ── For tabular: anomaly detection using IQR mathematical method ──────
        df = processed.get("cleaned_data")
        if df is None:
            return {"dl_summary": "", "dl_result": ""}

        import pandas as pd
        numeric_cols = df.select_dtypes(include='number').columns.tolist()

        if not numeric_cols:
            return {"dl_summary": "No numeric columns for anomaly detection.", "dl_result": ""}

        # IQR-based anomaly detection (mathematical, no sklearn needed)
        anomaly_flags = pd.Series([False] * len(df))

        for col in numeric_cols[:5]:
            q1  = df[col].quantile(0.25)
            q3  = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            flags = (df[col] < lower) | (df[col] > upper)
            anomaly_flags = anomaly_flags | flags

        n_anomalies = int(anomaly_flags.sum())
        anomaly_pct = round(n_anomalies / len(df) * 100, 2)
        severity    = "low" if anomaly_pct < 3 else "moderate" if anomaly_pct < 10 else "high"

        severity_desc = {
            "low":      "The dataset is clean with minimal unusual records.",
            "moderate": "A moderate number of unusual patterns were detected and may require selective review.",
            "high":     "A significant number of anomalies detected — thorough data review recommended.",
        }.get(severity, "")

        dl_summary = (
            f"Anomaly detection completed. "
            f"{n_anomalies} unusual records were identified out of {len(df):,} total records "
            f"({anomaly_pct}% anomaly rate). "
            f"Anomaly severity is assessed as {severity}. "
            f"{severity_desc} "
            f"Overall, the dataset is suitable for clinical trend review, patient segmentation, "
            f"anomaly detection, and healthcare analysis."
            if "stroke" in " ".join(df.columns).lower()
            else
            f"Anomaly detection completed using IQR mathematical method. "
            f"{n_anomalies} unusual records were identified out of {len(df):,} total records "
            f"({anomaly_pct}% anomaly rate). Severity: {severity}. {severity_desc}"
        )

        return {
            "dl_summary": dl_summary,
            "dl_result":  dl_summary,
            "n_anomalies": n_anomalies,
            "anomaly_pct": anomaly_pct,
            "severity":    severity,
        }

    return {"dl_summary": "", "dl_result": ""}
