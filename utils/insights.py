def generate_insights(file_type, processed):
    if file_type in ['csv', 'excel','json_tabular']:
        return generate_tabular_insights(processed)
    elif file_type in ['pdf', 'docx','json_txt','txt']:
        return generate_text_insights(processed)
    else:
        return "No insights available."


def generate_tabular_insights(processed):
    summary = processed["summary"]
    roles = summary["column_roles"]

    rows = summary["rows"]
    cols = summary["columns"]

    numeric_cols = roles["numeric_columns"][:4]
    categorical_cols = roles["categorical_columns"][:3]
    date_cols = roles["date_columns"][:2]

    insight = (
        f"The uploaded dataset contains {rows} rows and {cols} columns, indicating a structured tabular dataset suitable for analytical processing. "
    )

    if numeric_cols:
        insight += f"Key measurable business metrics include {', '.join(numeric_cols)}. "

    if categorical_cols:
        insight += f"Important categorical dimensions include {', '.join(categorical_cols)}, enabling segmentation and comparative analysis. "

    if date_cols:
        insight += f"Temporal fields such as {', '.join(date_cols)} support trend and time-series evaluation. "

    if rows > 1000:
        insight += "This is a sufficiently large dataset to support trend discovery, anomaly detection, and business pattern analysis. "
    elif rows > 100:
        insight += "This is a moderately sized dataset suitable for structured analytical reporting. "
    else:
        insight += "This is a compact dataset suitable for focused exploratory analysis. "

    insight += (
        "The dataset has been cleaned, standardized, and prepared for downstream machine learning, visualization, and reporting workflows."
    )

    return insight


def generate_text_insights(processed):
    summary = processed["summary"]

    total_words = summary["total_words"]
    filtered_words = summary["filtered_words"]

    insight = (
        f"The uploaded document contains approximately {total_words} total words, of which {filtered_words} meaningful terms remain after preprocessing. "
    )

    if total_words > 1000:
        insight += "This is a content-rich document suitable for deeper semantic and thematic analysis. "
    elif total_words > 300:
        insight += "This document contains sufficient textual content for reliable keyword and contextual interpretation. "
    else:
        insight += "This is a shorter document suitable for lightweight text summarization and keyword extraction. "

    insight += (
        "The content has been normalized, cleaned, and prepared for semantic analysis, keyword extraction, and automated summarization."
    )

    return insight