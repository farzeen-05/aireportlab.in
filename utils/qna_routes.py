"""
Add these routes to app.py for Q&A functionality.
Also add the /qna/<report_id> route for stored report Q&A.
"""

# ─── Add this import at top of app.py ────────────────────────────────────────
# from utils.llm_engine import answer_question

# ─── Live Q&A route (on current report page) ─────────────────────────────────

@app.route('/api/qna', methods=['POST'])
@login_required
def qna_live():
    """
    Live Q&A on the current uploaded document.
    Called from report.html via fetch().
    """
    from utils.llm_engine import answer_question

    data         = request.get_json()
    question     = data.get("question", "").strip()
    context      = data.get("context", "")       # text content
    file_type    = data.get("file_type", "")
    df_summary   = data.get("df_summary", None)
    chat_history = data.get("chat_history", [])

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    result = answer_question(
        question=question,
        context_text=context,
        file_type=file_type,
        df_summary=df_summary,
        chat_history=chat_history
    )

    return jsonify({
        "answer":     result["answer"],
        "confidence": result["confidence"],
        "question":   question
    })


# ─── Stored report Q&A route (from history) ──────────────────────────────────

@app.route('/api/qna/<int:report_id>', methods=['POST'])
@login_required
def qna_stored(report_id):
    """
    Q&A on a previously analyzed report stored in DB.
    Called from view_report.html via fetch().
    """
    from utils.llm_engine import answer_question

    data         = request.get_json()
    question     = data.get("question", "").strip()
    chat_history = data.get("chat_history", [])

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    # ── Fetch stored report context from DB ───────────────────────────────────
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT file_type, insights, key_insights, recommendations,
               structured_breakdown, ml_result, nlp_result
        FROM upload_history
        WHERE id = ? AND user_id = ?
    """, (report_id, session['user_id']))
    report = cursor.fetchone()
    conn.close()

    if not report:
        return jsonify({"error": "Report not found."}), 404

    report = dict(report)

    # ── Build context from stored fields ─────────────────────────────────────
    context_parts = []

    if report.get("insights"):
        context_parts.append(f"Executive Summary:\n{report['insights']}")

    if report.get("key_insights"):
        context_parts.append(f"Key Insights:\n{report['key_insights']}")

    if report.get("recommendations"):
        context_parts.append(f"Recommendations:\n{report['recommendations']}")

    if report.get("structured_breakdown"):
        context_parts.append(f"Detailed Breakdown:\n{report['structured_breakdown'][:2000]}")

    if report.get("ml_result"):
        context_parts.append(f"ML Analysis:\n{report['ml_result']}")

    if report.get("nlp_result"):
        context_parts.append(f"Keywords:\n{report['nlp_result']}")

    context_text = "\n\n".join(context_parts)

    result = answer_question(
        question=question,
        context_text=context_text,
        file_type=report.get("file_type", ""),
        chat_history=chat_history
    )

    return jsonify({
        "answer":     result["answer"],
        "confidence": result["confidence"],
        "question":   question
    })
