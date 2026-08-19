"""
TEC - The Learning Platform
Flask + SQLite web application.

Sections:
  T - Trading  (courses, chart patterns, candlestick patterns, forex, crypto, commodities)
  E - Editing  (graphic design, video editing, animation, photo editing)
  C - Coding   (Java, Python, C, C++, .NET, JavaScript, HTML, CSS)

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""
import os
import uuid
import io
from functools import wraps
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash,
    send_file, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import get_db, init_db, seed_db

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import math

app = Flask(__name__)
app.secret_key = os.environ.get("TEC_SECRET_KEY", "dev-secret-key-change-me")

# Base URL of the live site, used to build the QR code / verification link on
# certificates. Override with the TEC_SITE_URL environment variable once you
# have a custom domain (e.g. on Render: Settings -> Environment -> add
# TEC_SITE_URL = https://yourdomain.com).
SITE_URL = os.environ.get("TEC_SITE_URL", "https://tec-learning-platform2-o.onrender.com").rstrip("/")

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "profile_photos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_PHOTO_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_PHOTO_BYTES = 4 * 1024 * 1024  # 4 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_PHOTO_BYTES

# Admin dashboard password. CHANGE THIS via an environment variable in
# production (Render: Settings -> Environment -> TEC_ADMIN_PASSWORD).
ADMIN_PASSWORD = os.environ.get("TEC_ADMIN_PASSWORD", "changeme123")

# ---------------------------------------------------------------- helpers

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return user


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return dict(current_user=current_user())


# ---------------------------------------------------------------- public routes

@app.route("/")
def index():
    conn = get_db()
    conn.execute("INSERT INTO page_views DEFAULT VALUES")
    conn.commit()
    sections = conn.execute("SELECT * FROM sections ORDER BY id").fetchall()
    conn.close()
    return render_template("index.html", sections=sections)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not (full_name and username and email and password):
            flash("Please fill in all fields.", "error")
            return render_template("signup.html")

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username=? OR email=?", (username, email)
        ).fetchone()
        if existing:
            conn.close()
            flash("Username or email already registered.", "error")
            return render_template("signup.html")

        pw_hash = generate_password_hash(password)
        cur = conn.execute(
            "INSERT INTO users (full_name, username, email, password_hash) VALUES (?,?,?,?)",
            (full_name, username, email, pw_hash),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.execute("INSERT INTO login_events (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()

        session["user_id"] = user_id
        flash(f"Welcome to TEC, {full_name}! Your account has been created.", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? OR email=?", (username, username)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            conn = get_db()
            conn.execute("INSERT INTO login_events (user_id) VALUES (?)", (user["id"],))
            conn.commit()
            conn.close()
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------- learning area

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    sections = conn.execute("SELECT * FROM sections ORDER BY id").fetchall()
    data = []
    for s in sections:
        courses = conn.execute(
            "SELECT * FROM courses WHERE section_id=? ORDER BY id", (s["id"],)
        ).fetchall()
        data.append((s, courses))
    conn.close()
    return render_template("dashboard.html", data=data)


@app.route("/section/<slug>")
@login_required
def section_view(slug):
    conn = get_db()
    section = conn.execute("SELECT * FROM sections WHERE slug=?", (slug,)).fetchone()
    if not section:
        conn.close()
        abort(404)
    courses = conn.execute(
        "SELECT * FROM courses WHERE section_id=? ORDER BY id", (section["id"],)
    ).fetchall()

    course_progress = {}
    for c in courses:
        total = conn.execute("SELECT COUNT(*) n FROM lessons WHERE course_id=?", (c["id"],)).fetchone()["n"]
        done = conn.execute(
            """SELECT COUNT(*) n FROM progress p JOIN lessons l ON p.lesson_id=l.id
               WHERE p.user_id=? AND l.course_id=?""",
            (session["user_id"], c["id"]),
        ).fetchone()["n"]
        course_progress[c["id"]] = (done, total)
    conn.close()
    return render_template("section.html", section=section, courses=courses, course_progress=course_progress)


@app.route("/course/<slug>")
@login_required
def course_view(slug):
    conn = get_db()
    course = conn.execute("SELECT * FROM courses WHERE slug=?", (slug,)).fetchone()
    if not course:
        conn.close()
        abort(404)
    section = conn.execute("SELECT * FROM sections WHERE id=?", (course["section_id"],)).fetchone()
    lessons = conn.execute(
        "SELECT * FROM lessons WHERE course_id=? ORDER BY sort_order, id", (course["id"],)
    ).fetchall()
    done_ids = {
        r["lesson_id"] for r in conn.execute(
            """SELECT p.lesson_id FROM progress p JOIN lessons l ON p.lesson_id=l.id
               WHERE p.user_id=? AND l.course_id=?""",
            (session["user_id"], course["id"]),
        ).fetchall()
    }
    certificate = conn.execute(
        "SELECT * FROM certificates WHERE user_id=? AND course_id=?",
        (session["user_id"], course["id"]),
    ).fetchone()
    conn.close()

    all_done = len(lessons) > 0 and all(l["id"] in done_ids for l in lessons)
    return render_template(
        "course.html", course=course, section=section, lessons=lessons,
        done_ids=done_ids, all_done=all_done, certificate=certificate,
    )


@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson_view(lesson_id):
    conn = get_db()
    lesson = conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    if not lesson:
        conn.close()
        abort(404)
    course = conn.execute("SELECT * FROM courses WHERE id=?", (lesson["course_id"],)).fetchone()
    section = conn.execute("SELECT * FROM sections WHERE id=?", (course["section_id"],)).fetchone()
    lessons = conn.execute(
        "SELECT * FROM lessons WHERE course_id=? ORDER BY sort_order, id", (course["id"],)
    ).fetchall()
    is_done = conn.execute(
        "SELECT 1 FROM progress WHERE user_id=? AND lesson_id=?",
        (session["user_id"], lesson_id),
    ).fetchone() is not None
    conn.close()

    ids = [l["id"] for l in lessons]
    idx = ids.index(lesson_id)
    prev_lesson = lessons[idx-1] if idx > 0 else None
    next_lesson = lessons[idx+1] if idx < len(lessons)-1 else None

    return render_template(
        "lesson.html", lesson=lesson, course=course, section=section,
        is_done=is_done, prev_lesson=prev_lesson, next_lesson=next_lesson,
    )


@app.route("/lesson/<int:lesson_id>/complete", methods=["POST"])
@login_required
def complete_lesson(lesson_id):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO progress (user_id, lesson_id) VALUES (?,?)",
        (session["user_id"], lesson_id),
    )
    conn.commit()
    conn.close()
    flash("Lesson marked as complete!", "success")
    return redirect(url_for("lesson_view", lesson_id=lesson_id))


@app.route("/course/<int:course_id>/certificate/claim", methods=["POST"])
@login_required
def claim_certificate(course_id):
    conn = get_db()
    lessons = conn.execute("SELECT id FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    done = conn.execute(
        """SELECT COUNT(*) n FROM progress p JOIN lessons l ON p.lesson_id=l.id
           WHERE p.user_id=? AND l.course_id=?""",
        (session["user_id"], course_id),
    ).fetchone()["n"]

    if done < len(lessons) or len(lessons) == 0:
        conn.close()
        flash("Complete all lessons in this course to earn your certificate.", "error")
        return redirect(url_for("course_view", slug=_course_slug(course_id)))

    existing = conn.execute(
        "SELECT * FROM certificates WHERE user_id=? AND course_id=?",
        (session["user_id"], course_id),
    ).fetchone()
    if not existing:
        code = str(uuid.uuid4())[:8].upper()
        conn.execute(
            "INSERT INTO certificates (user_id, course_id, certificate_code) VALUES (?,?,?)",
            (session["user_id"], course_id, code),
        )
        conn.commit()
        flash("Congratulations! Your certificate has been issued.", "success")
    conn.close()
    return redirect(url_for("course_view", slug=_course_slug(course_id)))


def _course_slug(course_id):
    conn = get_db()
    row = conn.execute("SELECT slug FROM courses WHERE id=?", (course_id,)).fetchone()
    conn.close()
    return row["slug"] if row else ""


def _spaced_text(c, x, y, text, font, size, color, spacing, align="center"):
    """Draw text with letter-spacing, centred (or left) at x."""
    c.saveState()
    c.setFillColor(color)
    c.setFont(font, size)
    tw = c.stringWidth(text, font, size) + spacing * (len(text) - 1)
    start_x = x - tw / 2 if align == "center" else x
    t = c.beginText(start_x, y)
    t.setFont(font, size)
    t.setFillColor(color)
    t.setCharSpace(spacing)
    t.textOut(text)
    c.drawText(t)
    c.restoreState()


def _diamond(c, x, y, r, color):
    c.saveState()
    c.setFillColor(color)
    c.setStrokeColor(color)
    p = c.beginPath()
    p.moveTo(x, y + r)
    p.lineTo(x + r, y)
    p.lineTo(x, y - r)
    p.lineTo(x - r, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _star(c, cx, cy, r_outer, r_inner, color):
    c.saveState()
    c.setFillColor(color)
    p = c.beginPath()
    points = 5
    for i in range(points * 2):
        angle = math.pi/2 + i * math.pi / points
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _draw_qr(c, url, x, y, size, dark_color, light_color=None):
    """Draw a QR code encoding `url`, with its bottom-left corner at (x, y)."""
    widget = qr.QrCodeWidget(url)
    widget.barFillColor = dark_color
    if light_color is not None:
        widget.barBorderColor = light_color
    b = widget.getBounds()
    native_w = b[2] - b[0]
    native_h = b[3] - b[1]
    d = Drawing(size, size, transform=[size / native_w, 0, 0, size / native_h, 0, 0])
    d.add(widget)
    renderPDF.draw(d, c, x, y)


def _draw_certificate(buf, full_name, course_title, cert_code, issued_at):
    """Render a nicely designed landscape certificate PDF into buf."""
    page = landscape(A4)
    c = canvas.Canvas(buf, pagesize=page)
    w, h = page

    deep = HexColor("#01579B")
    deep2 = HexColor("#0277BD")
    sky = HexColor("#4FC3F7")
    pale = HexColor("#E1F5FE")
    gold = HexColor("#C9A227")
    ink = HexColor("#263238")
    muted = HexColor("#607D8B")
    white = HexColor("#FFFFFF")

    # ---- background ----
    c.setFillColor(white)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # faint pale-blue corner wash
    c.setFillColor(pale)
    c.saveState()
    c.circle(w, h, 11*cm, fill=1, stroke=0)
    c.circle(0, 0, 11*cm, fill=1, stroke=0)
    c.restoreState()
    c.setFillColor(white)
    c.circle(w, h, 10.3*cm, fill=1, stroke=0)
    c.circle(0, 0, 10.3*cm, fill=1, stroke=0)

    # ---- border frame ----
    margin = 1.0*cm
    c.setStrokeColor(deep)
    c.setLineWidth(3)
    c.rect(margin, margin, w-2*margin, h-2*margin, fill=0, stroke=1)

    inner = margin + 0.35*cm
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    c.rect(inner, inner, w-2*inner, h-2*inner, fill=0, stroke=1)

    # corner diamonds on the outer frame
    for cx, cy in [(margin, margin), (w-margin, margin), (margin, h-margin), (w-margin, h-margin)]:
        _diamond(c, cx, cy, 0.28*cm, gold)

    # ---- monogram badge ----
    badge_cy = h - 2.7*cm
    c.setFillColor(deep)
    c.circle(w/2, badge_cy, 1.05*cm, fill=1, stroke=0)
    c.setStrokeColor(gold)
    c.setLineWidth(1.2)
    c.circle(w/2, badge_cy, 1.05*cm, fill=0, stroke=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, badge_cy - 0.32*cm, "TEC")

    # ---- headings ----
    _spaced_text(c, w/2, h-4.5*cm, "CERTIFICATE OF COMPLETION", "Helvetica-Bold", 24, deep, 3)

    c.setFillColor(muted)
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(w/2, h-5.25*cm, "Trading  \u00b7  Editing  \u00b7  Coding")

    # small divider with diamond
    dy = h-5.9*cm
    c.setStrokeColor(gold)
    c.setLineWidth(0.8)
    c.line(w/2-3.2*cm, dy, w/2-0.35*cm, dy)
    c.line(w/2+0.35*cm, dy, w/2+3.2*cm, dy)
    _diamond(c, w/2, dy, 0.12*cm, gold)

    # ---- body ----
    c.setFillColor(ink)
    c.setFont("Helvetica", 13)
    c.drawCentredString(w/2, h-7.1*cm, "This certifies that")

    c.setFillColor(deep)
    c.setFont("Times-BoldItalic", 32)
    c.drawCentredString(w/2, h-8.6*cm, full_name)

    # underline beneath the name
    name_w = c.stringWidth(full_name, "Times-BoldItalic", 32)
    c.setStrokeColor(sky)
    c.setLineWidth(1)
    c.line(w/2 - name_w/2 - 0.4*cm, h-9.05*cm, w/2 + name_w/2 + 0.4*cm, h-9.05*cm)

    c.setFillColor(ink)
    c.setFont("Helvetica", 13)
    c.drawCentredString(w/2, h-10.1*cm, "has successfully completed the course")

    c.setFillColor(deep2)
    c.setFont("Helvetica-Bold", 19)
    c.drawCentredString(w/2, h-11.2*cm, course_title)

    # small divider under the course title, mirroring the one near the top
    dy2 = h-12.15*cm
    c.setStrokeColor(gold)
    c.setLineWidth(0.8)
    c.line(w/2-3.2*cm, dy2, w/2-0.35*cm, dy2)
    c.line(w/2+0.35*cm, dy2, w/2+3.2*cm, dy2)
    _diamond(c, w/2, dy2, 0.12*cm, gold)

    # ---- footer: signature blocks + seal ----
    foot_y = margin + 3.4*cm
    line_w = 5.4*cm

    left_x = margin + 3.0*cm
    c.setStrokeColor(muted)
    c.setLineWidth(0.8)
    c.line(left_x - line_w/2, foot_y, left_x + line_w/2, foot_y)
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(left_x, foot_y + 0.18*cm, "TEC Learning Platform")
    c.setFillColor(muted)
    c.setFont("Helvetica", 9)
    c.drawCentredString(left_x, foot_y - 0.4*cm, "Issuing Authority")

    right_x = w - margin - 3.0*cm
    c.setStrokeColor(muted)
    c.line(right_x - line_w/2, foot_y, right_x + line_w/2, foot_y)
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(right_x, foot_y + 0.18*cm, issued_at.split(" ")[0] if issued_at else "")
    c.setFillColor(muted)
    c.setFont("Helvetica", 9)
    c.drawCentredString(right_x, foot_y - 0.4*cm, "Date Issued")

    # decorative seal, centered under course title, above signatures
    seal_cx, seal_cy = w/2, foot_y + 0.1*cm
    c.setFillColor(gold)
    c.circle(seal_cx, seal_cy, 1.15*cm, fill=1, stroke=0)
    c.setFillColor(deep)
    c.circle(seal_cx, seal_cy, 0.92*cm, fill=1, stroke=0)
    _star(c, seal_cx, seal_cy, 0.62*cm, 0.26*cm, white)

    # certificate ID at the very bottom, with a small TEC logo badge and a
    # scannable QR code (linking to the public verification page) beside it
    id_text = f"Certificate ID: {cert_code}"
    id_font = "Helvetica"
    id_size = 8.5
    id_y = margin + 0.5*cm
    badge_r = 0.26*cm
    gap = 0.2*cm
    qr_size = 1.3*cm
    qr_gap = 0.25*cm

    c.setFont(id_font, id_size)
    text_w = c.stringWidth(id_text, id_font, id_size)
    total_w = (badge_r * 2) + gap + text_w + qr_gap + qr_size
    start_x = w/2 - total_w/2

    badge_cx2 = start_x + badge_r
    c.setFillColor(deep)
    c.circle(badge_cx2, id_y + 0.09*cm, badge_r, fill=1, stroke=0)
    c.setStrokeColor(gold)
    c.setLineWidth(0.6)
    c.circle(badge_cx2, id_y + 0.09*cm, badge_r, fill=0, stroke=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 5.2)
    c.drawCentredString(badge_cx2, id_y - 0.03*cm, "TEC")

    c.setFillColor(muted)
    c.setFont(id_font, id_size)
    text_x = start_x + (badge_r * 2) + gap
    c.drawString(text_x, id_y, id_text)

    verify_url = f"{SITE_URL}/verify/{cert_code}"
    qr_x = text_x + text_w + qr_gap
    qr_y = id_y - (qr_size / 2) + 0.28*cm
    _draw_qr(c, verify_url, qr_x, qr_y, qr_size, deep)

    c.showPage()
    c.save()


@app.route("/certificate/<int:course_id>/download")
@login_required
def download_certificate(course_id):
    conn = get_db()
    cert = conn.execute(
        "SELECT * FROM certificates WHERE user_id=? AND course_id=?",
        (session["user_id"], course_id),
    ).fetchone()
    user = current_user()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    conn.close()

    if not cert or not course:
        abort(404)

    buf = io.BytesIO()
    _draw_certificate(buf, user["full_name"], course["title"], cert["certificate_code"], cert["issued_at"])
    buf.seek(0)

    filename = f"TEC_Certificate_{course['slug']}.pdf"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/pdf")


def _allowed_photo(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXT


@app.route("/profile/photo", methods=["POST"])
@login_required
def upload_profile_photo():
    file = request.files.get("photo")
    if not file or file.filename == "":
        flash("Please choose an image to upload.", "error")
        return redirect(url_for("profile"))

    if not _allowed_photo(file.filename):
        flash("Please upload a PNG, JPG, GIF, or WEBP image.", "error")
        return redirect(url_for("profile"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"user_{session['user_id']}_{uuid.uuid4().hex[:8]}.{ext}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    conn = get_db()
    old = conn.execute("SELECT profile_photo FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.execute(
        "UPDATE users SET profile_photo=? WHERE id=?",
        (f"uploads/profile_photos/{filename}", session["user_id"]),
    )
    conn.commit()
    conn.close()

    # remove the old photo file, if any, to avoid piling up unused uploads
    if old and old["profile_photo"]:
        old_path = os.path.join(app.root_path, "static", old["profile_photo"])
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    flash("Profile photo updated!", "success")
    return redirect(url_for("profile"))


@app.route("/verify/<code>")
def verify_certificate(code):
    """Public certificate verification page — no login required, since this
    is meant to be opened by anyone scanning the QR code on a printed/shared
    certificate."""
    conn = get_db()
    cert = conn.execute(
        """SELECT cert.*, u.full_name, co.title AS course_title, co.icon AS course_icon,
                  s.name AS section_name
           FROM certificates cert
           JOIN users u ON cert.user_id = u.id
           JOIN courses co ON cert.course_id = co.id
           JOIN sections s ON co.section_id = s.id
           WHERE cert.certificate_code = ?""",
        (code,),
    ).fetchone()
    conn.close()
    return render_template("verify.html", cert=cert, code=code)


@app.route("/profile")
@login_required
def profile():
    conn = get_db()
    user = current_user()

    courses = conn.execute("SELECT * FROM courses").fetchall()
    ongoing, completed = [], []
    for c in courses:
        total = conn.execute("SELECT COUNT(*) n FROM lessons WHERE course_id=?", (c["id"],)).fetchone()["n"]
        done = conn.execute(
            """SELECT COUNT(*) n FROM progress p JOIN lessons l ON p.lesson_id=l.id
               WHERE p.user_id=? AND l.course_id=?""",
            (user["id"], c["id"]),
        ).fetchone()["n"]
        if total == 0:
            continue
        if done == total:
            completed.append(c)
        elif done > 0:
            ongoing.append((c, done, total))

    certificates = conn.execute(
        """SELECT cert.*, co.title as course_title, co.slug as course_slug, co.icon as course_icon
           FROM certificates cert JOIN courses co ON cert.course_id = co.id
           WHERE cert.user_id=? ORDER BY cert.issued_at DESC""",
        (user["id"],),
    ).fetchall()
    conn.close()

    return render_template(
        "profile.html", user=user, ongoing=ongoing, completed=completed, certificates=certificates
    )


# ---------------------------------------------------------------- admin

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Welcome to the admin dashboard.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect admin password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out of admin.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()

    total_users = conn.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
    total_logins = conn.execute("SELECT COUNT(*) n FROM login_events").fetchone()["n"]
    total_certs = conn.execute("SELECT COUNT(*) n FROM certificates").fetchone()["n"]
    total_lessons_done = conn.execute("SELECT COUNT(*) n FROM progress").fetchone()["n"]
    total_page_views = conn.execute("SELECT COUNT(*) n FROM page_views").fetchone()["n"]

    # signups & logins per day, for the last 14 days (zero-filled so the chart has no gaps)
    today = datetime.utcnow().date()
    day_labels = [(today - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]

    signup_rows = conn.execute(
        """SELECT date(created_at) d, COUNT(*) c FROM users
           WHERE date(created_at) >= date('now', '-13 days')
           GROUP BY d"""
    ).fetchall()
    signup_map = {r["d"]: r["c"] for r in signup_rows}
    signups_series = [signup_map.get(d, 0) for d in day_labels]

    login_rows = conn.execute(
        """SELECT date(logged_in_at) d, COUNT(*) c FROM login_events
           WHERE date(logged_in_at) >= date('now', '-13 days')
           GROUP BY d"""
    ).fetchall()
    login_map = {r["d"]: r["c"] for r in login_rows}
    logins_series = [login_map.get(d, 0) for d in day_labels]

    # per-user login count + last login time
    login_stats = {
        r["user_id"]: {"count": r["c"], "last": r["last"]}
        for r in conn.execute(
            """SELECT user_id, COUNT(*) c, MAX(logged_in_at) last
               FROM login_events GROUP BY user_id"""
        ).fetchall()
    }

    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    courses = conn.execute("SELECT * FROM courses").fetchall()

    user_rows = []
    for u in users:
        lessons_done = conn.execute(
            "SELECT COUNT(*) n FROM progress WHERE user_id=?", (u["id"],)
        ).fetchone()["n"]

        completed_titles = []
        ongoing_count = 0
        for c in courses:
            total = conn.execute(
                "SELECT COUNT(*) n FROM lessons WHERE course_id=?", (c["id"],)
            ).fetchone()["n"]
            if total == 0:
                continue
            done = conn.execute(
                """SELECT COUNT(*) n FROM progress p JOIN lessons l ON p.lesson_id=l.id
                   WHERE p.user_id=? AND l.course_id=?""",
                (u["id"], c["id"]),
            ).fetchone()["n"]
            if done == total:
                completed_titles.append(c["title"])
            elif done > 0:
                ongoing_count += 1

        ls = login_stats.get(u["id"], {"count": 0, "last": None})
        user_rows.append(dict(
            user=u,
            lessons_done=lessons_done,
            completed_titles=completed_titles,
            completed_count=len(completed_titles),
            ongoing_count=ongoing_count,
            login_count=ls["count"],
            last_login=ls["last"],
        ))

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_logins=total_logins,
        total_certs=total_certs,
        total_lessons_done=total_lessons_done,
        total_page_views=total_page_views,
        day_labels=day_labels,
        signups_series=signups_series,
        logins_series=logins_series,
        user_rows=user_rows,
    )


# ---------------------------------------------------------------- entrypoint

# Run once at import time, so the DB is ready whether this file is launched
# directly (python app.py) or imported by a production server (gunicorn app:app).
init_db()
seed_db()

if __name__ == "__main__":
    app.run(debug=True)
