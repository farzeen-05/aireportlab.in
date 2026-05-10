import pandas as pd
import PyPDF2
import json
from docx import Document


def extract_file_content(file):
    filename = file.filename.lower()

    # ── CSV ───────────────────────────────────────────────────────────────────
    if filename.endswith('.csv'):
        for enc in ('utf-8', 'latin1', 'cp1252'):
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding=enc)
                return {"type": "csv", "content": df}
            except UnicodeDecodeError:
                continue
        file.seek(0)
        df = pd.read_csv(file, encoding='latin1', errors='replace')
        return {"type": "csv", "content": df}

    # ── EXCEL ─────────────────────────────────────────────────────────────────
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file)
        return {"type": "excel", "content": df}

    # ── PDF ───────────────────────────────────────────────────────────────────
    elif filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        pages, full_text = [], ""
        for page in pdf_reader.pages:
            page_text = (page.extract_text() or "").strip()
            if page_text:
                pages.append(page_text)
                full_text += page_text + "\n"
        return {"type": "pdf", "content": full_text, "pages": pages}

    # ── DOCX ──────────────────────────────────────────────────────────────────
    elif filename.endswith(('.doc', '.docx')):
        doc = Document(file)
        pages, full_text, chunk = [], "", []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                chunk.append(text)
                full_text += text + "\n"
                if len(chunk) >= 8:
                    pages.append(" ".join(chunk))
                    chunk = []
        if chunk:
            pages.append(" ".join(chunk))
        return {"type": "docx", "content": full_text, "pages": pages}

    # ── TXT ───────────────────────────────────────────────────────────────────
    elif filename.endswith('.txt'):
        for enc in ('utf-8', 'latin1'):
            try:
                file.seek(0)
                raw = file.read().decode(enc)
                break
            except UnicodeDecodeError:
                continue

        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        full_text = "\n".join(lines)
        pages = []
        for i in range(0, len(lines), 8):
            chunk = " ".join(lines[i:i + 8])
            if chunk:
                pages.append(chunk)
        return {"type": "txt", "content": full_text, "pages": pages}

    # ── JSON ──────────────────────────────────────────────────────────────────
    elif filename.endswith('.json'):
        for enc in ('utf-8', 'latin1'):
            try:
                file.seek(0)
                raw = file.read().decode(enc)
                break
            except UnicodeDecodeError:
                continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return {"type": "unknown", "content": None, "error": f"Invalid JSON: {e}"}

        # List of dicts → tabular (same pipeline as CSV)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            return {"type": "json_tabular", "content": df}

        # Single dict → flatten to readable text
        elif isinstance(data, dict):
            flat_text = _flatten_json_to_text(data)
            pages = []
            lines = flat_text.splitlines()
            for i in range(0, len(lines), 8):
                chunk = " ".join(lines[i:i + 8]).strip()
                if chunk:
                    pages.append(chunk)
            return {"type": "json_text", "content": flat_text, "pages": pages}

        else:
            flat_text = json.dumps(data, indent=2)
            return {"type": "json_text", "content": flat_text, "pages": [flat_text]}

    # ── UNKNOWN ───────────────────────────────────────────────────────────────
    else:
        return {"type": "unknown", "content": None}


def _flatten_json_to_text(data, prefix=""):
    lines = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            lines.extend(_flatten_json_to_text(value, prefix=full_key).splitlines())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    lines.extend(_flatten_json_to_text(item, prefix=f"{full_key}[{i}]").splitlines())
                else:
                    lines.append(f"{full_key}[{i}]: {item}")
        else:
            lines.append(f"{full_key}: {value}")
    return "\n".join(lines)