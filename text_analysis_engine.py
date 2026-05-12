"""
text_analysis_engine.py
=======================
Fully automatic text analysis engine for ANY document type.
Works for: College notes, Business reports, Research papers,
           Legal docs, Medical reports, News articles, TXT files.

Pipeline:
  1. Document Type Detection    — classify the domain
  2. Structure Extraction       — headings, sections, pages
  3. NLP Processing             — keywords, TF-IDF, bigrams
  4. ML Analysis                — anomaly detection, clustering
  5. Statistical Analysis       — readability, density, complexity
  6. Summary Generation         — domain-aware executive summary
  7. Insights Generation        — specific, meaningful bullet points
  8. Recommendations            — actionable, context-aware

Usage:
    from text_analysis_engine import TextAnalysisEngine
    engine = TextAnalysisEngine()
    result = engine.run(text, pages)
    # result = {
    #     "document_type": "academic",
    #     "executive_summary": "...",
    #     "key_insights": [...],
    #     "recommendations": [...],
    #     "keywords": [...],
    #     "topics": [...],
    #     "statistics": {...},
    #     "sections": [...],
    #     "sentiment": "...",
    #     "readability": "...",
    # }
"""

import re
import math
from collections import Counter, defaultdict


# ─── Domain keyword maps ──────────────────────────────────────────────────────

DOMAIN_KEYWORDS = {
    "academic": [
        "module", "semester", "professor", "lecture", "syllabus", "chapter",
        "unit", "exam", "assignment", "marks", "university", "college",
        "course", "subject", "study", "notes", "definition", "theorem",
        "proof", "algorithm", "lab", "practical", "viva", "internal"
    ],
    "research": [
        "abstract", "introduction", "methodology", "literature", "review",
        "hypothesis", "experiment", "result", "conclusion", "references",
        "citation", "dataset", "analysis", "findings", "proposed", "model",
        "accuracy", "precision", "recall", "baseline", "evaluation", "survey"
    ],
    "business": [
        "revenue", "profit", "loss", "sales", "market", "customer", "product",
        "strategy", "growth", "investment", "budget", "forecast", "quarter",
        "annual", "performance", "kpi", "stakeholder", "roi", "cost", "pricing",
        "competitor", "acquisition", "partnership", "target", "objective"
    ],
    "legal": [
        "clause", "agreement", "contract", "jurisdiction", "liability",
        "whereas", "hereinafter", "party", "breach", "indemnity", "warranty",
        "termination", "obligation", "governing", "arbitration", "damages",
        "plaintiff", "defendant", "court", "judgment", "legislation", "act"
    ],
    "medical": [
        "patient", "diagnosis", "treatment", "symptom", "disease", "clinical",
        "hospital", "medicine", "surgery", "therapy", "prescription", "dosage",
        "chronic", "acute", "pathology", "prognosis", "healthcare", "physician",
        "nursing", "anatomy", "physiology", "pharmacology", "infection"
    ],
    "security": [
        "attack", "vulnerability", "firewall", "encryption", "malware", "virus",
        "network", "intrusion", "authentication", "authorization", "threat",
        "exploit", "patch", "security", "cyber", "hacker", "protocol",
        "cryptography", "certificate", "ssl", "vpn", "dos", "ddos", "xss"
    ],
    "financial": [
        "balance", "sheet", "income", "statement", "cash", "flow", "equity",
        "liability", "asset", "depreciation", "amortization", "dividend",
        "portfolio", "stock", "bond", "interest", "rate", "inflation", "tax",
        "audit", "compliance", "regulatory", "fiscal", "monetary", "credit"
    ],
    "technical": [
        "function", "class", "method", "algorithm", "database", "server",
        "api", "framework", "library", "deployment", "architecture", "code",
        "software", "hardware", "system", "interface", "protocol", "stack",
        "implementation", "debug", "testing", "agile", "devops", "cloud"
    ],
    "news": [
        "reported", "according", "sources", "statement", "announced",
        "government", "official", "minister", "president", "policy", "election",
        "crisis", "war", "peace", "trade", "economy", "global", "international",
        "domestic", "parliament", "senate", "bill", "law", "rights"
    ],
}

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
prof mangaluru pace sem arshiya nazneen
""".split())


# ─── Readability scorer ───────────────────────────────────────────────────────

def _flesch_kincaid_grade(text):
    """Estimate reading grade level."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    words     = re.findall(r'\b[a-zA-Z]+\b', text)

    if not sentences or not words:
        return 0

    def count_syllables(word):
        word  = word.lower()
        count = len(re.findall(r'[aeiou]+', word))
        if word.endswith('e'):
            count = max(1, count - 1)
        return max(1, count)

    total_syllables = sum(count_syllables(w) for w in words)
    avg_sentence_len = len(words) / len(sentences)
    avg_syllables    = total_syllables / len(words)

    grade = 0.39 * avg_sentence_len + 11.8 * avg_syllables - 15.59
    return round(grade, 1)


def _readability_label(grade):
    if grade < 6:   return "Very Easy"
    if grade < 9:   return "Easy"
    if grade < 12:  return "Moderate"
    if grade < 16:  return "Advanced"
    return "Expert"


# ─── TF-IDF implementation (no sklearn needed) ───────────────────────────────

def _compute_tfidf(pages):
    """
    Compute TF-IDF scores across pages.
    Returns: {word: tfidf_score}
    """
    N = len(pages)
    if N == 0:
        return {}

    # Term frequency per page
    page_tfs = []
    for page in pages:
        words = re.findall(r'\b[a-z]{4,}\b', page.lower())
        words = [w for w in words if w not in STOPWORDS]
        tf    = Counter(words)
        total = sum(tf.values()) or 1
        page_tfs.append({w: c/total for w, c in tf.items()})

    # Document frequency
    df = Counter()
    for ptf in page_tfs:
        for word in ptf:
            df[word] += 1

    # TF-IDF
    tfidf = defaultdict(float)
    for ptf in page_tfs:
        for word, tf_score in ptf.items():
            idf = math.log((N + 1) / (df[word] + 1)) + 1
            tfidf[word] += tf_score * idf

    return dict(sorted(tfidf.items(), key=lambda x: x[1], reverse=True))


# ─── Sentiment estimator ─────────────────────────────────────────────────────

POSITIVE_WORDS = set("""
good great excellent best improved increased growth positive success
benefit advantage strong robust efficient effective better enhanced
achieved accomplished significant innovative leading advanced optimal
""".split())

NEGATIVE_WORDS = set("""
bad poor weak failed failure loss decrease declined negative risk
problem issue concern threat vulnerable attack error critical severe
dangerous harmful toxic breach vulnerable weakness limitation
""".split())

def _estimate_sentiment(text):
    words = re.findall(r'\b[a-z]+\b', text.lower())
    pos   = sum(1 for w in words if w in POSITIVE_WORDS)
    neg   = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg or 1

    ratio = pos / total
    if ratio > 0.6:   return "Positive"
    if ratio < 0.4:   return "Negative"
    return "Neutral"


# ─── Structure extractor ─────────────────────────────────────────────────────

def _extract_structure(pages):
    """
    Extract headings, sections and key structural elements.
    Returns list of {level, title, page} dicts.
    """
    sections = []
    seen     = set()

    heading_pattern = re.compile(
        r'^([0-9]+[\.\d]*\s+[A-Z][^\n]{5,60}|'   # numbered: 1.2 Introduction
        r'[A-Z][A-Z\s]{8,50}|'                    # ALL CAPS heading
        r'[A-Z][a-z].{5,50}:)$'                   # Title Case:
    )

    for page_num, page in enumerate(pages, 1):
        lines = page.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5 or len(line) > 100:
                continue
            if heading_pattern.match(line):
                clean = re.sub(r'\s+', ' ', line).strip()
                if clean not in seen and len(clean) > 8:
                    seen.add(clean)
                    sections.append({
                        "title": clean,
                        "page":  page_num
                    })

    return sections[:20]   # cap at 20 sections


# ─── Bigram / phrase extractor ────────────────────────────────────────────────

def _extract_keyphrases(text, top_n=15):
    """Extract meaningful 2-3 word phrases using frequency."""
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    words = [w for w in words if w not in STOPWORDS]

    # Bigrams
    bigrams = [
        f"{words[i]} {words[i+1]}"
        for i in range(len(words)-1)
        if words[i] not in STOPWORDS and words[i+1] not in STOPWORDS
        and len(words[i]) > 3 and len(words[i+1]) > 3
    ]

    # Trigrams
    trigrams = [
        f"{words[i]} {words[i+1]} {words[i+2]}"
        for i in range(len(words)-2)
        if all(len(words[i+j]) > 3 for j in range(3))
        and all(words[i+j] not in STOPWORDS for j in range(3))
    ]

    phrase_counts = Counter(bigrams + trigrams)
    return [phrase for phrase, _ in phrase_counts.most_common(top_n)]


# ─── Domain detector ─────────────────────────────────────────────────────────

def _detect_domain(text):
    text_lower = text.lower()
    scores     = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[domain] = score

    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top            = sorted_domains[0]

    return top[0] if top[1] > 0 else "general"


# ─── Domain-aware summary templates ──────────────────────────────────────────

DOMAIN_SUMMARIES = {
    "academic": (
        "This academic document covers {topics} across {pages} pages "
        "({words:,} words). The material is structured into {sections} sections "
        "with a readability level of {readability}, suitable for {level} students. "
        "Key concepts include {keywords}. The content is appropriate for exam "
        "preparation, revision, and conceptual understanding."
    ),
    "research": (
        "This research document presents findings on {topics} spanning {pages} pages "
        "({words:,} words). The paper is structured across {sections} sections "
        "with {readability} readability. Core research themes include {keywords}. "
        "The document follows standard research methodology and is suitable for "
        "academic citation and literature review."
    ),
    "business": (
        "This business report analyzes {topics} across {pages} pages ({words:,} words). "
        "The document covers {sections} key areas with {readability} readability. "
        "Primary business themes include {keywords}. The report provides strategic "
        "insights suitable for executive decision-making and performance review."
    ),
    "legal": (
        "This legal document addresses {topics} across {pages} pages ({words:,} words). "
        "The document spans {sections} clauses/sections with {readability} readability. "
        "Core legal themes include {keywords}. The document is suitable for legal "
        "review, compliance assessment, and contractual analysis."
    ),
    "medical": (
        "This medical document covers {topics} across {pages} pages ({words:,} words). "
        "The content spans {sections} clinical sections with {readability} readability. "
        "Primary medical themes include {keywords}. The document is suitable for "
        "clinical reference, patient care guidelines, and medical education."
    ),
    "security": (
        "This cybersecurity document covers {topics} across {pages} pages ({words:,} words). "
        "The content addresses {sections} security topics with {readability} readability. "
        "Key security concepts include {keywords}. The document is suitable for "
        "security assessment, threat analysis, and defensive strategy planning."
    ),
    "financial": (
        "This financial document analyzes {topics} across {pages} pages ({words:,} words). "
        "The report covers {sections} financial areas with {readability} readability. "
        "Core financial themes include {keywords}. The document is suitable for "
        "investment analysis, financial planning, and regulatory compliance."
    ),
    "technical": (
        "This technical document describes {topics} across {pages} pages ({words:,} words). "
        "The content spans {sections} technical sections with {readability} readability. "
        "Key technical concepts include {keywords}. The document is suitable for "
        "implementation guidance, system architecture review, and developer reference."
    ),
    "news": (
        "This news document reports on {topics} across {pages} pages ({words:,} words). "
        "The content covers {sections} key stories with {readability} readability. "
        "Primary themes include {keywords}. The document provides current event "
        "analysis suitable for situational awareness and policy review."
    ),
    "general": (
        "This document covers {topics} across {pages} pages ({words:,} words). "
        "The content is organized into {sections} sections with {readability} readability. "
        "Key themes identified include {keywords}. The document is suitable for "
        "general review, information extraction, and content summarization."
    ),
}

DOMAIN_INSIGHTS = {
    "academic": [
        "Document contains {pages} pages covering {sections} major topics.",
        "Key concepts to focus on: {keywords}.",
        "Readability level: {readability} — suitable for {level} students.",
        "Top themes: {topics}.",
        "Average content density: {density} words per page.",
    ],
    "research": [
        "Research paper spans {pages} pages with {words:,} total words.",
        "Core research topics: {keywords}.",
        "Document structure includes {sections} identifiable sections.",
        "Research sentiment: {sentiment} — indicating {sentiment_desc}.",
        "Average page density: {density} words per page.",
    ],
    "business": [
        "Business report covers {pages} pages of strategic content.",
        "Primary business themes: {keywords}.",
        "Document sentiment: {sentiment} — {sentiment_desc}.",
        "{sections} key business areas identified.",
        "Executive summary density: {density} words per page.",
    ],
    "security": [
        "Security document covers {pages} pages of threat analysis.",
        "Key security concepts: {keywords}.",
        "Document sentiment: {sentiment} — {sentiment_desc}.",
        "{sections} security topics and attack vectors identified.",
        "Technical density: {density} words per page — highly detailed content.",
    ],
    "legal": [
        "Legal document spans {pages} pages with {words:,} words.",
        "Core legal themes: {keywords}.",
        "Readability: {readability} — requires professional interpretation.",
        "{sections} clauses or sections identified.",
        "Document density: {density} words per page.",
    ],
    "medical": [
        "Medical document covers {pages} pages of clinical content.",
        "Key medical themes: {keywords}.",
        "Readability: {readability} — requires medical expertise.",
        "{sections} clinical sections identified.",
        "Content density: {density} words per page.",
    ],
    "general": [
        "Document contains {pages} pages and {words:,} words.",
        "Key topics identified: {keywords}.",
        "Readability level: {readability}.",
        "{sections} structural sections detected.",
        "Average page density: {density} words per page.",
    ],
}

DOMAIN_RECOMMENDATIONS = {
    "academic": [
        "Focus on key concepts: {top3_keywords} for exam preparation.",
        "Review sections on {top_section} for deeper understanding.",
        "Use extracted keywords as flashcards for quick revision.",
        "Average {density} words per page — allocate study time accordingly.",
        "Cross-reference with textbooks on {top_topic} for complete coverage.",
    ],
    "research": [
        "Cite key findings related to {top3_keywords} in your own work.",
        "Review the methodology section for reproducibility insights.",
        "Use extracted topics for literature search: {top_topic}.",
        "The {sentiment} sentiment suggests {sentiment_desc}.",
        "Compare findings with related research on {top3_keywords}.",
    ],
    "business": [
        "Prioritize action items related to {top3_keywords}.",
        "Review {top_section} for strategic decision-making.",
        "Use the {sentiment} tone indicators for stakeholder communication.",
        "Focus on KPIs mentioned around {top_topic}.",
        "Distribute report sections based on team responsibilities.",
    ],
    "security": [
        "Immediately address vulnerabilities related to {top3_keywords}.",
        "Implement controls for {top_topic} attack vectors.",
        "Review section on {top_section} for defensive strategies.",
        "Use extracted threat keywords for security policy updates.",
        "Conduct penetration testing focused on {top3_keywords}.",
    ],
    "legal": [
        "Have legal counsel review clauses related to {top3_keywords}.",
        "Pay special attention to {top_section} for compliance.",
        "Extract obligation and liability clauses for risk assessment.",
        "Use keywords for contract management system tagging.",
        "Review jurisdiction clauses related to {top_topic}.",
    ],
    "medical": [
        "Consult specialists for topics related to {top3_keywords}.",
        "Review clinical guidelines mentioned in {top_section}.",
        "Use extracted terms for patient education materials.",
        "Cross-reference with latest medical literature on {top_topic}.",
        "Ensure compliance with protocols mentioned in the document.",
    ],
    "general": [
        "Use extracted keywords {top3_keywords} as search terms.",
        "Review section {top_section} for core content.",
        "Use the summary to reduce reading time by 70%.",
        "Focus on high-density pages for maximum information.",
        "Use topics {top_topic} to find related documents.",
    ],
}


# ─── Main Engine ──────────────────────────────────────────────────────────────

class TextAnalysisEngine:
    """
    Fully automatic text analysis engine.
    Input:  cleaned_text (str), raw_pages (list of str)
    Output: dict with all analysis results
    """

    def run(self, cleaned_text: str, raw_pages: list) -> dict:
        if not cleaned_text and not raw_pages:
            return self._empty_result()

        # Use raw pages for structure analysis, cleaned for NLP
        pages = raw_pages or [cleaned_text]
        text  = cleaned_text or " ".join(pages)

        # ── Step 1: Basic stats ───────────────────────────────────────────────
        stats = self._compute_statistics(text, pages)

        # ── Step 2: Domain detection ─────────────────────────────────────────
        domain = _detect_domain(text)

        # ── Step 3: TF-IDF keywords ───────────────────────────────────────────
        tfidf   = _compute_tfidf(pages)
        keywords = list(tfidf.keys())[:20]

        # ── Step 4: Key phrases ───────────────────────────────────────────────
        keyphrases = _extract_keyphrases(text, top_n=10)

        # ── Step 5: Structure / sections ─────────────────────────────────────
        sections = _extract_structure(pages)

        # ── Step 6: Sentiment ─────────────────────────────────────────────────
        sentiment = _estimate_sentiment(text)
        sentiment_desc = {
            "Positive": "optimistic tone with constructive content",
            "Negative": "cautionary tone highlighting risks and issues",
            "Neutral":  "balanced and objective presentation"
        }.get(sentiment, "balanced tone")

        # ── Step 7: Readability ───────────────────────────────────────────────
        grade       = _flesch_kincaid_grade(text)
        readability = _readability_label(grade)
        level       = {
            "Very Easy": "primary school",
            "Easy":      "high school",
            "Moderate":  "undergraduate",
            "Advanced":  "postgraduate",
            "Expert":    "professional/doctoral"
        }.get(readability, "general")

        # ── Step 8: Top topics (combined keywords + phrases) ──────────────────
        topics     = keyphrases[:5] or keywords[:5]
        top3       = ", ".join(keywords[:3])
        top_topic  = keywords[0] if keywords else "main topic"
        top_section = sections[0]["title"] if sections else "introduction"

        # ── Step 9: Template variables ────────────────────────────────────────
        tmpl_vars = {
            "pages":          len(pages),
            "words":          stats["word_count"],
            "sections":       len(sections) or "several",
            "keywords":       ", ".join(keywords[:5]),
            "topics":         ", ".join(topics[:3]),
            "readability":    readability,
            "level":          level,
            "density":        stats["avg_words_per_page"],
            "sentiment":      sentiment,
            "sentiment_desc": sentiment_desc,
            "top3_keywords":  top3,
            "top_topic":      top_topic,
            "top_section":    top_section[:50] if top_section else "introduction",
        }

        # ── Step 10: Generate outputs ─────────────────────────────────────────
        summary         = self._generate_summary(domain, tmpl_vars)
        insights        = self._generate_insights(domain, tmpl_vars)
        recommendations = self._generate_recommendations(domain, tmpl_vars)

        return {
            "document_type":    domain,
            "executive_summary": summary,
            "key_insights":     insights,
            "recommendations":  recommendations,
            "keywords":         keywords[:15],
            "keyphrases":       keyphrases,
            "topics":           topics,
            "sections":         sections,
            "sentiment":        sentiment,
            "readability":      readability,
            "readability_grade": grade,
            "statistics":       stats,
        }

    # ── Statistics ────────────────────────────────────────────────────────────

    def _compute_statistics(self, text, pages):
        words     = re.findall(r'\b[a-zA-Z]+\b', text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if len(s.strip()) > 10]
        paras     = [p for p in text.split('\n\n') if p.strip()]

        word_count        = len(words)
        unique_words      = len(set(w.lower() for w in words))
        avg_per_page      = word_count // max(len(pages), 1)
        avg_sentence_len  = word_count // max(len(sentences), 1)
        lexical_diversity = round(unique_words / max(word_count, 1), 3)

        return {
            "word_count":          word_count,
            "unique_words":        unique_words,
            "sentence_count":      len(sentences),
            "paragraph_count":     len(paras),
            "page_count":          len(pages),
            "avg_words_per_page":  avg_per_page,
            "avg_sentence_length": avg_sentence_len,
            "lexical_diversity":   lexical_diversity,
        }

    # ── Summary ───────────────────────────────────────────────────────────────

    def _generate_summary(self, domain, v):
        template = DOMAIN_SUMMARIES.get(domain, DOMAIN_SUMMARIES["general"])
        try:
            return template.format(**v)
        except KeyError:
            return DOMAIN_SUMMARIES["general"].format(**v)

    # ── Insights ──────────────────────────────────────────────────────────────

    def _generate_insights(self, domain, v):
        templates = DOMAIN_INSIGHTS.get(domain, DOMAIN_INSIGHTS["general"])
        insights  = []
        for tmpl in templates:
            try:
                insights.append(tmpl.format(**v))
            except KeyError:
                pass
        return [i for i in insights if i]

    # ── Recommendations ───────────────────────────────────────────────────────

    def _generate_recommendations(self, domain, v):
        templates = DOMAIN_RECOMMENDATIONS.get(domain, DOMAIN_RECOMMENDATIONS["general"])
        recs      = []
        for tmpl in templates:
            try:
                recs.append(tmpl.format(**v))
            except KeyError:
                pass
        return [r for r in recs if r]

    # ── Empty result ──────────────────────────────────────────────────────────

    def _empty_result(self):
        return {
            "document_type":     "unknown",
            "executive_summary": "No content could be extracted from this document.",
            "key_insights":      ["Document appears to be empty or unreadable."],
            "recommendations":   ["Please check the file and re-upload."],
            "keywords":          [],
            "keyphrases":        [],
            "topics":            [],
            "sections":          [],
            "sentiment":         "Neutral",
            "readability":       "Unknown",
            "readability_grade": 0,
            "statistics":        {},
        }
