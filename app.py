"""
EduNova College Registration - Flask Backend
==========================================
Run: python app.py
Open: http://localhost:5000
"""

from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from io import BytesIO
import random, string, datetime, os
from functools import wraps

app = Flask(__name__)
app.secret_key = "edunova_super_secret_2025"

# ═══════════════════════════════════════════════════════════════
#  DATABASE CONFIG — change password to yours
# ═══════════════════════════════════════════════════════════════
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "root",   # ← CHANGE THIS
    "database": "edunova_db",
    "charset":  "utf8mb4"
}

def get_db():
    """Return a fresh MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def gen_app_id():
    """Generate unique application ID like EN-2025-12345."""
    year = datetime.datetime.now().year
    rand = ''.join(random.choices(string.digits, k=5))
    return f"EN-{year}-{rand}"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════════
#  ROOT
# ═══════════════════════════════════════════════════════════════
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('register_page'))

# ═══════════════════════════════════════════════════════════════
#  REGISTER
# ═══════════════════════════════════════════════════════════════
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        f = request.form

        # Collect all fields
        first_name   = f.get('firstName', '').strip()
        last_name    = f.get('lastName', '').strip()
        email        = f.get('email', '').strip()
        phone        = f.get('phone', '').strip()
        dob          = f.get('dob', '')
        gender       = f.get('gender', '')
        address      = f.get('address', '').strip()
        password     = f.get('password', '')
        school_10    = f.get('school10', '').strip()
        marks_10     = f.get('marks10', '0')
        school_12    = f.get('school12', '').strip()
        marks_12     = f.get('marks12', '0')
        exam_type    = f.get('examType', 'None')
        exam_score   = f.get('examScore', '-')
        achievements = f.get('achievements', '')
        program      = f.get('program', '')
        degree_level = f.get('degree', '')
        hostel       = f.get('hostel', 'Not specified')
        heard_from   = f.get('source', '')
        sop          = f.get('sop', '')

        try:
            db  = get_db()
            cur = db.cursor(dictionary=True)

            # Check duplicate email
            cur.execute("SELECT id FROM students WHERE email = %s", (email,))
            if cur.fetchone():
                cur.close(); db.close()
                return jsonify({'success': False, 'message': 'This email is already registered. Please login.'})

            # Generate unique application ID
            app_id = gen_app_id()
            while True:
                cur.execute("SELECT id FROM students WHERE application_id = %s", (app_id,))
                if not cur.fetchone():
                    break
                app_id = gen_app_id()

            pw_hash = generate_password_hash(password)

            cur.execute("""
                INSERT INTO students (
                    application_id, first_name, last_name, email, phone,
                    dob, gender, address, password_hash,
                    school_10, marks_10, school_12, marks_12,
                    exam_type, exam_score, achievements,
                    program, degree_level, hostel, heard_from, sop
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """, (
                app_id, first_name, last_name, email, phone,
                dob, gender, address, pw_hash,
                school_10, marks_10, school_12, marks_12,
                exam_type, exam_score, achievements,
                program, degree_level, hostel, heard_from, sop
            ))
            db.commit()
            cur.close(); db.close()

            return jsonify({
                'success': True,
                'application_id': app_id,
                'name': first_name
            })

        except Exception as e:
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

    return render_template('register.html')

# ═══════════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        try:
            db  = get_db()
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT * FROM students WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close(); db.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id']  = user['id']
                session['app_id']   = user['application_id']
                session['username'] = user['first_name']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password. Please try again.', 'error')

        except Exception as e:
            flash(f'Connection error: {str(e)}', 'error')

    return render_template('login.html')

# ═══════════════════════════════════════════════════════════════
#  LOGOUT
# ═══════════════════════════════════════════════════════════════
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ═══════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM students WHERE id = %s", (session['user_id'],))
        student = cur.fetchone()
        cur.close(); db.close()

        if not student:
            session.clear()
            return redirect(url_for('login'))

        return render_template('dashboard.html', student=student)

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('login'))

# ═══════════════════════════════════════════════════════════════
#  PDF DOWNLOAD (Server-side with ReportLab)
# ═══════════════════════════════════════════════════════════════
@app.route('/download_pdf/<app_id>')
@login_required
def download_pdf(app_id):
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM students WHERE application_id = %s AND id = %s",
            (app_id, session['user_id'])
        )
        s = cur.fetchone()
        cur.close(); db.close()

        if not s:
            return "Application not found", 404

        buf = BytesIO()
        c   = rl_canvas.Canvas(buf, pagesize=A4)
        W, H = A4

        # ── Background ──────────────────────────────────────
        c.setFillColorRGB(0.027, 0.027, 0.059)
        c.rect(0, 0, W, H, fill=1, stroke=0)

        # ── Header Banner ───────────────────────────────────
        c.setFillColorRGB(0.102, 0.039, 0.235)
        c.rect(0, H - 72*mm, W, 72*mm, fill=1, stroke=0)

        # accent line under header
        c.setStrokeColorRGB(0.482, 0.231, 0.929)
        c.setLineWidth(2)
        c.line(0, H - 72*mm, W, H - 72*mm)

        # logo circle
        c.setFillColorRGB(0.482, 0.231, 0.929)
        c.circle(24*mm, H - 36*mm, 11*mm, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(24*mm, H - 39.5*mm, "EN")

        # college name & info
        c.setFont("Helvetica-Bold", 20)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(40*mm, H - 26*mm, "EduNova College")

        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.655, 0.545, 0.984)
        c.drawString(40*mm, H - 34*mm, "Excellence in Education Since 1980 | NAAC A++ Accredited")
        c.drawString(40*mm, H - 41*mm, "admissions@edunova.edu  |  +91 44 2222 0000  |  www.edunova.edu")
        c.drawString(40*mm, H - 48*mm, "123 Education Lane, Knowledge Park, Chennai - 600001")

        # doc title right
        c.setFont("Helvetica-Bold", 11)
        c.setFillColorRGB(0.133, 0.827, 0.933)
        c.drawRightString(W - 14*mm, H - 26*mm, "ADMISSION RECEIPT")
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.655, 0.545, 0.984)
        c.drawRightString(W - 14*mm, H - 34*mm, f"Date: {datetime.date.today().strftime('%d %B %Y')}")
        c.drawRightString(W - 14*mm, H - 41*mm, "Academic Year 2025-26")

        # ── Application ID Box ──────────────────────────────
        by = H - 92*mm
        c.setFillColorRGB(0.118, 0.039, 0.176)
        c.roundRect(14*mm, by, W - 28*mm, 14*mm, 4*mm, fill=1, stroke=0)
        c.setStrokeColorRGB(0.482, 0.231, 0.929)
        c.setLineWidth(0.8)
        c.roundRect(14*mm, by, W - 28*mm, 14*mm, 4*mm, fill=0, stroke=1)

        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.655, 0.545, 0.984)
        c.drawCentredString(W/2, by + 9.5*mm, "APPLICATION ID")
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(1, 1, 1)
        c.drawCentredString(W/2, by + 3.8*mm, s['application_id'])

        # status badge
        status_colors = {
            'Pending':      (0.961, 0.620, 0.043),
            'Under Review': (0.133, 0.827, 0.933),
            'Accepted':     (0.063, 0.725, 0.506),
            'Rejected':     (0.937, 0.267, 0.267),
        }
        sc = status_colors.get(s['status'], (0.655, 0.545, 0.984))
        c.setFillColorRGB(0.063, 0.725, 0.506)
        c.roundRect(W - 50*mm, by + 3*mm, 34*mm, 8*mm, 2*mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(1, 1, 1)
        c.drawCentredString(W - 33*mm, by + 6.8*mm, f"STATUS: {s['status'].upper()}")

        # ── Section drawing helper ───────────────────────────
        y = by - 8*mm

        def draw_section(title, fields):
            nonlocal y
            c.setFillColorRGB(0.078, 0.078, 0.153)
            c.rect(14*mm, y - 6*mm, W - 28*mm, 9*mm, fill=1, stroke=0)
            c.setStrokeColorRGB(0.482, 0.231, 0.929)
            c.setLineWidth(2.5)
            c.line(14*mm, y + 3*mm, 14*mm, y - 6*mm)
            c.setLineWidth(0.4)
            c.setFont("Helvetica-Bold", 9)
            c.setFillColorRGB(0.655, 0.545, 0.984)
            c.drawString(18.5*mm, y - 2*mm, title.upper())
            y -= 9.5*mm

            col_w = (W - 28*mm) / 2
            for i in range(0, len(fields), 2):
                rh = 12*mm
                pair = fields[i:i+2]
                for idx, item in enumerate(pair):
                    x0 = 14*mm + idx * col_w
                    c.setFillColorRGB(0.071, 0.071, 0.114)
                    c.rect(x0, y - rh, col_w - 1*mm, rh, fill=1, stroke=0)
                    c.setStrokeColorRGB(0.157, 0.157, 0.231)
                    c.setLineWidth(0.3)
                    c.rect(x0, y - rh, col_w - 1*mm, rh, fill=0, stroke=1)
                    c.setFont("Helvetica", 6.5)
                    c.setFillColorRGB(0.471, 0.471, 0.706)
                    c.drawString(x0 + 2.5*mm, y - 3.8*mm, item[0])
                    c.setFont("Helvetica-Bold", 8.5)
                    c.setFillColorRGB(0.863, 0.863, 0.941)
                    val = str(item[1] if item[1] else '-')[:37]
                    c.drawString(x0 + 2.5*mm, y - 9.5*mm, val)
                if len(pair) == 1:
                    # empty right cell
                    x0 = 14*mm + col_w
                    c.setFillColorRGB(0.071, 0.071, 0.114)
                    c.rect(x0, y - rh, col_w - 1*mm, rh, fill=1, stroke=0)
                    c.setStrokeColorRGB(0.157, 0.157, 0.231)
                    c.setLineWidth(0.3)
                    c.rect(x0, y - rh, col_w - 1*mm, rh, fill=0, stroke=1)
                y -= rh + 0.8*mm
            y -= 4*mm

        draw_section("Personal Information", [
            ("Full Name",       f"{s['first_name']} {s['last_name']}"),
            ("Date of Birth",   str(s['dob'])),
            ("Gender",          s['gender']),
            ("Phone Number",    s['phone']),
            ("Email Address",   s['email']),
            ("Address",         str(s['address'])[:40]),
        ])

        draw_section("Academic Details", [
            ("10th School",     s['school_10']),
            ("10th Marks",      f"{s['marks_10']}%"),
            ("12th College",    s['school_12']),
            ("12th Marks",      f"{s['marks_12']}%"),
            ("Entrance Exam",   s['exam_type'] or 'None'),
            ("Score / Rank",    s['exam_score'] or '-'),
        ])

        draw_section("Program Details", [
            ("Program Applied", s['program']),
            ("Degree Level",    s['degree_level']),
            ("Hostel",          s['hostel'] or 'Not specified'),
            ("Heard From",      s['heard_from'] or '-'),
        ])

        # ── SOP Box ─────────────────────────────────────────
        sop_text = str(s['sop'] or '')
        c.setFillColorRGB(0.071, 0.071, 0.114)
        c.roundRect(14*mm, y - 26*mm, W - 28*mm, 26*mm, 3*mm, fill=1, stroke=0)
        c.setStrokeColorRGB(0.157, 0.157, 0.231)
        c.setLineWidth(0.3)
        c.roundRect(14*mm, y - 26*mm, W - 28*mm, 26*mm, 3*mm, fill=0, stroke=1)
        c.setFont("Helvetica", 6.5)
        c.setFillColorRGB(0.471, 0.471, 0.706)
        c.drawString(18*mm, y - 5*mm, "STATEMENT OF PURPOSE")
        c.setFont("Helvetica", 7.8)
        c.setFillColorRGB(0.706, 0.706, 0.824)
        words = sop_text.split()
        line, lines_list = "", []
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, "Helvetica", 7.8) < (W - 36*mm):
                line = test
            else:
                lines_list.append(line)
                line = w
        lines_list.append(line)
        tx_obj = c.beginText(18*mm, y - 11*mm)
        tx_obj.setFont("Helvetica", 7.8)
        tx_obj.setFillColorRGB(0.706, 0.706, 0.824)
        tx_obj.setLeading(11)
        for ln in lines_list[:3]:
            tx_obj.textLine(ln)
        if len(lines_list) > 3:
            tx_obj.setFillColorRGB(0.482, 0.231, 0.929)
            tx_obj.textLine("... (see full SOP in portal)")
        c.drawText(tx_obj)
        y -= 30*mm

        # ── Submission Info Row ──────────────────────────────
        submitted = s['created_at'].strftime('%d %B %Y at %I:%M %p') if s.get('created_at') else 'N/A'
        c.setFillColorRGB(0.039, 0.157, 0.118)
        c.roundRect(14*mm, y - 11*mm, W - 28*mm, 11*mm, 2.5*mm, fill=1, stroke=0)
        c.setStrokeColorRGB(0.063, 0.725, 0.506)
        c.setLineWidth(0.5)
        c.roundRect(14*mm, y - 11*mm, W - 28*mm, 11*mm, 2.5*mm, fill=0, stroke=1)
        c.setFont("Helvetica", 7.5)
        c.setFillColorRGB(0.063, 0.725, 0.506)
        c.drawString(18*mm, y - 7*mm, f"Submitted on: {submitted}")
        c.setFillColorRGB(0.4, 0.9, 0.7)
        c.drawRightString(W - 18*mm, y - 7*mm, "Thank you for applying to EduNova College!")

        # ── Footer ──────────────────────────────────────────
        fy = 18*mm
        c.setStrokeColorRGB(0.157, 0.157, 0.231)
        c.setLineWidth(0.5)
        c.line(14*mm, fy, W - 14*mm, fy)
        c.setFont("Helvetica", 6.5)
        c.setFillColorRGB(0.314, 0.314, 0.471)
        c.drawCentredString(W/2, 13*mm, "This is a computer-generated receipt. No signature is required.")
        c.drawCentredString(W/2, 8*mm, "EduNova College  |  NAAC A++  |  Estd. 1980  |  admissions@edunova.edu")

        # ── Outer Border ────────────────────────────────────
        c.setStrokeColorRGB(0.235, 0.078, 0.392)
        c.setLineWidth(1.2)
        c.rect(4.5*mm, 4.5*mm, W - 9*mm, H - 9*mm, fill=0, stroke=1)

        c.save()
        buf.seek(0)

        return send_file(
            buf,
            as_attachment=True,
            download_name=f"EduNova_{s['application_id']}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

# ═══════════════════════════════════════════════════════════════
#  STATUS CHECK API
# ═══════════════════════════════════════════════════════════════
@app.route('/api/status/<app_id>')
def api_status(app_id):
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT application_id, first_name, last_name, program, status, created_at FROM students WHERE application_id = %s",
            (app_id,)
        )
        row = cur.fetchone()
        cur.close(); db.close()
        if row:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime('%d %B %Y')
            return jsonify({'found': True, **row})
        return jsonify({'found': False})
    except Exception as e:
        return jsonify({'found': False, 'error': str(e)})

# ═══════════════════════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  EduNova College Registration Portal")
    print("  Running at: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)