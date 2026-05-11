from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from utils.file_reader import extract_file_content
from utils.preprocess import preprocess_content
from utils.insights import generate_insights
from utils.ml_model import run_ml_analysis
from utils.nlp_model import run_nlp_analysis
from utils.dl_model import run_dl_analysis
from utils.db import (save_upload_history, get_upload_history,
                      check_existing_upload, save_user_settings, get_user_settings,
                      save_reset_token, get_user_by_reset_token, update_user_password)
from utils.breakdown import generate_structured_breakdown
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
from functools import wraps
from utils.report_generator import generate_final_report
from utils.export_report import export_pdf_report
from utils.document_classifier import detect_document_type
from utils.research_parser import extract_research_sections, clean_section_text
from visualization_engine import VisualizationEngine
import pandas as pd
import time
import os
import io
import json
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "9945")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# ─── File type groups ─────────────────────────────────────────────────────────
TABULAR_TYPES = ['csv', 'excel', 'json_tabular']
TEXT_TYPES    = ['pdf', 'docx', 'txt', 'json_text']

# ─── Mail config ──────────────────────────────────────────────────────────────
MAIL_USERNAME = "farz88928@gmail.com"
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")



# ─── Auth decorator ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ─── Chart helpers ────────────────────────────────────────────────────────────

def _read_dataframe(file):
    """Read uploaded FileStorage → DataFrame. UTF-8 with latin-1 fallback."""
    filename = file.filename.lower()
    raw = file.read()
    file.seek(0)
    try:
        if filename.endswith(".csv"):
            try:
                return pd.read_csv(io.BytesIO(raw))
            except UnicodeDecodeError:
                return pd.read_csv(io.BytesIO(raw), encoding="latin-1")
        elif filename.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(raw))
    except Exception:
        return None
    return None


def _run_visualization_engine(file_type, processed, file_obj=None):
    """
    Runs VisualizationEngine for tabular types.
    Returns dict {label: filepath} or None.
    """
    if file_type not in TABULAR_TYPES:
        return None

    df = processed.get("cleaned_data")
    if (df is None or (hasattr(df, "empty") and df.empty)) and file_obj is not None:
        df = _read_dataframe(file_obj)

    if df is None or (hasattr(df, "empty") and df.empty):
        return None

    try:
        engine = VisualizationEngine(output_dir="static/charts")
        return engine.run(df)
    except Exception as e:
        app.logger.warning(f"VisualizationEngine failed: {e}", exc_info=True)
        return None


def _parse_chart_paths(raw):
    """
    Convert DB-stored chart_data back into a dict the template can iterate.
      JSON string → dict  (new format)
      plain string → {"chart": path}  (legacy)
      None → None
    """
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return {"chart": raw}


def _to_list(value, sep=" || "):
    """Safely convert DB value → list. Works for list, string, or None."""
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [i.strip() for i in value.split(sep) if i.strip()]
    return [str(value)]


def _serialize_breakdown(structured_breakdown, file_type):
    """Serialize structured_breakdown list → single DB string."""
    if not structured_breakdown:
        return None
    rows = []
    for item in structured_breakdown:
        if file_type in TABULAR_TYPES:
            rows.append(
                f"{item['column']} ({item['type']}) - "
                f"Missing: {item['missing_percent']}%, "
                f"Unique: {item['unique_values']} - {item['summary']}"
            )
        else:
            rows.append(f"Page {item['page']} - {item['summary']}")
    return " || ".join(rows)


# ─── Mail helper ──────────────────────────────────────────────────────────────
def send_reset_email(to_email, reset_link):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset your aireportlab password"
        msg["From"]    = f"aireportlab <{MAIL_USERNAME}>"
        msg["To"]      = to_email
        html = f"""..."""
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, to_email, msg.as_string())

        app.logger.info(f"Email sent to {to_email}")

    except Exception as e:
        app.logger.error(f"SMTP crash: {type(e).__name__}: {e}")
        raise   # re-raise so forgot_password route can catch it



# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
@app.route('/landing')
def landing():
    return render_template('landing.html')


@app.route('/index')
@login_required
def index():

    records = get_upload_history(session['user_id'])

    total_uploads = len(records)

    total_reports = len([
        r for r in records
        if r["pdf_report"]
    ])

    recent_uploads = records[:5]

    return render_template(
        'index.html',
        total_uploads=total_uploads,
        total_reports=total_reports,
        recent_uploads=recent_uploads
    )

# ─── Upload ───────────────────────────────────────────────────────────────────

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']

        if not file or file.filename == '':
            flash("Please upload a file before submitting.", "warning")
            return redirect(request.url)

        allowed_extensions = {'csv', 'xlsx', 'xls', 'pdf', 'doc', 'docx', 'json', 'txt'}
        file_ext = file.filename.rsplit('.', 1)[-1].lower()

        if file_ext not in allowed_extensions:
            flash("Unsupported file format. Please upload CSV, Excel, PDF, DOCX, JSON, or TXT files only.", "danger")
            return redirect(request.url)

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > 10 * 1024 * 1024:
            flash("File is too large. Maximum allowed size is 10 MB.", "danger")
            return redirect(request.url)

        try:
            start_time = time.time()

            # ── Extract ───────────────────────────────────────────────────────
            try:
                extracted = extract_file_content(file)
            except Exception as extract_err:
                app.logger.error(f"File extraction failed: {extract_err}", exc_info=True)
                flash(f"Could not read file: {str(extract_err)}", "danger")
                return redirect(request.url)

            file_type    = extracted["type"]
            display_type = file_type.replace('_tabular', '').replace('_text', '')

            if file_type == 'unknown':
                flash("Could not read the file. Please check the format.", "danger")
                return redirect(request.url)

            if time.time() - start_time > 25:
                flash("File processing timed out. Please upload a smaller file.", "danger")
                return redirect(request.url)

            # ── Preprocess ────────────────────────────────────────────────────
            processed            = preprocess_content(file_type, extracted)
            structured_breakdown = generate_structured_breakdown(file_type, processed)

            if not processed:
                flash("The uploaded file could not be processed.", "danger")
                return redirect(request.url)

            if file_type in TABULAR_TYPES and processed["cleaned_data"].empty:
                flash("The uploaded file is empty or contains no usable data.", "warning")
                return redirect(request.url)

            if file_type in TEXT_TYPES and not processed.get("cleaned_text", "").strip():
                flash("The uploaded document contains no readable text.", "warning")
                return redirect(request.url)

            # ── Settings & document type ──────────────────────────────────────
            settings_data = get_user_settings()
            document_type = detect_document_type(file_type, processed)

            # ── Research sections (text only) ─────────────────────────────────
            research_sections = None
            if file_type in TEXT_TYPES and document_type == "research_paper":
                research_sections = extract_research_sections(processed["cleaned_text"])
                for key in research_sections:
                    research_sections[key] = clean_section_text(
                        research_sections[key], section_name=key
                    )

            insights = generate_insights(file_type, processed)

            # ── Visualizations (tabular only) ─────────────────────────────────
            chart_paths = None
            if not settings_data or settings_data.get("visual_charts") == "Enabled":
                chart_paths = _run_visualization_engine(file_type, processed, file_obj=file)

            # Single representative path for PDF export
            if isinstance(chart_paths, dict) and chart_paths:
                chart_path = chart_paths.get(
                    "dataset_overview",
                    next(iter(chart_paths.values()), None)
                )
            else:
                chart_path = None

            # ── ML / NLP / DL ─────────────────────────────────────────────────
            ml_output  = run_ml_analysis(file_type, processed) if file_type in TABULAR_TYPES else None
            nlp_output = run_nlp_analysis(file_type, processed, document_type) if file_type in TEXT_TYPES else None
            dl_output  = run_dl_analysis(file_type, processed, document_type, research_sections) if file_type in TEXT_TYPES else None

            # ── Final report ──────────────────────────────────────────────────
            final_report = generate_final_report(
                file_type, processed, insights,
                ml_output, nlp_output, dl_output,
                document_type, research_sections
            )

            if settings_data:
                selected_sections = settings_data.get("report_format", [])
                if isinstance(selected_sections, str):
                    selected_sections = [s.strip() for s in selected_sections.split(",")]

                if "Detailed Report" in selected_sections:
                    final_report["key_insights"]    = final_report.get("key_insights", [])[:5]
                    final_report["recommendations"] = final_report.get("recommendations", [])[:4]
                else:
                    if "Executive Summary"    not in selected_sections:
                        final_report["executive_summary"] = ""
                    if "Key Insights"         not in selected_sections:
                        final_report["key_insights"] = []
                    if "Structured Breakdown" not in selected_sections:
                        structured_breakdown = []
                    if "Recommendations"      not in selected_sections:
                        final_report["recommendations"] = []

            # ── PDF export ────────────────────────────────────────────────────
            pdf_report = export_pdf_report(
                final_report,
                display_type,
                file.filename.rsplit(".", 1)[0],
                chart_paths if isinstance(chart_paths, dict) else {},
                structured_breakdown
            )

            # ── Save to DB ────────────────────────────────────────────────────
            report_id = save_upload_history(
                session['user_id'],
                file.filename,
                file_size,
                file_type,
                final_report.get("executive_summary"),
                " || ".join(final_report.get("key_insights", []))
                    if final_report.get("key_insights") else None,
                " || ".join(final_report.get("recommendations", []))
                    if final_report.get("recommendations") else None,
                json.dumps(chart_paths) if isinstance(chart_paths, dict) else chart_paths,
                _serialize_breakdown(structured_breakdown, file_type),
                ml_output.get("ml_result")                if ml_output  else None,
                ", ".join(nlp_output.get("keywords", [])) if nlp_output else None,
                dl_output.get("dl_summary")               if dl_output  else None,
                pdf_report
            )

            return render_template(
                'report.html',
                result=extracted,
                processed=processed,
                chart_path=chart_path,
                chart_paths=chart_paths,
                final_report=final_report,
                structured_breakdown=structured_breakdown,
                report_id=report_id,
                pdf_report=pdf_report,
                ml_output=ml_output,
                nlp_output=nlp_output,
                dl_output=dl_output
            )

        except Exception as e:
            app.logger.error(f"Upload processing failed: {str(e)}", exc_info=True)
            flash(f"Upload failed: {str(e)}", "danger")
            return redirect(request.url)

    return render_template('upload.html')


# ─── Serve chart images ───────────────────────────────────────────────────────

@app.route('/static/charts/<path:filename>')
def serve_chart(filename):
    return send_from_directory('static/charts', filename)


# ─── Report placeholder ───────────────────────────────────────────────────────

# ─── History ──────────────────────────────────────────────────────────────────

@app.route('/history')
@login_required
def history():

    q = request.args.get('q', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if q:

        cursor.execute("""
            SELECT * FROM upload_history
            WHERE user_id = ?
            AND (
                file_name LIKE ?
                OR file_type LIKE ?
                OR insights LIKE ?
            )
            ORDER BY id DESC
        """, (
            session['user_id'],
            f"%{q}%",
            f"%{q}%",
            f"%{q}%"
        ))

    else:

        cursor.execute("""
            SELECT * FROM upload_history
            WHERE user_id = ?
            ORDER BY id DESC
        """, (session['user_id'],))

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'history.html',
        records=records
    )


# ─── View report ──────────────────────────────────────────────────────────────

@app.route('/view-report/<int:report_id>')
@login_required
def view_report(report_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            file_name,
            file_type,
            upload_date,
            insights,
            key_insights,
            recommendations,
            chart_data,
            ml_result,
            nlp_result,
            dl_result,
            structured_breakdown,
            pdf_report

        FROM upload_history
        WHERE id = ?
    """, (report_id,))

    report = cursor.fetchone()

    cursor.close()
    conn.close()

    if not report:

        flash("Report not found.", "danger")

        return redirect(url_for('history'))

    chart_paths = {}
    chart_path = None

    if report["chart_data"]:

        try:

            chart_paths = json.loads(report["chart_data"])

            if chart_paths:
                chart_path = next(iter(chart_paths.values()))

        except:
            chart_paths = {}
            chart_path = None

    key_insights = []

    if report["key_insights"]:

        if isinstance(report["key_insights"], str):

            try:
                key_insights = json.loads(report["key_insights"])
            except:
                key_insights = [report["key_insights"]]

    recommendations = []

    if report["recommendations"]:

        if isinstance(report["recommendations"], str):

            try:
                recommendations = json.loads(report["recommendations"])
            except:
                recommendations = [report["recommendations"]]

    structured_breakdown = []

    if report["structured_breakdown"]:

        if isinstance(report["structured_breakdown"], str):

            structured_breakdown = [
                {"summary": item.strip()}
                for item in report["structured_breakdown"].split("||")
                if item.strip()
            ]

    return render_template(
        'view_report.html',
        report=report,
        chart_paths=chart_paths,
        chart_path=chart_path,
        structured_breakdown=structured_breakdown,
        key_insights=key_insights,
        recommendations=recommendations
    )


# ─── Download PDF ─────────────────────────────────────────────────────────────

@app.route('/download-report/<int:report_id>')
@login_required
def download_report(report_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT
            pdf_report,
            file_name

        FROM upload_history

        WHERE id = ?

    """, (report_id,))

    report = cursor.fetchone()

    cursor.close()

    conn.close()

    if (
        not report
        or not report["pdf_report"]
    ):

        flash(
            "Report file not found.",
            "danger"
        )

        return redirect(
            url_for('history')
        )

    pdf_data = report["pdf_report"]

    file_name = (

        report["file_name"].rsplit(".", 1)[0]

        if report["file_name"]

        else "report"

    )

    filename = f"{file_name}_report.pdf"

    # ─── If PDF stored as bytes ───────────────────────────────

    if isinstance(
        pdf_data,
        (bytes, bytearray)
    ):

        from flask import Response

        return Response(

            bytes(pdf_data),

            mimetype="application/pdf",

            headers={

                "Content-Disposition":
                f"attachment; filename={filename}"

            }

        )

    # ─── If PDF stored as path ────────────────────────────────

    if (
        isinstance(pdf_data, str)
        and os.path.exists(pdf_data)
    ):

        return send_from_directory(

            os.path.dirname(pdf_data),

            os.path.basename(pdf_data),

            as_attachment=True

        )

    flash(
        "PDF file missing.",
        "danger"
    )

    return redirect(
        url_for('history')
    )

# ─── Settings ─────────────────────────────────────────────────────────────────

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():

    if request.method == 'POST':

        analysis_type = request.form.get('analysis_type')

        report_format = ",".join(
            request.form.getlist('report_format')
        )

        visual_charts = request.form.get('visual_charts')

        save_user_settings(
            analysis_type,
            report_format,
            visual_charts
        )

        flash(
            "Settings saved successfully.",
            "success"
        )

        return redirect(url_for('settings'))

    settings_data = get_user_settings()

    return render_template(
        'settings.html',
        settings_data=settings_data
    )


# ─── Register ─────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = generate_password_hash(
            request.form['password']
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,))

        existing_user = cursor.fetchone()

        if existing_user:

            flash(
                "Email already registered",
                "danger"
            )

            cursor.close()
            conn.close()

            return redirect(url_for('register'))

        cursor.execute("""
            INSERT INTO users
            (username, email, password)

            VALUES (?, ?, ?)
        """, (
            username,
            email,
            password
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(url_for('login'))

    return render_template('register.html')


# ─── Login ────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(
            user['password'],
            password
        ):

            session['user_id'] = user['id']
            session['username'] = user['username']

            flash(
                "Login successful",
                "success"
            )

            return redirect(url_for('index'))

        flash(
            "Invalid email or password",
            "danger"
        )

        return redirect(url_for('login'))

    return render_template('login.html')


# ─── Logout ───────────────────────────────────────────────────────────────────

@app.route('/logout')
def logout():

    session.clear()

    flash(
        "Logged out successfully",
        "success"
    )

    return redirect(url_for('login'))


# ─── Password Reset ───────────────────────────────────────────────────────────

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email  = request.form.get('email', '').strip().lower()
        token  = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=1)
        found  = save_reset_token(email, token, expiry)

        if found:
            link = url_for('reset_password', token=token, _external=True)
            try:
                send_reset_email(email, link)
                app.logger.info(f"✅ Reset email sent to {email}")
            except Exception as e:
                # ← Log the FULL error so we can see it in Render logs
                app.logger.error(f"❌ SMTP FAILED: {type(e).__name__}: {e}")
                flash(f"Email failed to send: {str(e)}", "danger")
                return render_template('auth-forgot-password-basic.html')
        else:
            app.logger.warning(f"⚠️ Email not found in DB: {email}")

        return redirect(url_for('forgot_password') + '?sent=1')

    return render_template('auth-forgot-password-basic.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    user = get_user_by_reset_token(token)

    if not user:

        flash(
            "Reset link expired or invalid.",
            "danger"
        )

        return redirect(
            url_for('forgot_password')
        )

    if request.method == 'POST':

        password = request.form.get(
            'password',
            ''
        )

        confirm = request.form.get(
            'confirm_password',
            ''
        )

        if len(password) < 8:

            flash(
                "Password must be at least 8 characters.",
                "danger"
            )

            return render_template(
                'reset-password.html',
                token=token
            )

        if password != confirm:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                'reset-password.html',
                token=token
            )

        update_user_password(
            user['id'],
            generate_password_hash(password)
        )

        flash(
            "Password reset successfully.",
            "success"
        )

        return redirect(url_for('login'))

    return render_template(
        'reset-password.html',
        token=token
    )
@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    try:
        token     = google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            flash("Google login failed. Please try again.", "danger")
            return redirect(url_for('login'))

        email   = user_info.get('email', '').strip().lower()
        name    = user_info.get('name', email.split('@')[0])
        picture = user_info.get('picture', '')

        if not email:
            flash("Could not get email from Google.", "danger")
            return redirect(url_for('login'))

        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(os.urandom(32).hex()))
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

        cursor.close()
        conn.close()

        session['user_id']  = user['id']        # ← works because of row_factory
        session['username'] = user['username']
        session['avatar']   = picture

        flash(f"Welcome, {user['username']}!", "success")
        return redirect(url_for('index'))

    except Exception as e:
        app.logger.error(f"Google OAuth error: {e}", exc_info=True)
        flash("Google login failed. Please try again.", "danger")
        return redirect(url_for('login'))
# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
