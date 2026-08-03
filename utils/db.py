import sqlite3
import os


# =========================
# DB CONNECTION
# =========================
DB_PATH = os.environ.get("SQLITE_DB_PATH", "aireportlab.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================
# DB INITIALIZATION
# =========================
def init_db():
    conn = get_db_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            username            TEXT NOT NULL,
            email               TEXT NOT NULL UNIQUE,
            password            TEXT NOT NULL,
            reset_token         TEXT DEFAULT NULL,
            reset_token_expiry  DATETIME DEFAULT NULL,
            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS upload_history (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id               INTEGER NOT NULL,
            file_name             TEXT NOT NULL,
            file_size             INTEGER,
            file_type             TEXT,
            insights              TEXT,
            key_insights          TEXT,
            recommendations       TEXT,
            chart_data            TEXT,
            structured_breakdown  TEXT,
            ml_result             TEXT,
            nlp_result            TEXT,
            dl_result             TEXT,
            pdf_report            BLOB,
            upload_date           DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_type  TEXT,
            report_format  TEXT,
            visual_charts  TEXT,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_upload_user_id ON upload_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(reset_token);
    """)
    conn.close()


# =========================
# PASSWORD RESET
# =========================

def save_reset_token(email, token, expiry):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET reset_token = ?,
            reset_token_expiry = ?
        WHERE email = ?
    """, (
        token,
        expiry,
        email
    ))

    conn.commit()

    affected = cursor.rowcount

    conn.close()

    return affected > 0


def get_user_by_reset_token(token):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            email,
            reset_token_expiry
        FROM users
        WHERE reset_token = ?
        LIMIT 1
    """, (token,))

    user = cursor.fetchone()

    conn.close()

    return dict(user) if user else None


def update_user_password(user_id, hashed_password):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password = ?,
            reset_token = NULL,
            reset_token_expiry = NULL
        WHERE id = ?
    """, (
        hashed_password,
        user_id
    ))

    conn.commit()

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
        WHERE file_name = ?
        AND file_size = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        file_name,
        file_size
    ))

    result = cursor.fetchone()

    conn.close()

    return dict(result) if result else None


# =========================
# SAVE UPLOAD HISTORY
# =========================

def save_upload_history(
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
):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO upload_history
        (
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
        )

        VALUES (
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?
        )
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

    conn.close()

    return saved_id


# =========================
# SETTINGS
# =========================

def save_user_settings(
    analysis_type,
    report_format,
    visual_charts
):

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
            existing["id"]
        ))

    else:

        cursor.execute("""
            INSERT INTO app_settings
            (
                analysis_type,
                report_format,
                visual_charts
            )

            VALUES (?, ?, ?)
        """, (
            analysis_type,
            report_format,
            visual_charts
        ))

    conn.commit()

    conn.close()


def get_user_settings():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            analysis_type,
            report_format,
            visual_charts

        FROM app_settings

        ORDER BY id DESC

        LIMIT 1
    """)

    settings = cursor.fetchone()

    conn.close()

    return dict(settings) if settings else None


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

    history = cursor.fetchall()

    conn.close()

    return [dict(row) for row in history]
