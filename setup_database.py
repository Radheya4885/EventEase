"""
EventEase Database Setup Script
================================
Run this script ONCE when setting up the project on a new machine.
It will create the 'eventease' database and all required tables.

Usage:
    python setup_database.py
"""

import MySQLdb
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "eventease")


def create_database():
    """Connect to MySQL server and create the database if it doesn't exist."""
    print(f"\n🔌 Connecting to MySQL as '{MYSQL_USER}' on '{MYSQL_HOST}'...")

    try:
        conn = MySQLdb.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWORD,
        )
    except MySQLdb.OperationalError as e:
        print(f"\n❌ Could not connect to MySQL: {e}")
        print("\n💡 Possible fixes:")
        print("   1. Make sure MySQL Server is running")
        print("   2. Check your .env file has the correct MYSQL_USER and MYSQL_PASSWORD")
        print(f"   3. Current settings: host={MYSQL_HOST}, user={MYSQL_USER}")
        sys.exit(1)

    cursor = conn.cursor()

    print(f"📦 Creating database '{MYSQL_DB}' if it doesn't exist...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}`")
    cursor.execute(f"USE `{MYSQL_DB}`")

    print("📋 Creating tables...\n")

    # ---- USERS TABLE ----
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
    print("   ✅ Table 'users' ready")

    # ---- EVENTS TABLE ----
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
    print("   ✅ Table 'events' ready")

    # ---- REGISTRATIONS TABLE ----
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
    print("   ✅ Table 'registrations' ready")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n🎉 Database '{MYSQL_DB}' is fully set up and ready to go!")
    print("   You can now run the app with: python app.py\n")


if __name__ == "__main__":
    create_database()
