"""
utils/llm_engine.py
===================
Groq-powered LLM engine for:
1. Executive summary generation (text + tabular)
2. Page-wise summaries (text files)
3. Column-wise summaries (tabular files)
4. RAG-based Q&A (live + stored)
"""

import os
import json
import re
from groq import Groq

# ── Groq client ───────────────────────────────────────────────────────────────
_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        _client = Groq(api_key=api_key)
    return _client

MODEL = "openai/gpt-oss-20b"   # fast, free, 128K context (llama3-8b-8192 -> llama-3.1-8b-instant -> this, per console.groq.com/docs/deprecations)


def _call_groq(prompt, max_tokens=1024, system=None):
    """
    Call Groq API safely. Returns text or None on failure.
    """
    client = _get_client()
    if not client:
        return None
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def generate_llm_executive_summary(file_type, processed, template_summary,
                                   keywords=None, domain=None):
    """
    Generate an LLM-powered executive summary.
    Falls back to template_summary if Groq is unavailable.
    Returns: {"llm": "...", "template": "..."}
    """
    TABULAR = ['csv', 'excel', 'json_tabular']
    TEXT    = ['pdf', 'docx', 'txt', 'json_text']

    if file_type in TABULAR:
        df      = processed.get("cleaned_data")
        summary = processed.get("summary", {})
        roles   = summary.get("column_roles", {})

        if df is None:
            return {"llm": None, "template": template_summary}

        # Build a data snapshot for context
        num_cols  = roles.get("numeric_columns", [])[:5]
        cat_cols  = roles.get("categorical_columns", [])[:3]
        stats_str = ""
        for col in num_cols:
            try:
                stats_str += (
                    f"{col}: min={df[col].min():.2f}, "
                    f"max={df[col].max():.2f}, "
                    f"mean={df[col].mean():.2f}\n"
                )
            except Exception:
                pass

        sample = df.head(5).to_string(index=False)

        prompt = f"""You are a senior data analyst. Analyze this dataset and write a professional executive summary.

Dataset info:
- Rows: {len(df):,}, Columns: {len(df.columns)}
- Domain: {domain or 'general'}
- Numeric columns: {', '.join(num_cols)}
- Categorical columns: {', '.join(cat_cols)}

Key statistics:
{stats_str}

Sample data (first 5 rows):
{sample}

Write a 4-5 sentence executive summary that:
1. States what this dataset is about and its size
2. Identifies the most important numeric patterns or ranges
3. Highlights key categorical distributions
4. States what analysis this data is suitable for
5. Mentions any notable data quality observations

Be specific — use actual column names and numbers. Do NOT be generic."""

    elif file_type in TEXT:
        text     = processed.get("cleaned_text", "")[:3000]
        pages    = processed.get("raw_pages", [])
        kw_str   = ', '.join((keywords or [])[:10])

        prompt = f"""You are an expert document analyst. Write a professional executive summary for this document.

Document domain: {domain or 'general'}
Key topics identified: {kw_str}
Total pages: {len(pages)}
Content preview:
{text[:2500]}

Write a 4-5 sentence executive summary that:
1. States clearly what this document is about
2. Identifies the main topics and themes using specific terms from the content
3. Highlights the most important information or findings
4. States who would benefit from reading this document and why

Be specific — reference actual terms, names, or concepts from the content. Do NOT be generic."""
    else:
        return {"llm": None, "template": template_summary}

    llm_result = _call_groq(
        prompt,
        max_tokens=300,
        system="You are a professional data analyst and technical writer. Write concise, accurate, specific summaries."
    )

    return {
        "llm":      llm_result,
        "template": template_summary
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. PAGE-WISE SUMMARIES (text files)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_llm_page_summaries(pages, domain=None):
    """
    Generate LLM summaries for each page.
    Returns list of {page, llm_summary, template_summary}
    Batches pages to save API calls.
    """
    if not pages or not _get_client():
        return []

    results = []

    # Process pages in batches of 3 to save API calls
    batch_size = 3
    for batch_start in range(0, min(len(pages), 15), batch_size):
        batch = pages[batch_start:batch_start + batch_size]
        batch_text = ""
        for i, page in enumerate(batch):
            page_num = batch_start + i + 1
            # Strip repeated headers
            clean = '\n'.join(
                line for line in page.split('\n')
                if len(line.strip()) > 5
            )[:600]
            batch_text += f"\n--- PAGE {page_num} ---\n{clean}\n"

        prompt = f"""Summarize each page below in 2-3 sentences. Focus on the actual content, not formatting.
Domain: {domain or 'general'}

{batch_text}

Respond in JSON format:
{{"pages": [{{"page": 1, "summary": "..."}}, {{"page": 2, "summary": "..."}}]}}"""

        resp = _call_groq(prompt, max_tokens=400)
        if resp:
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', resp, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    for item in data.get("pages", []):
                        results.append({
                            "page":         item["page"],
                            "llm_summary":  item.get("summary", ""),
                        })
            except Exception:
                # Fallback — use raw response for first page of batch
                for i, page in enumerate(batch):
                    results.append({
                        "page":        batch_start + i + 1,
                        "llm_summary": resp[:200] if i == 0 else "",
                    })

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 3. COLUMN-WISE SUMMARIES (tabular files)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_llm_column_summaries(df, domain=None):
    """
    Generate LLM business-context summaries for each column.
    Returns dict {col_name: llm_summary}
    """
    if df is None or not _get_client():
        return {}

    import pandas as pd

    col_info = []
    for col in df.columns[:15]:  # limit to 15 cols
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            col_info.append(
                f"{col} (numeric): min={s.min():.2f}, max={s.max():.2f}, "
                f"mean={s.mean():.2f}, missing={s.isnull().sum()}"
            )
        else:
            top = s.value_counts().head(3).index.tolist()
            col_info.append(
                f"{col} (categorical): {s.nunique()} unique values, "
                f"top: {', '.join(str(v) for v in top)}, missing={s.isnull().sum()}"
            )

    prompt = f"""You are a data analyst. For each column below, write ONE sentence explaining:
- What this column represents in real-world terms
- Why it's important for analysis
- Any notable pattern

Dataset domain: {domain or 'general'}
Columns:
{chr(10).join(col_info)}

Respond in JSON:
{{"columns": [{{"name": "col_name", "insight": "one sentence insight"}}]}}"""

    resp = _call_groq(prompt, max_tokens=600)
    result = {}

    if resp:
        try:
            json_match = re.search(r'\{.*\}', resp, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for item in data.get("columns", []):
                    result[item["name"]] = item.get("insight", "")
        except Exception:
            pass

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. RAG Q&A
# ═══════════════════════════════════════════════════════════════════════════════

def answer_question(question, context_text, file_type, df_summary=None,
                    chat_history=None):
    """
    RAG-based Q&A using the document/dataset as context.

    Args:
        question:     User's question string
        context_text: Full document text OR dataset summary string
        file_type:    e.g. 'csv', 'pdf'
        df_summary:   Optional dict with dataset stats for tabular files
        chat_history: List of {"role": "user/assistant", "content": "..."}

    Returns: {"answer": "...", "confidence": "high/medium/low"}
    """
    TABULAR = ['csv', 'excel', 'json_tabular']

    if not _get_client():
        return {
            "answer":     "LLM is not configured. Please add GROQ_API_KEY to environment variables.",
            "confidence": "low"
        }

    # ── Build context ─────────────────────────────────────────────────────────
    if file_type in TABULAR and df_summary:
        context = f"""Dataset context:
- Rows: {df_summary.get('rows', 'N/A'):,}
- Columns: {df_summary.get('columns', 'N/A')}
- Column names: {', '.join(df_summary.get('column_names', []))}
- Numeric columns: {', '.join(df_summary.get('column_roles', {}).get('numeric_columns', []))}
- Categorical columns: {', '.join(df_summary.get('column_roles', {}).get('categorical_columns', []))}

Statistical summary:
{context_text[:3000]}"""
    else:
        context = context_text[:4000]

    # ── Build messages with history ───────────────────────────────────────────
    system_msg = """You are an intelligent document and data analyst assistant.
Answer questions based ONLY on the provided context.
If the answer is not in the context, say "I cannot find this information in the document."
Be specific, cite actual data points or quotes when possible.
Keep answers concise but complete."""

    messages = [{"role": "system", "content": system_msg}]

    # Add chat history (last 6 exchanges)
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({
                "role":    msg["role"],
                "content": msg["content"]
            })

    # Add current question with context
    messages.append({
        "role":    "user",
        "content": f"""Context:
{context}

Question: {question}

Answer based on the context above:"""
    })

    client = _get_client()
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.2,
        )
        answer = resp.choices[0].message.content.strip()

        # Estimate confidence
        low_confidence_phrases = [
            "cannot find", "not mentioned", "not in the",
            "don't know", "unclear", "not specified"
        ]
        confidence = "low" if any(
            p in answer.lower() for p in low_confidence_phrases
        ) else "high"

        return {"answer": answer, "confidence": confidence}

    except Exception as e:
        return {
            "answer":     f"Error generating answer: {str(e)}",
            "confidence": "low"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GENERATE SUGGESTED QUESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_suggested_questions(file_type, processed, domain=None):
    """
    Generate 5 smart suggested questions based on the document/dataset.
    Returns list of question strings.
    """
    TABULAR = ['csv', 'excel', 'json_tabular']

    if not _get_client():
        return _default_questions(file_type)

    if file_type in TABULAR:
        df    = processed.get("cleaned_data")
        roles = processed.get("summary", {}).get("column_roles", {})
        num   = roles.get("numeric_columns", [])[:3]
        cat   = roles.get("categorical_columns", [])[:2]

        prompt = f"""Generate 5 insightful questions a data analyst would ask about this dataset.

Domain: {domain or 'general'}
Numeric columns: {', '.join(num)}
Categorical columns: {', '.join(cat)}
Total rows: {len(df) if df is not None else 'N/A'}

Return JSON: {{"questions": ["question1", "question2", ...]}}
Questions should be specific to the column names above."""

    else:
        text = processed.get("cleaned_text", "")[:1500]
        prompt = f"""Generate 5 insightful questions someone would ask about this document.

Domain: {domain or 'general'}
Content preview: {text}

Return JSON: {{"questions": ["question1", "question2", ...]}}
Questions should be specific to the content above."""

    resp = _call_groq(prompt, max_tokens=300)

    if resp:
        try:
            json_match = re.search(r'\{.*\}', resp, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("questions", _default_questions(file_type))
        except Exception:
            pass

    return _default_questions(file_type)


def _default_questions(file_type):
    TABULAR = ['csv', 'excel', 'json_tabular']
    if file_type in TABULAR:
        return [
            "What are the key statistics of this dataset?",
            "Which columns have the most missing values?",
            "What are the most common values in categorical columns?",
            "What is the range of numeric columns?",
            "Are there any notable patterns in this data?",
        ]
    return [
        "What is the main topic of this document?",
        "What are the key findings or conclusions?",
        "Who is the target audience for this document?",
        "What recommendations are made?",
        "What methodology or approach is described?",
    ]
