import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT UNIQUE,
    password TEXT,
    reset_token TEXT,
    reset_token_expiry TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS upload_history (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    file_name TEXT,
    file_size INTEGER,
    file_type TEXT,

    insights TEXT,
    key_insights TEXT,
    recommendations TEXT,
    chart_data TEXT,
    structured_breakdown TEXT,

    ml_result TEXT,
    nlp_result TEXT,
    dl_result TEXT,

    pdf_report TEXT,

    upload_date TIMESTAMP DEFAULT (
        datetime('now', '+5 hours', '+30 minutes')
    )
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    analysis_type TEXT,
    report_format TEXT,
    visual_charts TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Database created successfully")