import re


def detect_document_type(file_type, processed):
    """
    Detects the type of uploaded document so the correct
    summarization strategy can be applied.
    """

    # Tabular types — no text classification needed
    if file_type in ['csv', 'excel', 'json_tabular']:
        return "generic"

    # TXT — lightweight classification
    if file_type == 'txt':
        return _classify_text(processed)

    # JSON text (flattened key:value content)
    if file_type == 'json_text':
        return _classify_text(processed)

    # PDF / DOCX — full classification
    if file_type in ['pdf', 'docx']:
        return _classify_text(processed)

    return "generic"


def _classify_text(processed):
    text = processed.get("cleaned_text", "").lower()

    if not text:
        return "generic"

    research_signals = [
        "abstract", "introduction", "methodology", "literature review",
        "results", "discussion", "conclusion", "references",
        "proposed system", "experimental procedure"
    ]
    resume_signals = [
        "education", "skills", "experience", "projects",
        "certifications", "internship", "profile", "objective"
    ]
    business_signals = [
        "revenue", "sales", "profit", "market", "growth",
        "performance", "customer", "quarter", "forecast"
    ]
    legal_signals = [
        "agreement", "party", "terms", "conditions", "liability",
        "compliance", "policy", "contract", "obligation"
    ]

    def score(signals):
        return sum(1 for word in signals if word in text)

    scores = {
        "research_paper":  score(research_signals),
        "resume":          score(resume_signals),
        "business_report": score(business_signals),
        "legal_document":  score(legal_signals)
    }

    best_match = max(scores, key=scores.get)
    return best_match if scores[best_match] > 0 else "generic"