"""
utils/breakdown.py
==================
Generates structured breakdown for all file types.
- Tabular: column-wise summary with stats
- Text:    executive-style per-page summary (not raw text)
"""

import re
import pandas as pd
from collections import Counter

TABULAR_TYPES = ['csv', 'excel', 'json_tabular']
TEXT_TYPES    = ['pdf', 'docx', 'txt', 'json_text']

STOPWORDS = set("""
i me my myself we our ours ourselves you your yours yourself yourselves
he him his himself she her hers herself it its itself they them their
theirs themselves what which who whom this that these those am is are
was were be been being have has had having do does did doing a an the
and but if or because as until while of at by for with about against
between into through during before after above below to from up down
in out on off over under again further then once here there when where
why how all both each few more most other some such no nor not only
own same so than too very s t can will just don should now d ll m o
re ve y ain aren couldn didn doesn hadn hasn haven isn ma mightn mustn
needn shan shouldn wasn weren won wouldn also would could page module
prof mangaluru pace sem figure table
""".split())


def generate_structured_breakdown(file_type, processed):

    # ── Tabular ───────────────────────────────────────────────────────────────
    if file_type in TABULAR_TYPES:
        return _column_breakdown(processed)

    # ── Text ──────────────────────────────────────────────────────────────────
    elif file_type in TEXT_TYPES:
        return _page_breakdown(processed)

    return []


# ── TABULAR breakdown ─────────────────────────────────────────────────────────

def _column_breakdown(processed):
    df = processed.get("cleaned_data")
    if df is None or df.empty:
        return []

    roles    = processed.get("summary", {}).get("column_roles", {})
    num_cols = roles.get("numeric_columns", [])
    cat_cols = roles.get("categorical_columns", [])
    dat_cols = roles.get("date_columns", [])
    id_cols  = roles.get("id_columns", [])

    breakdown = []
    for col in df.columns:
        col_data    = df[col]
        total       = len(col_data)
        missing     = col_data.isnull().sum()
        missing_pct = round((missing / total) * 100, 1) if total else 0
        unique      = col_data.nunique()

        col_label = col.replace('_', ' ').title()
        miss_text = f"No missing values detected." if missing_pct == 0 else f"{missing_pct}% of values are missing."

        if col in id_cols:
            col_type = "ID"
            summary  = (
                f"The {col_label} column is an identifier field with {unique} unique values. "
                f"It serves as a record key and is excluded from statistical analysis. "
                f"{miss_text}"
            )
        elif col in dat_cols:
            col_type = "DateTime"
            try:
                parsed    = pd.to_datetime(col_data.dropna())
                date_min  = parsed.min().date()
                date_max  = parsed.max().date()
                span_days = (parsed.max() - parsed.min()).days
                summary   = (
                    f"The {col_label} column is a time-based feature spanning {span_days} days, "
                    f"from {date_min} to {date_max}. "
                    f"It enables trend analysis, time-series forecasting, and temporal segmentation. "
                    f"{miss_text}"
                )
            except Exception:
                summary = (
                    f"The {col_label} column contains date or time values "
                    f"suitable for trend and time-series analysis. {miss_text}"
                )
        elif pd.api.types.is_numeric_dtype(col_data):
            col_type = "Numeric"
            mn   = col_data.min()
            mx   = col_data.max()
            mean = col_data.mean()
            std  = col_data.std()
            # Detect skew
            skew = col_data.skew() if hasattr(col_data, 'skew') else 0
            skew_text = (
                "The distribution is right-skewed, indicating a few high outliers." if skew > 1 else
                "The distribution is left-skewed, indicating a few low outliers."   if skew < -1 else
                "The distribution is approximately normal."
            )
            summary = (
                f"The {col_label} column is a numeric feature ranging from {mn:.2f} to {mx:.2f}, "
                f"with a mean of {mean:.2f} and standard deviation of {std:.2f}. "
                f"{skew_text} "
                f"It is suitable for statistical analysis, correlation studies, and trend monitoring. "
                f"{miss_text}"
            )
        else:
            col_type = "Categorical"
            top      = col_data.value_counts().head(3).index.tolist()
            top_str  = ', '.join(str(v) for v in top)
            pct_top  = round(col_data.value_counts().iloc[0] / len(col_data) * 100, 1) if len(col_data) > 0 else 0
            summary  = (
                f"The {col_label} column is a categorical feature with {unique} distinct values. "
                f"The most frequent values are {top_str}, with the dominant category accounting for {pct_top}% of records. "
                f"It is useful for segmentation, grouping, and comparative analysis. "
                f"{miss_text}"
            )

        breakdown.append({
            "column":          col,
            "type":            col_type,
            "missing_percent": missing_pct,
            "unique_values":   unique,
            "summary":         summary,
        })

    return breakdown


# ── TEXT / PAGE breakdown ─────────────────────────────────────────────────────

def _page_breakdown(processed):
    pages = processed.get("raw_pages", [])

    if not pages:
        text  = processed.get("cleaned_text", "")
        words = text.split()
        pages = [
            " ".join(words[i:i + 100])
            for i in range(0, len(words), 100)
            if words[i:i + 100]
        ]

    if not pages:
        return []

    # Detect repeated header (printed on every page — skip it)
    first_lines = []
    for page in pages:
        lines = page.strip().split('\n')
        if lines:
            first_lines.append(lines[0].strip()[:60])
    common = Counter(first_lines).most_common(1)
    header_skip = common[0][0] if common and common[0][1] > 2 else None

    breakdown = []

    for i, page_text in enumerate(pages, start=1):
        # ── Clean page text ───────────────────────────────────────────────────
        lines = page_text.strip().split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip repeated header
            if header_skip and header_skip in line[:80]:
                continue
            # Skip page numbers like "1", "- 2 -", "Page 3"
            if re.fullmatch(r'[\-–\s]*\d+[\-–\s]*', line):
                continue
            if re.fullmatch(r'[Pp]age\s*\d+', line):
                continue
            clean_lines.append(line)

        clean_text = ' '.join(clean_lines).strip()
        if not clean_text:
            continue

        # ── Extract heading ───────────────────────────────────────────────────
        heading = _extract_heading(clean_lines)

        # ── Extract key sentences ─────────────────────────────────────────────
        key_sentences = _extract_key_sentences(clean_text, n=2)

        # ── Extract keywords ──────────────────────────────────────────────────
        keywords = _extract_keywords(clean_text, top_n=5)

        # ── Build executive-style summary ─────────────────────────────────────
        word_count = len(clean_text.split())
        summary    = _build_page_summary(
            page_num=i,
            heading=heading,
            key_sentences=key_sentences,
            keywords=keywords,
            word_count=word_count
        )

        breakdown.append({
            "page":     i,
            "heading":  heading,
            "keywords": keywords,
            "summary":  summary,
        })

    return breakdown


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_heading(lines):
    """Find the most heading-like line on the page."""
    for line in lines[:8]:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        # Numbered heading: "1.2 Introduction" or "3. Methodology"
        if re.match(r'^\d+[\.\d]*\s+[A-Z]', line) and len(line) < 80:
            return line
        # ALL CAPS heading
        if line.isupper() and 5 < len(line) < 80:
            return line.title()
        # Title case heading (no period at end, reasonable length)
        if (line[0].isupper() and
                not line.endswith('.') and
                10 < len(line) < 70 and
                sum(1 for c in line if c.isupper()) >= 2):
            return line
    return None


def _extract_key_sentences(text, n=2):
    """
    Extract the most informative sentences using keyword density scoring.
    Returns up to n sentences.
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if 20 < len(s.strip()) < 300]

    if not sentences:
        return []

    # Score each sentence by keyword density
    all_words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    all_words = [w for w in all_words if w not in STOPWORDS]
    word_freq = Counter(all_words)

    scored = []
    for sent in sentences:
        words = re.findall(r'\b[a-z]{4,}\b', sent.lower())
        words = [w for w in words if w not in STOPWORDS]
        score = sum(word_freq.get(w, 0) for w in words) / max(len(words), 1)
        scored.append((score, sent))

    scored.sort(reverse=True)
    return [s for _, s in scored[:n]]


def _extract_keywords(text, top_n=5):
    """Extract top keywords from page text."""
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    words = [w for w in words if w not in STOPWORDS]
    freq  = Counter(words)
    return [w for w, _ in freq.most_common(top_n)]


def _build_page_summary(page_num, heading, key_sentences, keywords, word_count):
    """
    Build an executive-style summary for a single page.
    Format:
      [Heading if found] Key sentence 1. Key sentence 2.
      Topics covered: keyword1, keyword2, keyword3.
    """
    parts = []

    # Add heading context
    if heading:
        parts.append(f"This section covers '{heading}'.")

    # Add key sentences
    if key_sentences:
        parts.extend(key_sentences)
    elif word_count > 0:
        parts.append(f"This page contains {word_count} words of content.")

    # Add keyword summary
    if keywords:
        parts.append(f"Key topics: {', '.join(keywords)}.")

    summary = ' '.join(parts)

    # Trim if too long
    if len(summary) > 400:
        summary = summary[:397] + "..."

    return summary if summary else f"Page {page_num} — {word_count} words."
