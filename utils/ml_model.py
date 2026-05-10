from sklearn.ensemble import IsolationForest

def run_ml_analysis(file_type, processed):
    if file_type in ['csv', 'excel', 'json_tabular']:  # ← add json_tabular
        return detect_anomalies(processed)
    return None

def detect_anomalies(processed):
    df = processed["cleaned_data"].copy()
    roles = processed["summary"]["column_roles"]
    domain = processed["summary"].get("dataset_domain", "generic")

    numeric_cols = [col for col in roles["numeric_columns"] if col not in roles["id_columns"]]
    numeric_df = df[numeric_cols].copy()

    if numeric_df.empty:
        return {
            "ml_result": "No suitable numeric columns were available for machine learning analysis."
        }

    model = IsolationForest(contamination=0.05, random_state=42)
    predictions = model.fit_predict(numeric_df)

    anomaly_count = (predictions == -1).sum()
    total_records = len(df)
    anomaly_rate = round((anomaly_count / total_records) * 100, 2)

    domain_terms = {
        "real_estate": {
            "entity": "property records",
            "label": "unusual property patterns",
            "low": "The housing dataset appears stable with only minor pricing irregularities.",
            "moderate": "A moderate number of unusual property patterns were detected and may require valuation review.",
            "high": "A significant number of unusual property records were detected and should be reviewed for pricing inconsistencies."
        },
        "sales": {
            "entity": "sales records",
            "label": "unusual sales patterns",
            "low": "Sales activity appears stable with minimal irregular performance behavior.",
            "moderate": "A moderate level of unusual sales behavior was detected and may require selective review.",
            "high": "A significant number of unusual sales records were detected and should be investigated carefully."
        },
        "healthcare": {
            "entity": "patient records",
            "label": "unusual clinical patterns",
            "low": "Clinical observations appear stable with minimal irregular patient behavior.",
            "moderate": "A moderate number of unusual patient patterns were detected and may require clinical review.",
            "high": "A significant number of unusual patient records were detected and should be reviewed carefully."
        },
        "finance": {
            "entity": "transaction records",
            "label": "unusual transaction patterns",
            "low": "Financial activity appears stable with minimal irregular transaction behavior.",
            "moderate": "A moderate number of unusual transaction patterns were detected and may require risk review.",
            "high": "A significant number of unusual transaction records were detected and should be investigated carefully."
        },
        "logistics": {
            "entity": "shipment records",
            "label": "unusual operational patterns",
            "low": "Operational movement appears stable with minimal irregular logistics behavior.",
            "moderate": "A moderate number of unusual shipment patterns were detected and may require route review.",
            "high": "A significant number of unusual shipment records were detected and should be investigated carefully."
        },
        "generic": {
            "entity": "records",
            "label": "unusual patterns",
            "low": "The dataset appears stable with minimal irregular behavior.",
            "moderate": "A moderate level of unusual behavior was detected and may require selective review.",
            "high": "A significant number of irregular records were detected and should be investigated carefully."
        }
    }

    phrasing = domain_terms.get(domain, domain_terms["generic"])

    if anomaly_rate < 3:
        severity = "low"
        impact = phrasing["low"]
    elif anomaly_rate < 8:
        severity = "moderate"
        impact = phrasing["moderate"]
    else:
        severity = "high"
        impact = phrasing["high"]

    return {
        "ml_result": (
            f"Anomaly detection completed. {anomaly_count} unusual {phrasing['entity']} were identified out of "
            f"{total_records} total records ({anomaly_rate}% anomaly rate). "
            f"Anomaly severity is assessed as {severity}. {impact}"
        ),
        "anomaly_count": anomaly_count,
        "anomaly_rate": anomaly_rate,
        "risk_severity": severity
    }