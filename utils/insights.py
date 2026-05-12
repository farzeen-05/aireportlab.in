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


def generate_insights(file_type, processed):
    if file_type in ['pdf', 'docx', 'txt', 'json_text']:
        text    = processed.get("cleaned_text", "")
        pages   = processed.get("raw_pages", [])
        words   = text.split()

        # Count sentences
        import re
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

        # Extract top bigrams (2-word phrases)
        from collections import Counter
        bigrams = []
        for i in range(len(words)-1):
            if len(words[i]) > 3 and len(words[i+1]) > 3:
                bigrams.append(f"{words[i]} {words[i+1]}")
        top_bigrams = [b for b, _ in Counter(bigrams).most_common(5)]

        # Get heading-like lines from pages
        headings = []
        for page in pages:
            lines = page.split('\n')
            for line in lines:
                line = line.strip()
                if (10 < len(line) < 80 and
                    not line.endswith('.') and
                    sum(1 for c in line if c.isupper()) > 3):
                    headings.append(line)
        headings = list(dict.fromkeys(headings))[:5]

        return {
            "executive_summary": (
                f"This document spans {len(pages)} pages with approximately "
                f"{len(words):,} words and {len(sentences)} key statements. "
                f"Core topics identified include: {', '.join(top_bigrams)}. "
                f"The content is structured around {len(headings)} major sections "
                f"and is suitable for academic or professional review."
            ),
            "key_insights": [
                f"Document contains {len(pages)} pages and {len(words):,} words.",
                f"Key topics: {', '.join(top_bigrams[:3])}." if top_bigrams else "",
                f"Major sections identified: {', '.join(headings[:3])}." if headings else "",
                f"Average section length: {len(words) // max(len(pages), 1)} words per page.",
                "Content suitable for summarization, keyword extraction and topic modeling.",
            ],
            "recommendations": [
                f"Focus on sections covering {top_bigrams[0]} for core understanding." if top_bigrams else "",
                "Use extracted keywords as a study guide or search index.",
                "Review page summaries to quickly navigate the document.",
                "Cross-reference with related documents for deeper analysis.",
            ]
        }
    
