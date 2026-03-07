from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import MySQLdb
import os

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

mysql = MySQL(app)


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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE SET NULL
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
                UNIQUE KEY unique_registration (user_id, event_id)
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

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    
    # Hash the password for security
    hashed_password = generate_password_hash(password)

    with mysql.connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered. Please login.")
            return redirect(url_for('login_page'))

        cursor.execute(
            "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
            (name, email, hashed_password, role)
        )
        mysql.connection.commit()

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

    email = request.form['email']
    password = request.form['password']

    with mysql.connection.cursor() as cursor:
        cursor.execute("SELECT id, name, email, password, role FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

    # Check if user exists and password hash matches
    if user and check_password_hash(user[3], password):
        # Store user info in session
        session['loggedin'] = True
        session['id'] = user[0]
        session['name'] = user[1]
        session['role'] = user[4]

        role = user[4]

        # Redirect based on role
        if role == "organizer":
            return redirect(url_for("organizer_dashboard")) # Assuming you'll create these routes
        elif role == "volunteer":
            return redirect(url_for("volunteer_dashboard"))
        elif role == "participant":
            return redirect(url_for("participant_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for('home')) # Fallback

    flash("Invalid email or password")
    return redirect(url_for('login_page'))

# -----------------------------
# DASHBOARD ROUTES
# -----------------------------
@app.route("/organizer_dashboard")
def organizer_dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login_page'))
    return render_template("organizer_dashboard.html")

@app.route("/volunteer_dashboard")
def volunteer_dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login_page'))
    return render_template("volunteer_dashboard.html")

@app.route("/participant_dashboard")
def participant_dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login_page'))
    return render_template("participant_dashboard.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login_page'))
    return render_template("admin_dashboard.html")

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
def create_event_page():
    if 'loggedin' not in session:
        flash("Please login to create an event.")
        return redirect(url_for('login_page'))
    return render_template("create_event.html")

# -----------------------------
# CREATE EVENT
# -----------------------------
@app.route("/create_event", methods=["POST"])
def create_event():

    title = request.form["title"]
    description = request.form["description"]
    category = request.form["category"]
    price = request.form["price"]
    event_date = request.form["event_date"]
    event_time = request.form["event_time"]
    venue = request.form["venue"]
    address = request.form["address"]
    gmap_link = request.form["gmap_link"]
    max_participants = request.form["max_participants"]
    registration_deadline = request.form["registration_deadline"]

    flyer = request.files.get("flyer_image")

    filename = ""

    if flyer and flyer.filename != "":
        filename = secure_filename(flyer.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        flyer.save(filepath)

    with mysql.connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO events
            (title, description, flyer_image, category, price,
            event_date, event_time, venue, address,
            gmap_link, max_participants, registration_deadline, organizer_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                title, description, filename, category, price,
                event_date, event_time, venue, address,
                gmap_link, max_participants, registration_deadline,
                session.get('id')
            )
        )
        mysql.connection.commit()

    flash("Event Created Successfully!")
    return redirect(url_for('events'))

# -----------------------------
# SHOW EVENTS PAGE
# -----------------------------
@app.route("/events")
def events():

    with mysql.connection.cursor() as cursor:
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()

    return render_template("events.html", events=events)

# -----------------------------
# REGISTER FOR EVENT
# -----------------------------
@app.route("/register_event/<int:event_id>")
def register_event(event_id):

    # Check if user is logged in
    if 'loggedin' in session:
        user_id = session['id']

        with mysql.connection.cursor() as cursor:
            # Check if already registered
            cursor.execute("SELECT * FROM registrations WHERE user_id = %s AND event_id = %s", (user_id, event_id))
            registration = cursor.fetchone()
            if registration:
                flash("You are already registered for this event.")
                return redirect(url_for('events'))

            # Register the user
            cursor.execute(
                "INSERT INTO registrations(user_id,event_id,payment_status) VALUES(%s,%s,%s)",
                (user_id, event_id, "pending")
            )
            mysql.connection.commit()

        flash("You have successfully registered for the event!")
        return redirect(url_for('events'))

    flash("You need to be logged in to register for an event.")
    return redirect(url_for('login_page'))

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