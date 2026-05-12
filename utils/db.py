import mysql.connector
import os


# =========================
# DB CONNECTION
# =========================

def get_db_connection():

    return mysql.connector.connect(

        host=os.environ.get("MYSQLHOST"),

        user=os.environ.get("MYSQLUSER"),

        password=os.environ.get("MYSQLPASSWORD"),

        database=os.environ.get("MYSQLDATABASE"),

        port=int(os.environ.get("MYSQLPORT", 3306))

    )


# =========================
# PASSWORD RESET
# =========================

def save_reset_token(email, token, expiry):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET reset_token = %s,
            reset_token_expiry = %s
        WHERE email = %s
    """, (
        token,
        expiry,
        email
    ))

    conn.commit()

    affected = cursor.rowcount

    cursor.close()
    conn.close()

    return affected > 0


def get_user_by_reset_token(token):

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            email,
            reset_token_expiry
        FROM users
        WHERE reset_token = %s
        LIMIT 1
    """, (token,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def update_user_password(user_id, hashed_password):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password = %s,
            reset_token = NULL,
            reset_token_expiry = NULL
        WHERE id = %s
    """, (
        hashed_password,
        user_id
    ))

    conn.commit()

    cursor.close()
    conn.close()


# =========================
# CHECK EXISTING UPLOAD
# =========================

def check_existing_upload(file_name, file_size):

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id
        FROM upload_history
        WHERE file_name = %s
        AND file_size = %s
        ORDER BY id DESC
        LIMIT 1
    """, (
        file_name,
        file_size
    ))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


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
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s
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

    cursor.close()
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

    cursor = conn.cursor(dictionary=True)

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
            SET analysis_type = %s,
                report_format = %s,
                visual_charts = %s,
                created_at = CURRENT_TIMESTAMP
            WHERE id = %s
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

            VALUES (%s, %s, %s)
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

    cursor = conn.cursor(dictionary=True)

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

    cursor.close()
    conn.close()

    return settings


# =========================
# GET HISTORY
# =========================

def get_upload_history(user_id):

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM upload_history
        WHERE user_id = %s
        ORDER BY id DESC
    """, (user_id,))

    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return history
