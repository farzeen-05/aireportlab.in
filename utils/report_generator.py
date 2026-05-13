"""
utils/report_generator.py
=========================
Generates the final report by using insights directly from
TextAnalysisEngine (for text files) or tabular analysis (for CSV/Excel).
"""

TABULAR_TYPES = ['csv', 'excel', 'json_tabular']
TEXT_TYPES    = ['pdf', 'docx', 'txt', 'json_text']


def generate_final_report(file_type, processed, insights,
                           ml_output=None, nlp_output=None, dl_output=None,
                           document_type="generic", research_sections=None):
    report = {}

    # ── Tabular: CSV / Excel / JSON tabular ───────────────────────────────────
    if file_type in TABULAR_TYPES:
        report["executive_summary"] = generate_tabular_summary(processed, ml_output)
        report["key_insights"]      = generate_tabular_insights(processed)
        report["recommendations"]   = generate_tabular_recommendations(processed, ml_output)

    # ── Text: PDF / DOCX / TXT / JSON text ───────────────────────────────────
    elif file_type in TEXT_TYPES:
        # ── Use TextAnalysisEngine output directly ────────────────────────────
        # insights dict comes from generate_insights() which runs the engine
        exec_summary = insights.get("executive_summary", "")
        key_insights = insights.get("key_insights", [])
        recommendations = insights.get("recommendations", [])

        # ── Enrich with DL summary if available ──────────────────────────────
        if dl_output and dl_output.get("dl_summary"):
            dl_text = dl_output["dl_summary"]
            # Append DL analysis to executive summary
            if exec_summary and dl_text not in exec_summary:
                exec_summary = exec_summary.rstrip(".") + ". " + dl_text

        # ── Enrich insights with NLP output ──────────────────────────────────
        if nlp_output:
            # Add sentiment if not already in insights
            sentiment   = nlp_output.get("sentiment", "")
            readability = nlp_output.get("readability", "")
            keyphrases  = nlp_output.get("keyphrases", [])

            if sentiment and not any("sentiment" in i.lower() for i in key_insights):
                key_insights.append(
                    f"Document tone is {sentiment} with {readability} readability level."
                )
            if keyphrases and not any("phrase" in i.lower() for i in key_insights):
                key_insights.append(
                    f"Key phrases identified: {', '.join(keyphrases[:4])}."
                )

        # ── Research paper extra sections ─────────────────────────────────────
        if document_type == "research_paper" and research_sections:
            abstract    = research_sections.get("abstract", "")[:200]
            methodology = research_sections.get("methodology", "")[:150]
            results     = research_sections.get("results", "")[:150]

            if abstract and abstract not in exec_summary:
                exec_summary = exec_summary.rstrip(".") + f". Abstract: {abstract}."
            if methodology:
                key_insights.append(f"Methodology: {methodology[:100]}...")
            if results:
                key_insights.append(f"Key findings: {results[:100]}...")

        report["executive_summary"] = exec_summary
        report["key_insights"]      = [i for i in key_insights if i]
        report["recommendations"]   = [r for r in recommendations if r]

    return report


# ══════════════════════════════════════════════════════════════════════════════
# TABULAR FUNCTIONS (unchanged — already working well)
# ══════════════════════════════════════════════════════════════════════════════

def generate_tabular_summary(processed, ml_output):
    summary          = processed["summary"]
    roles            = summary["column_roles"]
    domain           = summary.get("dataset_domain", "generic")
    rows             = summary["rows"]
    cols             = summary["columns"]
    numeric_cols     = roles["numeric_columns"][:3]
    categorical_cols = roles["categorical_columns"][:2]
    date_cols        = roles["date_columns"][:1]

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
        f"This dataset contains {rows:,} records across {cols} attributes, "
        f"with primary {phrasing['metric_label']} including "
        f"{', '.join(numeric_cols) if numeric_cols else 'core measurable variables'} "
        f"and {phrasing['category_label']} such as "
        f"{', '.join(categorical_cols) if categorical_cols else 'key grouping fields'}. "
    )
    if date_cols:
        text += f"Time-based analysis is supported through {', '.join(date_cols)}. "
    text += "Data quality was improved through duplicate removal, missing-value treatment, and datatype standardization. "
    if ml_output and ml_output.get("ml_result"):
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
        f"The dataset includes {summary['rows']:,} rows and {summary['columns']} columns.",
        f"Key measurable metrics include {', '.join(numeric_cols)}." if numeric_cols else "",
        f"Primary segmentation dimensions include {', '.join(categorical_cols)}." if categorical_cols else
        f"Primary grouping fields: {domain_labels.get(domain, 'category fields')}.",
        "Duplicates were removed and missing values were handled using datatype-aware preprocessing.",
        f"Trend analysis is supported through {', '.join(date_cols)}." if date_cols else
        "The dataset is suitable for trend analysis, category comparison, and anomaly monitoring.",
    ]
    return [i for i in insights if i]


def generate_tabular_recommendations(processed, ml_output):
    summary          = processed["summary"]
    roles            = summary["column_roles"]
    domain           = summary.get("dataset_domain", "generic")
    numeric_cols     = roles["numeric_columns"][:3]
    categorical_cols = roles["categorical_columns"][:2]
    date_cols        = roles["date_columns"]

    recommendations = [
        f"Prioritize metrics such as {', '.join(numeric_cols) if numeric_cols else 'core numeric indicators'} for focused analysis.",
    ]
    if categorical_cols:
        recommendations.append(
            f"Use dimensions such as {', '.join(categorical_cols)} for segmentation and comparison."
        )
    if date_cols:
        recommendations.append(
            f"Use {date_cols[0]} to monitor trends over time and improve forecasting accuracy."
        )
    else:
        recommendations.append(
            "Compare key numeric relationships to identify hidden trends and performance patterns."
        )

    if summary["rows"] > 5000:
        recommendations.append(
            "Consider segment-level aggregation to simplify analysis across large-scale records."
        )
    elif summary["rows"] < 200:
        recommendations.append(
            "Use caution when generalizing insights due to the relatively small dataset size."
        )

    domain_recs = {
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
        ],
    }
    if domain in domain_recs:
        recommendations.extend(domain_recs[domain])

    if ml_output:
        anomaly_rate = ml_output.get("anomaly_rate", 0)
        if anomaly_rate >= 8:
            recommendations.append(
                "A high anomaly rate was detected; review flagged records before making critical decisions."
            )
        elif anomaly_rate >= 3:
            recommendations.append(
                "Review flagged anomalies to validate unusual patterns before action."
            )
        else:
            recommendations.append(
                "Only minor anomalies were detected, indicating relatively stable behavior."
            )

    return recommendations
