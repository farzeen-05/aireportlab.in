import re
from collections import Counter

import nltk
nltk.download('punkt',     quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)


def run_nlp_analysis(file_type, processed, document_type=None):
    """
    Universal NLP analysis for any text document.
    Works for PDF, DOCX, TXT, JSON text.
    Returns keywords, summary sentences, and word stats.
    """
    if file_type not in ['pdf', 'docx', 'txt', 'json_text']:
        return None

    text  = processed.get("cleaned_text", "")
    pages = processed.get("raw_pages", [])

    if not text.strip():
        return {"keywords": [], "summary": "", "word_count": 0}

    # ── Keyword extraction using TF-IDF ───────────────────────────────────────
    keywords = _extract_keywords(text, n=20)

    # ── Extract meaningful sentences ──────────────────────────────────────────
    summary_sentences = _extract_summary_sentences(pages, n=5)

    # ── Word statistics ───────────────────────────────────────────────────────
    words          = text.split()
    total_words    = len(words)
    unique_words   = len(set(words))
    avg_word_len   = round(sum(len(w) for w in words) / max(len(words), 1), 1)

    # ── Sentence count ────────────────────────────────────────────────────────
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 20]

    # ── Top bigrams (2-word phrases) ──────────────────────────────────────────
    bigrams = _extract_bigrams(text, n=10)

    return {
        "keywords":          keywords,
        "bigrams":           bigrams,
        "summary_sentences": summary_sentences,
        "word_count":        total_words,
        "unique_words":      unique_words,
        "sentence_count":    len(sentences),
        "avg_word_length":   avg_word_len,
        "document_type":     document_type or "general",
    }


def _extract_keywords(text, n=20):
    """Extract top N keywords using TF-IDF with NLTK stopword fallback."""
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
        # Fallback to frequency-based extraction
        try:
            from nltk.corpus import stopwords
            stops = set(stopwords.words('english'))
        except Exception:
            stops = set()

        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        words = [w for w in words if w not in stops]
        freq  = Counter(words)
        return [w for w, _ in freq.most_common(n)]


def _extract_bigrams(text, n=10):
    """Extract top N meaningful bigram phrases."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(
            max_features=n,
            stop_words='english',
            ngram_range=(2, 2),
            min_df=1
        )
        vectorizer.fit_transform([text])
        return vectorizer.get_feature_names_out().tolist()
    except Exception:
        return []


def _extract_summary_sentences(pages, n=5):
    """
    Extract the most meaningful sentence from each page.
    Skips headers, page numbers, and short lines.
    """
    summaries = []

    # Detect repeated header (appears on every page — skip it)
    first_lines = []
    for page in pages:
        lines = page.strip().split('\n')
        if lines:
            first_lines.append(lines[0].strip()[:40])

    common = Counter(first_lines).most_common(1)
    skip_prefix = common[0][0][:25] if common and common[0][1] > 2 else None

    for page in pages[:n]:
        lines = page.strip().split('\n')
        for line in lines:
            line = line.strip()

            # Skip repeated headers
            if skip_prefix and line.startswith(skip_prefix):
                continue
            # Skip very short lines
            if len(line) < 40:
                continue
            # Skip lines that are ALL CAPS (likely headers)
            if line.isupper():
                continue
            # Skip lines with mostly numbers
            if sum(c.isdigit() for c in line) > len(line) * 0.4:
                continue
            # Skip bullet points and list markers
            if line.startswith(('•', '➢', '→', '-', '*', '►')):
                line = line[1:].strip()

            if len(line) > 40:
                summaries.append(line[:200])
                break

    return summaries
