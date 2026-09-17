"""
utils/insights.py
=================
Generates insights using TextAnalysisEngine (template)
+ Groq LLM for enhanced summaries.
Returns both versions so report.html can show both.
"""

try:
    from utils.text_analysis_engine import TextAnalysisEngine
except ImportError:
    from text_analysis_engine import TextAnalysisEngine
from utils.llm_engine import (
    generate_llm_executive_summary,
    generate_llm_page_summaries,
    generate_llm_column_summaries,
    generate_suggested_questions,
)

TABULAR_TYPES = ['csv', 'excel', 'json_tabular']
TEXT_TYPES    = ['pdf', 'docx', 'txt', 'json_text']

_engine = TextAnalysisEngine()


def generate_insights(file_type, processed):

    # ── Tabular ───────────────────────────────────────────────────────────────
    if file_type in TABULAR_TYPES:
        return _tabular_insights(file_type, processed)

    # ── Text ──────────────────────────────────────────────────────────────────
    elif file_type in TEXT_TYPES:
        return _text_insights(file_type, processed)

    return {"executive_summary": "", "key_insights": [], "recommendations": []}


# ── TABULAR ───────────────────────────────────────────────────────────────────

def _tabular_insights(file_type, processed):
    df      = processed.get("cleaned_data")
    summary = processed.get("summary", {})
    domain  = summary.get("dataset_domain", "generic")
    roles   = summary.get("column_roles", {})

    if df is None:
        return {"executive_summary": "", "key_insights": [], "recommendations": []}

    n_rows    = len(df)
    n_cols    = len(df.columns)
    num_cols  = roles.get("numeric_columns", [])
    cat_cols  = roles.get("categorical_columns", [])
    date_cols = roles.get("date_columns", [])

    # ── Template summary ──────────────────────────────────────────────────────
    template_summary = (
        f"This dataset contains {n_rows:,} records across {n_cols} attributes, "
        f"with primary key numerical indicators including {', '.join(num_cols[:3])} "
        f"and category dimensions such as {', '.join(cat_cols[:2])}. "
        f"{'Time-based analysis is supported through ' + date_cols[0] + '. ' if date_cols else ''}"
        f"Data quality was improved through duplicate removal, missing-value treatment, "
        f"and datatype standardization."
    )

    # ── LLM summary ──────────────────────────────────────────────────────────
    llm_result = generate_llm_executive_summary(
        file_type, processed, template_summary,
        keywords=num_cols + cat_cols, domain=domain
    )

    # ── LLM column insights ───────────────────────────────────────────────────
    llm_column_insights = generate_llm_column_summaries(df, domain=domain)

    # ── Suggested questions ───────────────────────────────────────────────────
    suggested_questions = generate_suggested_questions(file_type, processed, domain)

    # ── Key insights ──────────────────────────────────────────────────────────
    insights = [
        f"The dataset includes {n_rows:,} rows and {n_cols} columns.",
        f"Key measurable metrics include {', '.join(num_cols[:3])}." if num_cols else "",
        f"Primary segmentation dimensions include {', '.join(cat_cols[:2])}." if cat_cols else "",
        "Duplicates were removed and missing values were handled using datatype-aware preprocessing.",
        f"Trend analysis is supported through {date_cols[0]}." if date_cols else
        "The dataset is suitable for trend analysis, category comparison, and anomaly monitoring.",
    ]

    recommendations = [
        f"Prioritize metrics such as {', '.join(num_cols[:3])} for focused analysis." if num_cols else "",
        f"Use dimensions such as {', '.join(cat_cols[:2])} for segmentation and comparison." if cat_cols else "",
        "Compare key numeric relationships to identify hidden trends and performance patterns.",
        "Consider segment-level aggregation to simplify analysis across large-scale records.",
    ]

    return {
        "executive_summary":     llm_result.get("llm") or template_summary,
        "executive_summary_llm": llm_result.get("llm"),
        "executive_summary_template": template_summary,
        "key_insights":          [i for i in insights if i],
        "recommendations":       [r for r in recommendations if r],
        "llm_column_insights":   llm_column_insights,
        "suggested_questions":   suggested_questions,
        "domain":                domain,
    }


# ── TEXT ──────────────────────────────────────────────────────────────────────

def _text_insights(file_type, processed):
    text  = processed.get("cleaned_text", "")
    pages = processed.get("raw_pages", [])

    # ── TextAnalysisEngine (template) ────────────────────────────────────────
    result = _engine.run(text, pages)

    template_summary = result["executive_summary"]
    domain           = result["document_type"]
    keywords         = result["keywords"]

    # ── LLM executive summary ─────────────────────────────────────────────────
    llm_result = generate_llm_executive_summary(
        file_type, processed, template_summary,
        keywords=keywords, domain=domain
    )

    # ── LLM page summaries ────────────────────────────────────────────────────
    llm_pages = generate_llm_page_summaries(pages, domain=domain)
    llm_page_map = {item["page"]: item["llm_summary"] for item in llm_pages}

    # ── Suggested questions ───────────────────────────────────────────────────
    suggested_questions = generate_suggested_questions(file_type, processed, domain)

    return {
        "executive_summary":          llm_result.get("llm") or template_summary,
        "executive_summary_llm":      llm_result.get("llm"),
        "executive_summary_template": template_summary,
        "key_insights":               result["key_insights"],
        "recommendations":            result["recommendations"],
        "document_type":              domain,
        "keywords":                   keywords,
        "keyphrases":                 result["keyphrases"],
        "topics":                     result["topics"],
        "sentiment":                  result["sentiment"],
        "readability":                result["readability"],
        "statistics":                 result["statistics"],
        "sections":                   result["sections"],
        "llm_page_summaries":         llm_page_map,
        "suggested_questions":        suggested_questions,
    }
