"""
utils/insights.py — uses TextAnalysisEngine for text files
"""
from text_analysis_engine import TextAnalysisEngine

TABULAR_TYPES = ['csv', 'excel', 'json_tabular']
TEXT_TYPES    = ['pdf', 'docx', 'txt', 'json_text']
_engine       = TextAnalysisEngine()


def generate_insights(file_type, processed):
    if file_type in TABULAR_TYPES:
        return _tabular_insights(processed)
    elif file_type in TEXT_TYPES:
        text   = processed.get("cleaned_text", "")
        pages  = processed.get("raw_pages", [])
        result = _engine.run(text, pages)
        return {
            "executive_summary": result["executive_summary"],
            "key_insights":      result["key_insights"],
            "recommendations":   result["recommendations"],
            "document_type":     result["document_type"],
            "keywords":          result["keywords"],
            "keyphrases":        result["keyphrases"],
            "topics":            result["topics"],
            "sentiment":         result["sentiment"],
            "readability":       result["readability"],
            "statistics":        result["statistics"],
            "sections":          result["sections"],
        }
    return {"executive_summary": "", "key_insights": [], "recommendations": []}


def _tabular_insights(processed):
    df      = processed.get("cleaned_data")
    summary = processed.get("summary", {})
    domain  = summary.get("dataset_domain", "generic")
    roles   = summary.get("column_roles", {})
    if df is None:
        return {"executive_summary": "", "key_insights": [], "recommendations": []}
    n_rows   = len(df)
    n_cols   = len(df.columns)
    num_cols = roles.get("numeric_columns", [])
    cat_cols = roles.get("categorical_columns", [])
    date_cols= roles.get("date_columns", [])
    exec_summary = (
        f"This dataset contains {n_rows:,} records across {n_cols} attributes, "
        f"with primary key numerical indicators including {', '.join(num_cols[:3])} "
        f"and category dimensions such as {', '.join(cat_cols[:2])}. "
        f"{'Time-based analysis is supported through ' + date_cols[0] + '. ' if date_cols else ''}"
        f"Data quality was improved through duplicate removal, missing-value treatment, "
        f"and datatype standardization."
    )
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
        "executive_summary": exec_summary,
        "key_insights":      [i for i in insights if i],
        "recommendations":   [r for r in recommendations if r],
    }
