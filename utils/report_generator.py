def generate_final_report(file_type, processed, insights, ml_output=None, nlp_output=None, dl_output=None, document_type="generic", research_sections=None):
    report = {}

    if file_type in ['csv', 'excel', 'json_tabular']:
        report["executive_summary"] = generate_tabular_summary(processed, ml_output)
        report["key_insights"]      = generate_tabular_insights(processed)
        report["recommendations"]   = generate_tabular_recommendations(processed, ml_output)

    elif file_type in ['pdf', 'docx', 'txt', 'json_text']:
        report["executive_summary"] = generate_text_summary(processed, nlp_output, dl_output, document_type, research_sections)
        report["key_insights"]      = generate_text_insights(processed, nlp_output, document_type, research_sections)
        report["recommendations"]   = generate_text_recommendations(processed, nlp_output, document_type)

    return report


# ── TABULAR ────────────────────────────────────────────────────────────────────

def generate_tabular_summary(processed, ml_output):
    summary = processed["summary"]
    roles   = summary["column_roles"]
    domain  = summary.get("dataset_domain", "generic")

    rows           = summary["rows"]
    cols           = summary["columns"]
    numeric_cols   = roles["numeric_columns"][:3]
    categorical_cols = roles["categorical_columns"][:2]
    date_cols      = roles["date_columns"][:1]

    domain_phrases = {
        "real_estate": {
            "metric_label":   "property features",
            "category_label": "property segments",
            "closing":        "Overall, the dataset is suitable for pricing analysis, property comparison, valuation review, and housing trend analysis."
        },
        "sales": {
            "metric_label":   "sales and revenue metrics",
            "category_label": "business segments",
            "closing":        "Overall, the dataset is suitable for revenue monitoring, segmentation, sales performance review, and business trend analysis."
        },
        "healthcare": {
            "metric_label":   "clinical indicators",
            "category_label": "patient segments",
            "closing":        "Overall, the dataset is suitable for clinical trend review, patient segmentation, anomaly detection, and healthcare analysis."
        },
        "finance": {
            "metric_label":   "financial indicators",
            "category_label": "transaction segments",
            "closing":        "Overall, the dataset is suitable for financial monitoring, transaction review, anomaly detection, and risk analysis."
        },
        "logistics": {
            "metric_label":   "operational metrics",
            "category_label": "shipment segments",
            "closing":        "Overall, the dataset is suitable for logistics monitoring, route comparison, anomaly review, and operational trend analysis."
        },
        "generic": {
            "metric_label":   "key numerical indicators",
            "category_label": "category dimensions",
            "closing":        "Overall, the dataset is suitable for trend analysis, segmentation, anomaly review, and performance monitoring."
        }
    }

    phrasing = domain_phrases.get(domain, domain_phrases["generic"])

    text = (
        f"This dataset contains {rows} records across {cols} attributes, with primary {phrasing['metric_label']} including "
        f"{', '.join(numeric_cols) if numeric_cols else 'core measurable variables'} and {phrasing['category_label']} such as "
        f"{', '.join(categorical_cols) if categorical_cols else 'key grouping fields'}. "
    )
    if date_cols:
        text += f"Time-based analysis is supported through {', '.join(date_cols)}. "
    text += "Data quality was improved through duplicate removal, missing-value treatment, and datatype standardization. "
    if ml_output:
        text += f"{ml_output['ml_result']} "
    text += phrasing["closing"]
    return text


def generate_tabular_insights(processed):
    summary          = processed["summary"]
    roles            = summary["column_roles"]
    domain           = summary.get("dataset_domain", "generic")
    numeric_cols     = roles["numeric_columns"][:3]
    categorical_cols = roles["categorical_columns"][:2]
    date_cols        = roles["date_columns"][:1]

    domain_labels = {
        "real_estate": "property characteristics",
        "sales":       "business segments",
        "healthcare":  "patient groupings",
        "finance":     "transaction groupings",
        "logistics":   "shipment groupings",
        "generic":     "category fields"
    }

    insights = [
        f"The dataset includes {summary['rows']} rows and {summary['columns']} columns.",
        f"Key measurable metrics include {', '.join(numeric_cols) if numeric_cols else 'core numerical indicators'}.",
        f"Primary segmentation dimensions include {', '.join(categorical_cols) if categorical_cols else domain_labels.get(domain, 'category fields')}.",
        "Duplicates were removed and missing values were handled using datatype-aware preprocessing."
    ]
    if date_cols:
        insights.append(f"Trend analysis is supported through {', '.join(date_cols)}.")
    insights.append("The dataset is suitable for trend analysis, category comparison, and anomaly monitoring.")
    return insights


def generate_tabular_recommendations(processed, ml_output):
    summary          = processed["summary"]
    roles            = summary["column_roles"]
    domain           = summary.get("dataset_domain", "generic")
    numeric_cols     = roles["numeric_columns"][:3]
    categorical_cols = roles["categorical_columns"][:2]
    date_cols        = roles["date_columns"]

    recommendations = [
        f"Prioritize metrics such as {', '.join(numeric_cols) if numeric_cols else 'core numeric indicators'} for focused analysis."
    ]
    if categorical_cols:
        recommendations.append(f"Use dimensions such as {', '.join(categorical_cols)} for segmentation and comparison.")
    if date_cols:
        recommendations.append(f"Use {date_cols[0]} to monitor trends over time and improve forecasting accuracy.")
    else:
        recommendations.append("Compare key numeric relationships to identify hidden trends and performance patterns.")

    if summary["rows"] > 5000:
        recommendations.append("Consider segment-level aggregation to simplify analysis across large-scale records.")
    elif summary["rows"] < 200:
        recommendations.append("Use caution when generalizing insights due to the relatively small dataset size.")

    domain_recommendations = {
        "real_estate": [
            "Monitor property pricing patterns to identify valuation shifts and unusual listings.",
            "Compare housing attributes across property segments to improve pricing interpretation."
        ],
        "sales": [
            "Track revenue and sales behavior to identify high-performing segments.",
            "Use customer and product segmentation to improve sales strategy."
        ],
        "healthcare": [
            "Monitor clinical indicators to identify unusual patient patterns early.",
            "Use patient segmentation to improve care analysis and operational planning."
        ],
        "finance": [
            "Monitor transaction patterns to identify anomalies and emerging financial risk.",
            "Use account-level segmentation to improve financial review and risk monitoring."
        ],
        "logistics": [
            "Track operational movement to identify route inefficiencies and delays.",
            "Use shipment segmentation to improve logistics planning and execution."
        ]
    }
    if domain in domain_recommendations:
        recommendations.extend(domain_recommendations[domain])

    if ml_output:
        anomaly_rate = ml_output.get("anomaly_rate", 0)
        if anomaly_rate >= 8:
            recommendations.append("A high anomaly rate was detected; review flagged records before making critical decisions.")
        elif anomaly_rate >= 3:
            recommendations.append("Review flagged anomalies to validate unusual patterns before action.")
        else:
            recommendations.append("Only minor anomalies were detected, indicating relatively stable behavior.")

    return recommendations


# ── TEXT ───────────────────────────────────────────────────────────────────────

def generate_text_summary(processed, nlp_output, dl_output, document_type="generic", research_sections=None):
    summary        = processed["summary"]
    total_words    = summary["total_words"]
    filtered_words = summary["filtered_words"]

    if document_type == "research_paper":
        text = f"This research paper contains approximately {total_words} words, with {filtered_words} relevant terms retained after preprocessing. "
        if research_sections:
            abstract    = research_sections.get("abstract",    "")[:220]
            methodology = research_sections.get("methodology", "")[:180]
            results     = research_sections.get("results",     "")[:150]
            if abstract:    text += f"It focuses on {abstract}. "
            if methodology: text += f"The study proposes {methodology}. "
            if results:     text += f"Key findings suggest {results}. "
        text += "Overall, the document presents a structured technical contribution suitable for academic review, research interpretation, and rapid summarization."
        return text

    elif document_type == "business_report":
        text = (
            f"This business document contains approximately {total_words} words, with {filtered_words} relevant terms retained after preprocessing. "
            "The content highlights operational priorities, business performance, and decision-oriented insights. "
        )
        if nlp_output:
            text += f"Key themes include {', '.join(nlp_output['keywords'][:5])}. "
        text += "Overall, the report is suitable for executive review and business interpretation."
        return text

    elif document_type == "resume":
        text = f"This resume contains approximately {total_words} words and was analyzed for professional background, technical skills, and experience relevance. "
        if nlp_output:
            text += f"Key profile themes include {', '.join(nlp_output['keywords'][:5])}. "
        text += "Overall, the document is suitable for candidate screening and qualification review."
        return text

    elif document_type == "legal_document":
        text = f"This legal document contains approximately {total_words} words and was analyzed for obligations, compliance requirements, and policy interpretation. "
        if nlp_output:
            text += f"Key legal themes include {', '.join(nlp_output['keywords'][:5])}. "
        text += "Overall, the document is suitable for compliance review and legal interpretation."
        return text

    else:
        text = (
            f"The uploaded document contains approximately {total_words} words, with {filtered_words} relevant terms retained after preprocessing. "
            "The content was analyzed for thematic relevance, contextual meaning, and semantic structure. "
        )
        if nlp_output:
            text += f"Key themes include {', '.join(nlp_output['keywords'][:5])}. "
        text += "Overall, the document is suitable for rapid interpretation and structured summarization."
        return text


def generate_text_insights(processed, nlp_output, document_type="generic", research_sections=None):
    if document_type == "research_paper":
        insights = [
            "The document follows a research-oriented structure with technical and methodological content.",
            "The extracted content is suitable for academic summarization and contribution analysis.",
            "Text normalization improved technical keyword clarity and semantic interpretation."
        ]
        if research_sections:
            if research_sections.get("methodology"):
                insights.append("The paper includes a clearly identifiable methodology or proposed system section.")
            if research_sections.get("results"):
                insights.append("The paper includes measurable findings suitable for result-oriented interpretation.")

    elif document_type == "business_report":
        insights = [
            "The document is structured around business and operational themes.",
            "The extracted content is suitable for executive interpretation and performance review.",
            "Text normalization improved business keyword clarity and semantic interpretation."
        ]

    else:
        insights = [
            f"The processed document contains {processed['summary']['filtered_words']} relevant terms for semantic analysis.",
            "Text normalization improved keyword quality and contextual clarity.",
            "The content is suitable for thematic interpretation and summarization."
        ]

    if nlp_output:
        insights.append(f"Top extracted keywords include {', '.join(nlp_output['keywords'][:5])}.")

    return insights


def generate_text_recommendations(processed, nlp_output=None, document_type="generic"):
    summary        = processed["summary"]
    total_words    = summary.get("total_words", 0)
    filtered_words = summary.get("filtered_words", 0)

    keyword_density = round((filtered_words / total_words) * 100, 2) if total_words > 0 else 0

    recommendations = []

    if keyword_density < 35:
        recommendations.append("The document contains substantial filler content; focus on extracted keywords and summary for faster interpretation.")
    else:
        recommendations.append("The extracted keywords provide a strong signal of the document's core themes and intent.")

    if total_words > 3000:
        recommendations.append("Use the generated summary before reviewing the full document to reduce reading time.")
    elif total_words < 500:
        recommendations.append("The document is concise; review both summary and original text for full context.")

    if nlp_output and nlp_output.get("keywords"):
        recommendations.append(f"Focus on high-signal themes such as {', '.join(nlp_output['keywords'][:3])} for faster interpretation.")

    if document_type == "research_paper":
        recommendations.extend([
            "Review the methodology and results sections first to assess technical contribution quickly.",
            "Use extracted themes to accelerate academic review and literature comparison."
        ])
    elif document_type == "business_report":
        recommendations.extend([
            "Focus on operational themes to identify business priorities quickly.",
            "Use extracted signals to support faster executive decision-making."
        ])
    elif document_type == "resume":
        recommendations.extend([
            "Review technical skills and experience alignment before detailed screening.",
            "Use the summary to assess candidate fit quickly."
        ])
    elif document_type == "legal_document":
        recommendations.extend([
            "Review obligations and compliance clauses before full legal review.",
            "Use extracted legal themes to identify risk areas quickly."
        ])
    else:
        recommendations.extend([
            "Use the generated summary to assess document intent before full review.",
            "Review thematic highlights for faster interpretation and decision-making."
        ])

    return recommendations