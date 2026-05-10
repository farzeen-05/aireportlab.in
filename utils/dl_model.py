def run_dl_analysis(file_type, processed, document_type="generic", research_sections=None):
    if file_type in ['pdf', 'docx', 'txt', 'json_text']:  # ← add txt, json_text
        return generate_deep_summary(processed, document_type, research_sections)
    return None


def generate_deep_summary(processed, document_type="generic", research_sections=None):
    text = processed["cleaned_text"]

    if not text:
        return {
            "dl_summary": "No content available for deep learning summary.",
            "semantic_context": "No semantic interpretation available."
        }

    words = text.split()

    if len(words) < 30:
        return {
            "dl_summary": "Document is too short for deep learning summarization.",
            "semantic_context": "The uploaded content is too limited for reliable semantic interpretation."
        }

    # Research-aware summarization
    if document_type == "research_paper" and research_sections:
        abstract = research_sections.get("abstract", "")[:400]
        methodology = research_sections.get("methodology", "")[:300]
        results = research_sections.get("results", "")[:250]
        conclusion = research_sections.get("conclusion", "")[:250]

        summary_parts = []

        if abstract:
            summary_parts.append(f"Abstract: {abstract}")
        if methodology:
            summary_parts.append(f"Method: {methodology}")
        if results:
            summary_parts.append(f"Results: {results}")
        if conclusion:
            summary_parts.append(f"Conclusion: {conclusion}")

        summary = " ".join(summary_parts)

        return {
            "dl_summary": summary[:1200] + "...",
            "semantic_context": (
                "This document follows a research-oriented structure centered on problem definition, methodology, experimental findings, and technical contribution."
            )
        }

    # Generic content summary
    summary = " ".join(words[:80])

    semantic_context_map = {
        "business_report": (
            "This document emphasizes strategic priorities, operational performance, and business decision-making signals."
        ),
        "resume": (
            "This document reflects a professional candidate profile with emphasis on qualifications, competencies, and experience relevance."
        ),
        "legal_document": (
            "This document focuses on legal obligations, compliance interpretation, contractual language, and policy intent."
        ),
        "generic": (
            "The document contains structured thematic content with identifiable semantic context suitable for summarization."
        )
    }

    semantic_context = semantic_context_map.get(document_type, semantic_context_map["generic"])

    return {
        "dl_summary": summary + "...",
        "semantic_context": semantic_context
    }