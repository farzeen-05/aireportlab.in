import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# PASSWORD RESET
# =========================

def save_reset_token(email, token, expiry):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET reset_token = ?, reset_token_expiry = ?
        WHERE email = ?
    """, (token, expiry, email))

    conn.commit()
    affected = cursor.rowcount

    cursor.close()
    conn.close()

    return affected > 0


def get_user_by_reset_token(token):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, email, reset_token_expiry
        FROM users
        WHERE reset_token = ?
        LIMIT 1
    """, (token,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return {
            "id": row[0],
            "email": row[1],
            "reset_token_expiry": row[2]
        }

    return None


def update_user_password(user_id, hashed_password):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password = ?, reset_token = NULL, reset_token_expiry = NULL
        WHERE id = ?
    """, (hashed_password, user_id))

    conn.commit()

    cursor.close()
    conn.close()


# =========================
# CHECK EXISTING UPLOAD
# =========================

def check_existing_upload(file_name, file_size):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM upload_history
        WHERE file_name = ? AND file_size = ?
        ORDER BY id DESC
        LIMIT 1
    """, (file_name, file_size))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row


# =========================
# SAVE UPLOAD HISTORY
# =========================

def save_upload_history(user_id, file_name, file_size, file_type, insights,
                        key_insights, recommendations, chart_data,
                        structured_breakdown, ml_result,
                        nlp_result, dl_result, pdf_report):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO upload_history
        (user_id, file_name, file_size, file_type,
         insights, key_insights, recommendations,
         chart_data, structured_breakdown,
         ml_result, nlp_result, dl_result, pdf_report)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        file_name,
        file_size,
        file_type,
        insights,
        key_insights,
        recommendations,
        chart_data,
        structured_breakdown,
        ml_result,
        nlp_result,
        dl_result,
        pdf_report
    ))

    conn.commit()

    saved_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return saved_id


# =========================
# SETTINGS
# =========================

def save_user_settings(analysis_type, report_format, visual_charts):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM app_settings
        ORDER BY id DESC
        LIMIT 1
    """)

    existing = cursor.fetchone()

    if existing:

        cursor.execute("""
            UPDATE app_settings
            SET analysis_type = ?,
                report_format = ?,
                visual_charts = ?,
                created_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            analysis_type,
            report_format,
            visual_charts,
            existing[0]
        ))

    else:

        cursor.execute("""
            INSERT INTO app_settings
            (analysis_type, report_format, visual_charts)

            VALUES (?, ?, ?)
        """, (
            analysis_type,
            report_format,
            visual_charts
        ))

    conn.commit()

    cursor.close()
    conn.close()


def get_user_settings():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT analysis_type, report_format, visual_charts
        FROM app_settings
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return {
            "analysis_type": row[0],
            "report_format": row[1],
            "visual_charts": row[2]
        }

    return None


# =========================
# GET HISTORY
# =========================

def get_upload_history(user_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM upload_history
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows