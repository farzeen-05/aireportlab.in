from collections import Counter


def run_nlp_analysis(file_type, processed, document_type="generic"):
    if file_type in ['pdf', 'docx', 'txt', 'json_text']:  # ← add txt, json_text
        return extract_keywords(processed, document_type)
    return None

def extract_keywords(processed, document_type="generic"):
    text = processed["cleaned_text"]
    words = text.split()

    if not words:
        return {
            "keywords": [],
            "theme_summary": "No meaningful textual content was available for NLP analysis.",
            "keyword_density": 0
        }

    common_words = Counter(words).most_common(10)
    keywords = [word for word, count in common_words]

    total_words = len(words)
    keyword_density = round((sum(count for _, count in common_words) / total_words) * 100, 2)

    if keyword_density > 20:
        theme_strength = "high thematic concentration"
    elif keyword_density > 10:
        theme_strength = "moderate thematic concentration"
    else:
        theme_strength = "broad thematic spread"

    theme_templates = {
        "research_paper": (
            f"This research paper primarily focuses on {', '.join(keywords[:5])}, "
            f"indicating {theme_strength} around technical concepts, methodology, and research findings."
        ),
        "business_report": (
            f"This business report emphasizes {', '.join(keywords[:5])}, "
            f"reflecting {theme_strength} around operational priorities, business performance, and strategic themes."
        ),
        "resume": (
            f"This resume highlights {', '.join(keywords[:5])}, "
            f"indicating {theme_strength} around professional skills, experience, and candidate profile signals."
        ),
        "legal_document": (
            f"This legal document focuses on {', '.join(keywords[:5])}, "
            f"reflecting {theme_strength} across compliance obligations, policy interpretation, and legal clauses."
        ),
        "generic": (
            f"The document is primarily focused on {', '.join(keywords[:5])}, "
            f"indicating {theme_strength} across the extracted content."
        )
    }

    theme_summary = theme_templates.get(document_type, theme_templates["generic"])

    return {
        "keywords": keywords,
        "theme_summary": theme_summary,
        "keyword_density": keyword_density
    }