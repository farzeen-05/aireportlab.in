import re


def extract_research_sections(text):
    """
    Extract key academic sections from research papers
    for contribution-aware summarization.
    """

    if not text:
        return {
            "abstract": "",
            "methodology": "",
            "results": "",
            "conclusion": ""
        }

    text = text.replace("\n", " ").lower()

    section_patterns = {
        "abstract": r"abstract[:\s](.*?)(introduction|1\.)",
        "methodology": r"(methodology|proposed system|experimental procedure)[:\s](.*?)(results|discussion|5\.)",
        "results": r"(results|results and discussion)[:\s](.*?)(conclusion|6\.)",
        "conclusion": r"conclusion[:\s](.*?)(references|acknowledgement|$)"
    }

    extracted = {}

    for section, pattern in section_patterns.items():
        match = re.search(pattern, text, re.DOTALL)

        if match:
            if section == "abstract":
                extracted[section] = match.group(1).strip()
            else:
                extracted[section] = match.group(2).strip()
        else:
            extracted[section] = ""

    return extracted


def clean_section_text(text, max_words=80, section_name=None):
    """
    Clean extracted research section text
    before summary generation.
    """

    if not text:
        return ""

    # Remove citations like [5], [12], (2024)
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\(\d{4}\)", "", text)

    # Remove figure/table references
    text = re.sub(r"(figure|fig|table)\s*\d+", "", text, flags=re.IGNORECASE)

    # Extra cleanup for noisy results section
    if section_name == "results":
        text = re.sub(r"\b[a-z]+ et al\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(mdpi|ieee|springer|elsevier)\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\b\d+\b", "", text)
        text = re.sub(r"\b(dataset|datasets|paper|study|studies)\b", "", text, flags=re.IGNORECASE)

    # Remove extra symbols / noisy characters
    text = re.sub(r"[^a-zA-Z0-9\s.,%-]", " ", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Keep first useful chunk only
    words = text.split()
    text = " ".join(words[:max_words])

    return text