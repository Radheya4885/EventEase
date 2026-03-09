from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for, flash, abort
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, date
import MySQLdb
import os
import uuid
import re

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='templates/static')

# -----------------------------
# MySQL CONFIGURATION (from .env)
# -----------------------------
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'eventease')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-dev-key')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Return rows as dictionaries

mysql = MySQL(app)

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if uploaded file has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------
# AUTH DECORATORS
# -----------------------------
def login_required(f):
    """Decorator — redirects to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'loggedin' not in session:
            flash("Please login to access this page.")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    """Decorator — restricts route to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'loggedin' not in session:
                flash("Please login to access this page.")
                return redirect(url_for('login_page'))
            if session.get('role') not in roles:
                flash("You do not have permission to access this page.")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# -----------------------------
# PASSWORD VALIDATION
# -----------------------------
def validate_password(password):
    """Check password meets minimum strength requirements."""
    errors = []
    if len(password) < 6:
        errors.append("Password must be at least 6 characters long.")
    if not re.search(r'[A-Za-z]', password):
        errors.append("Password must contain at least one letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number.")
    return errors


# -----------------------------
# AUTO-CREATE DATABASE & TABLES
# -----------------------------
def ensure_database_exists():
    """Automatically create the database and tables if they don't exist."""
    try:
        conn = MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD'],
        )
        cursor = conn.cursor()
        db_name = app.config['MYSQL_DB']
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        cursor.execute(f"USE `{db_name}`")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role ENUM('organizer', 'volunteer', 'participant', 'admin') NOT NULL DEFAULT 'participant',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_role (role)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                flyer_image VARCHAR(255),
                category VARCHAR(100),
                price DECIMAL(10, 2) DEFAULT 0.00,
                event_date DATE,
                event_time TIME,
                venue VARCHAR(200),
                address VARCHAR(300),
                gmap_link VARCHAR(500),
                max_participants INT DEFAULT 100,
                registration_deadline DATE,
                organizer_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_event_date (event_date),
                INDEX idx_category (category),
                INDEX idx_organizer (organizer_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                event_id INT NOT NULL,
                payment_status VARCHAR(50) DEFAULT 'pending',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                UNIQUE KEY unique_registration (user_id, event_id),
                INDEX idx_user (user_id),
                INDEX idx_event (event_id)
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Database '{db_name}' is ready!")
    except MySQLdb.OperationalError as e:
        print(f"⚠️  Could not auto-create database: {e}")
        print("   Make sure MySQL is running and your .env credentials are correct.")

# Run on startup
ensure_database_exists()

# -----------------------------
# FILE UPLOAD CONFIG
# -----------------------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# -----------------------------
# ERROR HANDLERS
# -----------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# REGISTER PAGE
# -----------------------------
@app.route("/register")
def register_page():
    return render_template("register.html")

# -----------------------------
# REGISTER USER
# -----------------------------
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'participant')

    if not name or not email or not password:
        flash("All fields are required.")
        return redirect(url_for('register_page'))

    if role not in ('organizer', 'volunteer', 'participant'):
        flash("Invalid role selected.")
        return redirect(url_for('register_page'))

    pwd_errors = validate_password(password)
    if pwd_errors:
        for err in pwd_errors:
            flash(err)
        return redirect(url_for('register_page'))

    hashed_password = generate_password_hash(password)

    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("Email already registered. Please login.")
                return redirect(url_for('login_page'))

            cursor.execute(
                "INSERT INTO users(name, email, password, role) VALUES(%s, %s, %s, %s)",
                (name, email, hashed_password, role)
            )
            mysql.connection.commit()
    except Exception:
        flash("An error occurred during registration. Please try again.")
        return redirect(url_for('register_page'))

    flash("User Registered Successfully! Please login.")
    return redirect(url_for('login_page'))

# -----------------------------
# LOGIN PAGE
# -----------------------------
@app.route("/login")
def login_page():
    return render_template("login.html")

# -----------------------------
# LOGIN USER
# -----------------------------
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        flash("Please fill in all fields.")
        return redirect(url_for('login_page'))

    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT id, name, email, password, role FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
    except Exception:
        flash("An error occurred. Please try again.")
        return redirect(url_for('login_page'))

    if user and check_password_hash(user['password'], password):
        session['loggedin'] = True
        session['id'] = user['id']
        session['name'] = user['name']
        session['role'] = user['role']

        role = user['role']
        if role == "organizer":
            return redirect(url_for("organizer_dashboard"))
        elif role == "volunteer":
            return redirect(url_for("volunteer_dashboard"))
        elif role == "participant":
            return redirect(url_for("participant_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for('home'))

    flash("Invalid email or password")
    return redirect(url_for('login_page'))

# -----------------------------
# DASHBOARD ROUTES (with real data)
# -----------------------------
@app.route("/organizer_dashboard")
@login_required
def organizer_dashboard():
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE organizer_id=%s ORDER BY event_date DESC",
                           (session['id'],))
            my_events = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) AS total FROM registrations r
                JOIN events e ON r.event_id = e.id
                WHERE e.organizer_id = %s
            """, (session['id'],))
            total_registrations = cursor.fetchone()['total']

        return render_template("organizer_dashboard.html",
                               my_events=my_events,
                               total_registrations=total_registrations)
    except Exception:
        return render_template("organizer_dashboard.html", my_events=[], total_registrations=0)

@app.route("/volunteer_dashboard")
@login_required
def volunteer_dashboard():
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("""
                SELECT e.id, e.title, e.event_date, e.event_time, e.venue,
                       r.registered_at
                FROM registrations r
                JOIN events e ON r.event_id = e.id
                WHERE r.user_id = %s ORDER BY e.event_date ASC
            """, (session['id'],))
            my_registrations = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) AS total FROM events WHERE event_date >= CURDATE()")
            upcoming_count = cursor.fetchone()['total']

        return render_template("volunteer_dashboard.html",
                               my_registrations=my_registrations,
                               upcoming_count=upcoming_count)
    except Exception:
        return render_template("volunteer_dashboard.html", my_registrations=[], upcoming_count=0)

@app.route("/participant_dashboard")
@login_required
def participant_dashboard():
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("""
                SELECT e.id, e.title, e.description, e.flyer_image, e.category,
                       e.price, e.event_date, e.event_time, e.venue,
                       r.payment_status, r.registered_at
                FROM registrations r
                JOIN events e ON r.event_id = e.id
                WHERE r.user_id = %s ORDER BY e.event_date ASC
            """, (session['id'],))
            my_registrations = cursor.fetchall()

        return render_template("participant_dashboard.html",
                               my_registrations=my_registrations)
    except Exception:
        return render_template("participant_dashboard.html", my_registrations=[])

@app.route("/admin_dashboard")
@role_required('admin')
def admin_dashboard():
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM users")
            total_users = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) AS total FROM events")
            total_events = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) AS total FROM registrations")
            total_registrations = cursor.fetchone()['total']

            cursor.execute("SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC")
            all_users = cursor.fetchall()

            cursor.execute("SELECT * FROM events ORDER BY created_at DESC")
            all_events = cursor.fetchall()

        return render_template("admin_dashboard.html",
                               total_users=total_users,
                               total_events=total_events,
                               total_registrations=total_registrations,
                               all_users=all_users,
                               all_events=all_events)
    except Exception:
        return render_template("admin_dashboard.html",
                               total_users=0, total_events=0, total_registrations=0,
                               all_users=[], all_events=[])

# -----------------------------
# PROFILE PAGE
# -----------------------------
@app.route("/profile")
@login_required
def profile():
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE id=%s",
                           (session['id'],))
            user = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM registrations WHERE user_id=%s",
                           (session['id'],))
            reg_count = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) AS total FROM events WHERE organizer_id=%s",
                           (session['id'],))
            events_organized = cursor.fetchone()['total']

        return render_template("profile.html", user=user, reg_count=reg_count,
                               events_organized=events_organized)
    except Exception:
        flash("Could not load profile.")
        return redirect(url_for('home'))

@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    if not name:
        flash("Name cannot be empty.")
        return redirect(url_for('profile'))

    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("UPDATE users SET name=%s WHERE id=%s", (name, session['id']))
            mysql.connection.commit()
            session['name'] = name
        flash("Profile updated successfully!")
    except Exception:
        flash("Could not update profile. Please try again.")

    return redirect(url_for('profile'))

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('home'))

# -----------------------------
# CREATE EVENT PAGE
# -----------------------------
@app.route("/create_event")
@login_required
def create_event_page():
    return render_template("create_event.html")

# -----------------------------
# CREATE EVENT (POST)
# -----------------------------
@app.route("/create_event", methods=["POST"])
@login_required
def create_event():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "0")
    event_date = request.form.get("event_date", "")
    event_time = request.form.get("event_time", "")
    venue = request.form.get("venue", "").strip()
    address = request.form.get("address", "").strip()
    gmap_link = request.form.get("gmap_link", "").strip()
    max_participants = request.form.get("max_participants", "100")
    registration_deadline = request.form.get("registration_deadline", "")

    if not title:
        flash("Event title is required.")
        return redirect(url_for('create_event_page'))

    if event_date:
        try:
            ed = datetime.strptime(event_date, "%Y-%m-%d").date()
            if ed < date.today():
                flash("Event date cannot be in the past.")
                return redirect(url_for('create_event_page'))
        except ValueError:
            flash("Invalid event date format.")
            return redirect(url_for('create_event_page'))

    if registration_deadline and event_date:
        try:
            rd = datetime.strptime(registration_deadline, "%Y-%m-%d").date()
            ed = datetime.strptime(event_date, "%Y-%m-%d").date()
            if rd > ed:
                flash("Registration deadline cannot be after the event date.")
                return redirect(url_for('create_event_page'))
        except ValueError:
            pass

    flyer = request.files.get("flyer_image")
    filename = ""

    if flyer and flyer.filename != "":
        if not allowed_file(flyer.filename):
            flash("Only image files (png, jpg, jpeg, gif, webp) are allowed.")
            return redirect(url_for('create_event_page'))
        original_name = secure_filename(flyer.filename)
        filename = f"{uuid.uuid4().hex}_{original_name}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        flyer.save(filepath)

    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO events
                (title, description, flyer_image, category, price,
                event_date, event_time, venue, address,
                gmap_link, max_participants, registration_deadline, organizer_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    title, description, filename, category, price,
                    event_date or None, event_time or None, venue, address,
                    gmap_link, max_participants, registration_deadline or None,
                    session.get('id')
                )
            )
            mysql.connection.commit()
    except Exception:
        flash("An error occurred while creating the event. Please try again.")
        return redirect(url_for('create_event_page'))

    flash("Event Created Successfully!")
    return redirect(url_for('events'))

# -----------------------------
# EVENTS PAGE (with search & filter)
# -----------------------------
@app.route("/events")
def events():
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 9

    try:
        with mysql.connection.cursor() as cursor:
            query = "SELECT * FROM events WHERE 1=1"
            params = []

            if search:
                query += " AND (title LIKE %s OR description LIKE %s OR venue LIKE %s)"
                like = f"%{search}%"
                params.extend([like, like, like])

            if category_filter:
                query += " AND category = %s"
                params.append(category_filter)

            count_query = query.replace("SELECT *", "SELECT COUNT(*) AS total", 1)
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            total_pages = max(1, (total + per_page - 1) // per_page)

            query += " ORDER BY event_date DESC LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])

            cursor.execute(query, params)
            events_list = cursor.fetchall()

            cursor.execute(
                "SELECT DISTINCT category FROM events WHERE category IS NOT NULL AND category != '' ORDER BY category"
            )
            categories = [row['category'] for row in cursor.fetchall()]

        return render_template("events.html", events=events_list, categories=categories,
                               search=search, category_filter=category_filter,
                               page=page, total_pages=total_pages)
    except Exception:
        return render_template("events.html", events=[], categories=[],
                               search='', category_filter='', page=1, total_pages=1)

# -----------------------------
# EVENT DETAIL PAGE
# -----------------------------
@app.route("/event/<int:event_id>")
def event_detail(event_id):
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
            event = cursor.fetchone()
            if not event:
                abort(404)

            cursor.execute("SELECT name FROM users WHERE id=%s", (event['organizer_id'],))
            organizer = cursor.fetchone()
            organizer_name = organizer['name'] if organizer else "Unknown"

            cursor.execute("SELECT COUNT(*) AS total FROM registrations WHERE event_id=%s", (event_id,))
            reg_count = cursor.fetchone()['total']

            is_registered = False
            if 'loggedin' in session:
                cursor.execute("SELECT id FROM registrations WHERE user_id=%s AND event_id=%s",
                               (session['id'], event_id))
                is_registered = cursor.fetchone() is not None

        return render_template("event_detail.html", event=event,
                               organizer_name=organizer_name,
                               reg_count=reg_count,
                               is_registered=is_registered)
    except Exception:
        abort(404)

# -----------------------------
# EDIT EVENT
# -----------------------------
@app.route("/edit_event/<int:event_id>")
@login_required
def edit_event_page(event_id):
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
            event = cursor.fetchone()
            if not event:
                abort(404)
            if event['organizer_id'] != session['id'] and session.get('role') != 'admin':
                flash("You do not have permission to edit this event.")
                return redirect(url_for('events'))
        return render_template("edit_event.html", event=event)
    except Exception:
        abort(404)

@app.route("/edit_event/<int:event_id>", methods=["POST"])
@login_required
def edit_event(event_id):
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
            event = cursor.fetchone()
            if not event:
                abort(404)
            if event['organizer_id'] != session['id'] and session.get('role') != 'admin':
                flash("You do not have permission to edit this event.")
                return redirect(url_for('events'))

            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", "").strip()
            price = request.form.get("price", "0")
            event_date = request.form.get("event_date", "")
            event_time = request.form.get("event_time", "")
            venue = request.form.get("venue", "").strip()
            address = request.form.get("address", "").strip()
            gmap_link = request.form.get("gmap_link", "").strip()
            max_participants = request.form.get("max_participants", "100")
            registration_deadline = request.form.get("registration_deadline", "")

            if not title:
                flash("Event title is required.")
                return redirect(url_for('edit_event_page', event_id=event_id))

            flyer = request.files.get("flyer_image")
            filename = event['flyer_image']  # Keep existing

            if flyer and flyer.filename != "":
                if not allowed_file(flyer.filename):
                    flash("Only image files are allowed.")
                    return redirect(url_for('edit_event_page', event_id=event_id))
                original_name = secure_filename(flyer.filename)
                filename = f"{uuid.uuid4().hex}_{original_name}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                flyer.save(filepath)

            cursor.execute(
                """UPDATE events SET title=%s, description=%s, flyer_image=%s, category=%s,
                price=%s, event_date=%s, event_time=%s, venue=%s, address=%s,
                gmap_link=%s, max_participants=%s, registration_deadline=%s
                WHERE id=%s""",
                (title, description, filename, category, price,
                 event_date or None, event_time or None, venue, address,
                 gmap_link, max_participants, registration_deadline or None,
                 event_id)
            )
            mysql.connection.commit()

        flash("Event updated successfully!")
        return redirect(url_for('event_detail', event_id=event_id))
    except Exception:
        flash("An error occurred while updating the event.")
        return redirect(url_for('edit_event_page', event_id=event_id))

# -----------------------------
# DELETE EVENT
# -----------------------------
@app.route("/delete_event/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
            event = cursor.fetchone()
            if not event:
                abort(404)
            if event['organizer_id'] != session['id'] and session.get('role') != 'admin':
                flash("You do not have permission to delete this event.")
                return redirect(url_for('events'))
            if event['flyer_image']:
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], event['flyer_image'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            cursor.execute("DELETE FROM events WHERE id=%s", (event_id,))
            mysql.connection.commit()
        flash("Event deleted successfully!")
    except Exception:
        flash("An error occurred while deleting the event.")
    return redirect(url_for('events'))

# -----------------------------
# REGISTER FOR EVENT
# -----------------------------
@app.route("/register_event/<int:event_id>")
def register_event(event_id):
    if 'loggedin' in session:
        user_id = session['id']
        try:
            with mysql.connection.cursor() as cursor:
                cursor.execute("SELECT max_participants FROM events WHERE id=%s", (event_id,))
                event = cursor.fetchone()
                if not event:
                    flash("Event not found.")
                    return redirect(url_for('events'))

                cursor.execute("SELECT COUNT(*) AS total FROM registrations WHERE event_id=%s", (event_id,))
                current_count = cursor.fetchone()['total']
                if current_count >= event['max_participants']:
                    flash("Sorry, this event is full.")
                    return redirect(url_for('events'))

                cursor.execute("SELECT id FROM registrations WHERE user_id=%s AND event_id=%s",
                               (user_id, event_id))
                if cursor.fetchone():
                    flash("You are already registered for this event.")
                    return redirect(url_for('events'))

                cursor.execute(
                    "INSERT INTO registrations(user_id, event_id, payment_status) VALUES(%s, %s, %s)",
                    (user_id, event_id, "pending")
                )
                mysql.connection.commit()
        except Exception:
            flash("An error occurred during registration.")
            return redirect(url_for('events'))

        flash("You have successfully registered for the event!")
        return redirect(url_for('events'))

    flash("You need to be logged in to register for an event.")
    return redirect(url_for('login_page'))

# -----------------------------
# UNREGISTER FROM EVENT
# -----------------------------
@app.route("/unregister_event/<int:event_id>", methods=["POST"])
@login_required
def unregister_event(event_id):
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("DELETE FROM registrations WHERE user_id=%s AND event_id=%s",
                           (session['id'], event_id))
            mysql.connection.commit()
        flash("You have been unregistered from the event.")
    except Exception:
        flash("An error occurred. Please try again.")
    return redirect(url_for('events'))

# -----------------------------
# ADMIN: DELETE USER
# -----------------------------
@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@role_required('admin')
def delete_user(user_id):
    if user_id == session['id']:
        flash("You cannot delete your own account.")
        return redirect(url_for('admin_dashboard'))
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
            mysql.connection.commit()
        flash("User deleted successfully.")
    except Exception:
        flash("An error occurred while deleting the user.")
    return redirect(url_for('admin_dashboard'))

# -----------------------------
# SERVE UPLOADED IMAGES
# -----------------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)