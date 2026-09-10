from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import sqlite3
import os

from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# Change this in production and preferably load it from an environment variable.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-production"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Doctors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience TEXT,
            description TEXT,
            image TEXT
        )
    """)

    # Services table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    # Appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(patient_id)
            REFERENCES users(id),

            FOREIGN KEY(doctor_id)
            REFERENCES doctors(id)
        )
    """)

    # Contact / Enquiry table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # CREATE DEFAULT ADMIN
    # -----------------------------------------------------

    admin = cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@fertility.com",)
    ).fetchone()

    if not admin:

        password = generate_password_hash("admin123")

        cursor.execute("""
            INSERT INTO users
            (name, email, phone, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Administrator",
            "admin@fertility.com",
            "9999999999",
            password,
            "admin"
        ))

    # -----------------------------------------------------
    # DEFAULT DOCTORS
    # -----------------------------------------------------

    doctor_count = cursor.execute(
        "SELECT COUNT(*) AS count FROM doctors"
    ).fetchone()["count"]

    if doctor_count == 0:

        doctors = [
            (
                "Dr. Priya Patil",
                "Fertility Specialist",
                "12+ Years",
                "Experienced fertility specialist providing personalized fertility care."
            ),
            (
                "Dr. Amit Deshmukh",
                "Reproductive Medicine Specialist",
                "10+ Years",
                "Specialist in reproductive medicine and fertility treatment."
            ),
            (
                "Dr. Neha Kulkarni",
                "IVF Specialist",
                "8+ Years",
                "Focused on IVF, infertility evaluation and patient-centered care."
            )
        ]

        cursor.executemany("""
            INSERT INTO doctors
            (name, specialization, experience, description)
            VALUES (?, ?, ?, ?)
        """, doctors)

    # -----------------------------------------------------
    # DEFAULT SERVICES
    # -----------------------------------------------------

    service_count = cursor.execute(
        "SELECT COUNT(*) AS count FROM services"
    ).fetchone()["count"]

    if service_count == 0:

        services = [
            (
                "IVF Treatment",
                "Advanced fertility treatment with personalized medical guidance."
            ),
            (
                "IUI Treatment",
                "Intrauterine insemination treatment for selected fertility cases."
            ),
            (
                "Fertility Consultation",
                "Professional fertility consultation and treatment planning."
            ),
            (
                "Infertility Evaluation",
                "Comprehensive evaluation to understand possible fertility issues."
            ),
            (
                "Egg & Sperm Freezing",
                "Fertility preservation options for eligible patients."
            ),
            (
                "Pregnancy Support",
                "Guidance and support throughout your fertility journey."
            )
        ]

        cursor.executemany("""
            INSERT INTO services
            (name, description)
            VALUES (?, ?)
        """, services)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():

    conn = get_db()

    doctors = conn.execute(
        "SELECT * FROM doctors LIMIT 3"
    ).fetchall()

    services = conn.execute(
        "SELECT * FROM services LIMIT 6"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        doctors=doctors,
        services=services
    )


# ---------------------------------------------------------
# ABOUT
# ---------------------------------------------------------

@app.route("/about")
def about():
    return render_template("about.html")


# ---------------------------------------------------------
# SERVICES
# ---------------------------------------------------------

@app.route("/services")
def services():

    conn = get_db()

    services = conn.execute(
        "SELECT * FROM services"
    ).fetchall()

    conn.close()

    return render_template(
        "services.html",
        services=services
    )


# ---------------------------------------------------------
# DOCTORS
# ---------------------------------------------------------

@app.route("/doctors")
def doctors():

    conn = get_db()

    doctors = conn.execute(
        "SELECT * FROM doctors"
    ).fetchall()

    conn.close()

    return render_template(
        "doctors.html",
        doctors=doctors
    )


# ---------------------------------------------------------
# CONTACT
# ---------------------------------------------------------

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not message:
            flash(
                "Please enter your name and message.",
                "danger"
            )

            return redirect(url_for("contact"))

        conn = get_db()

        conn.execute("""
            INSERT INTO enquiries
            (name, email, phone, message)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            message
        ))

        conn.commit()
        conn.close()

        flash(
            "Your enquiry has been submitted successfully.",
            "success"
        )

        return redirect(url_for("contact"))

    return render_template("contact.html")


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(url_for("register"))

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(url_for("register"))

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(url_for("register"))

        conn = get_db()

        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:

            conn.close()

            flash(
                "Email already registered.",
                "danger"
            )

            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn.execute("""
            INSERT INTO users
            (name, email, phone, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            hashed_password,
            "patient"
        ))

        conn.commit()
        conn.close()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(
                url_for("patient_dashboard")
            )

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("home"))


# ---------------------------------------------------------
# APPOINTMENT BOOKING
# ---------------------------------------------------------

@app.route("/appointment", methods=["GET", "POST"])
def appointment():

    if "user_id" not in session:

        flash(
            "Please login before booking an appointment.",
            "warning"
        )

        return redirect(url_for("login"))

    conn = get_db()

    doctors = conn.execute(
        "SELECT * FROM doctors"
    ).fetchall()

    if request.method == "POST":

        doctor_id = request.form.get("doctor_id")
        appointment_date = request.form.get(
            "appointment_date"
        )
        appointment_time = request.form.get(
            "appointment_time"
        )
        reason = request.form.get(
            "reason",
            ""
        ).strip()

        if not appointment_date or not appointment_time:

            conn.close()

            flash(
                "Please select appointment date and time.",
                "danger"
            )

            return redirect(
                url_for("appointment")
            )

        conn.execute("""
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                reason
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            doctor_id if doctor_id else None,
            appointment_date,
            appointment_time,
            reason
        ))

        conn.commit()
        conn.close()

        flash(
            "Appointment request submitted successfully.",
            "success"
        )

        return redirect(
            url_for("patient_dashboard")
        )

    conn.close()

    return render_template(
        "appointment.html",
        doctors=doctors
    )


# ---------------------------------------------------------
# PATIENT DASHBOARD
# ---------------------------------------------------------

@app.route("/patient/dashboard")
def patient_dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if session.get("role") != "patient":

        return redirect(url_for("admin_dashboard"))

    conn = get_db()

    appointments = conn.execute("""
        SELECT
            appointments.*,
            doctors.name AS doctor_name,
            doctors.specialization
        FROM appointments
        LEFT JOIN doctors
        ON appointments.doctor_id = doctors.id
        WHERE appointments.patient_id = ?
        ORDER BY appointment_date DESC
    """, (
        session["user_id"],
    )).fetchall()

    patient = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    conn.close()

    return render_template(
        "patient_dashboard.html",
        appointments=appointments,
        patient=patient
    )


# ---------------------------------------------------------
# ADMIN CHECK
# ---------------------------------------------------------

def admin_required():

    return (
        "user_id" in session
        and session.get("role") == "admin"
    )


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------

@app.route("/admin")
def admin_dashboard():

    if not admin_required():

        flash(
            "Admin login required.",
            "danger"
        )

        return redirect(url_for("login"))

    conn = get_db()

    patient_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'patient'
    """).fetchone()["count"]

    appointment_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM appointments
    """).fetchone()["count"]

    pending_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM appointments
        WHERE status = 'Pending'
    """).fetchone()["count"]

    enquiry_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM enquiries
    """).fetchone()["count"]

    recent_appointments = conn.execute("""
        SELECT
            appointments.*,
            users.name AS patient_name,
            doctors.name AS doctor_name
        FROM appointments
        JOIN users
        ON appointments.patient_id = users.id
        LEFT JOIN doctors
        ON appointments.doctor_id = doctors.id
        ORDER BY appointments.created_at DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        patient_count=patient_count,
        appointment_count=appointment_count,
        pending_count=pending_count,
        enquiry_count=enquiry_count,
        recent_appointments=recent_appointments
    )


# ---------------------------------------------------------
# ADMIN - PATIENTS
# ---------------------------------------------------------

@app.route("/admin/patients")
def patients():

    if not admin_required():

        return redirect(url_for("login"))

    conn = get_db()

    patients = conn.execute("""
        SELECT *
        FROM users
        WHERE role = 'patient'
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return render_template(
        "patients.html",
        patients=patients
    )


# ---------------------------------------------------------
# ADMIN - PATIENT DETAIL
# ---------------------------------------------------------

@app.route("/admin/patient/<int:patient_id>")
def patient_detail(patient_id):

    if not admin_required():

        return redirect(url_for("login"))

    conn = get_db()

    patient = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        AND role = 'patient'
    """, (
        patient_id,
    )).fetchone()

    if not patient:

        conn.close()

        flash(
            "Patient not found.",
            "danger"
        )

        return redirect(
            url_for("patients")
        )

    appointments = conn.execute("""
        SELECT
            appointments.*,
            doctors.name AS doctor_name
        FROM appointments
        LEFT JOIN doctors
        ON appointments.doctor_id = doctors.id
        WHERE appointments.patient_id = ?
        ORDER BY appointment_date DESC
    """, (
        patient_id,
    )).fetchall()

    conn.close()

    return render_template(
        "patient_detail.html",
        patient=patient,
        appointments=appointments
    )


# ---------------------------------------------------------
# ADMIN - APPOINTMENTS
# ---------------------------------------------------------

@app.route("/admin/appointments")
def appointments():

    if not admin_required():

        return redirect(url_for("login"))

    conn = get_db()

    appointments = conn.execute("""
        SELECT
            appointments.*,
            users.name AS patient_name,
            users.email AS patient_email,
            users.phone AS patient_phone,
            doctors.name AS doctor_name
        FROM appointments
        JOIN users
        ON appointments.patient_id = users.id
        LEFT JOIN doctors
        ON appointments.doctor_id = doctors.id
        ORDER BY appointment_date DESC
    """).fetchall()

    conn.close()

    return render_template(
        "appointments.html",
        appointments=appointments
    )


# ---------------------------------------------------------
# ADMIN - UPDATE APPOINTMENT STATUS
# ---------------------------------------------------------

@app.route(
    "/admin/appointment/<int:appointment_id>/status",
    methods=["POST"]
)
def update_appointment_status(appointment_id):

    if not admin_required():

        return redirect(url_for("login"))

    status = request.form.get("status")

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid appointment status.",
            "danger"
        )

        return redirect(
            url_for("appointments")
        )

    conn = get_db()

    conn.execute("""
        UPDATE appointments
        SET status = ?
        WHERE id = ?
    """, (
        status,
        appointment_id
    ))

    conn.commit()
    conn.close()

    flash(
        "Appointment status updated.",
        "success"
    )

    return redirect(
        url_for("appointments")
    )


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

# Initialize database when the application starts
init_db()


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )