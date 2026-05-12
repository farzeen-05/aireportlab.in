def detect_document_type(file_type, processed):
    """
    Detects document type for any PDF/DOCX/TXT.
    Returns a specific domain string used by insights generator.
    """
    if file_type not in ['pdf', 'docx', 'txt', 'json_text']:
        return "tabular"

    text = processed.get("cleaned_text", "").lower()

    domains = {
        "academic":    ["module", "semester", "professor", "lecture", "syllabus",
                        "chapter", "unit", "exam", "assignment", "marks", "grade",
                        "course", "curriculum", "tutorial", "practicum", "viva"],

        "security":    ["security", "attack", "network", "virus", "malware",
                        "firewall", "encryption", "vulnerability", "threat",
                        "intrusion", "authentication", "cryptography", "hacking"],

        "medical":     ["patient", "disease", "treatment", "diagnosis", "hospital",
                        "clinical", "symptoms", "medication", "surgery", "therapy",
                        "prescription", "pathology", "anatomy", "physiology"],

        "legal":       ["clause", "agreement", "jurisdiction", "liability",
                        "contract", "plaintiff", "defendant", "judgment", "statute",
                        "regulation", "compliance", "attorney", "legal", "court"],

        "financial":   ["revenue", "profit", "balance", "investment", "fiscal",
                        "budget", "expense", "income", "assets", "liabilities",
                        "cashflow", "equity", "dividend", "audit", "financial"],

        "research":    ["abstract", "methodology", "conclusion", "references",
                        "hypothesis", "literature", "findings", "analysis",
                        "experiment", "results", "discussion", "citation"],

        "business":    ["company", "market", "strategy", "customer", "product",
                        "sales", "revenue", "growth", "operations", "management",
                        "stakeholder", "enterprise", "corporate", "business"],

        "technology":  ["software", "hardware", "algorithm", "database", "api",
                        "programming", "system", "architecture", "cloud", "server",
                        "code", "development", "deployment", "framework"],

        "hr":          ["employee", "recruitment", "salary", "performance",
                        "appraisal", "leave", "policy", "payroll", "benefits",
                        "onboarding", "training", "workforce", "hiring"],

        "government":  ["government", "policy", "ministry", "regulation", "act",
                        "parliament", "citizen", "public", "scheme", "authority",
                        "municipal", "gazette", "ordinance", "constitution"],

        "news":        ["according", "reported", "announced", "breaking", "sources",
                        "official", "press", "media", "journalist", "article",
                        "editorial", "coverage", "statement", "spokesperson"],

        "invoice":     ["invoice", "bill", "payment", "due", "amount", "gst",
                        "total", "subtotal", "tax", "vendor", "purchaser",
                        "quantity", "rate", "discount", "receipt"],

        "resume":      ["experience", "education", "skills", "objective",
                        "qualification", "internship", "project", "achievement",
                        "certification", "reference", "career", "profile"],

        "manual":      ["instructions", "steps", "procedure", "guide", "manual",
                        "how to", "setup", "install", "configure", "troubleshoot",
                        "warning", "caution", "note", "operation"],
    }

    scores = {}
    for domain, keywords in domains.items():
        scores[domain] = sum(1 for kw in keywords if kw in text)

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"
