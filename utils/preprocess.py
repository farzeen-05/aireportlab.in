import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt',     quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

# All types that go through the text pipeline
TEXT_TYPES    = {'pdf', 'docx', 'txt', 'json_text'}

# All types that go through the tabular pipeline
TABULAR_TYPES = {'csv', 'excel', 'json_tabular'}


def preprocess_content(file_type, extracted):
    if file_type in TABULAR_TYPES:
        return preprocess_tabular(extracted["content"])
    elif file_type in TEXT_TYPES:
        return preprocess_text(extracted["content"], extracted.get("pages", []))
    return None


# ── TABULAR ───────────────────────────────────────────────────────────────────

def preprocess_tabular(df):
    df = df.copy()
    df.drop_duplicates(inplace=True)

    for col in df.columns:
        if pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].fillna(False).astype(str)
        else:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            if numeric_col.notna().sum() >= len(df[col]) * 0.5:
                df[col] = numeric_col
                df[col].fillna(df[col].mean(), inplace=True)
            else:
                df[col].fillna("Missing", inplace=True)

    column_roles   = detect_column_roles(df)
    dataset_domain = detect_dataset_domain(df)

    summary = {
        "rows":           df.shape[0],
        "columns":        df.shape[1],
        "column_names":   list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "column_roles":   column_roles,
        "dataset_domain": dataset_domain,
    }

    return {"cleaned_data": df, "summary": summary}


def detect_column_roles(df):
    roles = {
        "id_columns":          [],
        "numeric_columns":     [],
        "categorical_columns": [],
        "date_columns":        [],
        "text_columns":        [],
    }
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in ['id', 'ordernumber', 'customerid', 'phone', 'zipcode']):
            roles["id_columns"].append(col)
        elif 'date' in col_lower or 'time' in col_lower:
            roles["date_columns"].append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            roles["numeric_columns"].append(col)
        elif df[col].nunique() < 20:
            roles["categorical_columns"].append(col)
        else:
            roles["text_columns"].append(col)
    return roles


def detect_dataset_domain(df):
    joined = " ".join(col.lower() for col in df.columns)
    domain_keywords = {
        "real_estate": ["price", "house", "bedroom", "bathroom", "square_footage", "lot", "year_built", "property"],
        "sales":       ["sales", "revenue", "profit", "customer", "product", "order", "quantity", "discount"],
        "healthcare":  ["patient", "diagnosis", "hospital", "treatment", "disease", "age", "medical"],
        "finance":     ["transaction", "credit", "debit", "balance", "loan", "account", "payment", "risk"],
        "logistics":   ["delivery", "courier", "distance", "traffic", "weather", "shipment", "route"],
    }
    scores = {d: sum(1 for kw in kws if kw in joined) for d, kws in domain_keywords.items()}
    best   = max(scores, key=scores.get)
    return best if scores[best] > 0 else "generic"


# ── TEXT ──────────────────────────────────────────────────────────────────────

def preprocess_text(text, pages=None):
    if not text:
        return {"cleaned_text": "", "raw_pages": pages or [], "summary": {"total_words": 0, "filtered_words": 0}}

    text_lower = text.lower()
    text_clean = re.sub(r'[^a-zA-Z0-9\s]', '', text_lower)

    tokens      = word_tokenize(text_clean)
    stop_words  = set(stopwords.words('english'))
    filtered    = [w for w in tokens if w not in stop_words and len(w) > 1]
    cleaned_text = " ".join(filtered)

    return {
        "cleaned_text": cleaned_text,
        "raw_pages":    pages or [],
        "summary": {
            "total_words":    len(tokens),
            "filtered_words": len(filtered),
        },
    }