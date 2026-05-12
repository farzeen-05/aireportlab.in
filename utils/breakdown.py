import pandas as pd

TABULAR_TYPES = ['csv', 'excel', 'json_tabular']
TEXT_TYPES    = ['pdf', 'docx', 'txt', 'json_text']


def generate_structured_breakdown(file_type, processed):

    # ── Tabular: CSV / Excel / JSON (list of dicts) ───────────────────────────
    if file_type in TABULAR_TYPES:
        df = processed.get("cleaned_data")
        if df is None or df.empty:
            return []

        breakdown = []
        for col in df.columns:
            col_data    = df[col]
            total       = len(col_data)
            missing     = col_data.isnull().sum()
            missing_pct = round((missing / total) * 100, 1) if total else 0
            unique      = col_data.nunique()

            if pd.api.types.is_numeric_dtype(col_data):
                col_type = "Numeric"
                summary  = (
                    f"Min: {col_data.min():.2f}, "
                    f"Max: {col_data.max():.2f}, "
                    f"Mean: {col_data.mean():.2f}"
                )
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                col_type = "DateTime"
                summary  = f"Range: {col_data.min()} → {col_data.max()}"
            else:
                col_type = "Categorical"
                top      = col_data.value_counts().head(3).index.tolist()
                summary  = f"Top values: {', '.join(str(v) for v in top)}"

            breakdown.append({
                "column":          col,
                "type":            col_type,
                "missing_percent": missing_pct,
                "unique_values":   unique,
                "summary":         summary,
            })
        return breakdown

    # ── Text-based: PDF / DOCX / TXT / JSON (flat text) ─────────────────────
    elif file_type in TEXT_TYPES:
        pages = processed.get("raw_pages", [])

        # Fallback: split cleaned_text into chunks of 80 words
        if not pages:
            text  = processed.get("cleaned_text", "")
            words = text.split()
            pages = [
                " ".join(words[i:i + 80])
                for i in range(0, len(words), 80)
                if words[i:i + 80]
            ]

        breakdown = []
        for i, page_text in enumerate(pages, start=1):
            word_count = len(page_text.split())
            preview    = (page_text[:150] + "...") if len(page_text) > 150 else page_text
            breakdown.append({
                "page":    i,
                "summary": f"{preview} ({word_count} words)",
            })
        return breakdown

    return []
