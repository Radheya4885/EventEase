# EventEase - Project Context

## Overview
EventEase is a Flask-based event management web application. Users can register as organizers, participants, volunteers, or admins. Organizers create events, and participants can register for them.

## Tech Stack
- **Backend:** Python 3 + Flask
- **Database:** MySQL 8.0 (via flask-mysqldb)
- **Frontend:** HTML + CSS (Jinja2 templates)
- **Auth:** Werkzeug password hashing, Flask sessions
- **Config:** python-dotenv (.env files)

## Project Structure
```
EventEase/
├── app.py                  # Main Flask app (all routes and logic)
├── setup_database.py       # Standalone DB setup script
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── .env                    # Local config (NOT in git)
├── .gitignore
├── README.md
├── templates/
│   ├── index.html              # Homepage
│   ├── login.html              # Login form
│   ├── register.html           # Registration form
│   ├── events.html             # List all events
│   ├── create_event.html       # Create event form
│   ├── organizer_dashboard.html
│   ├── participant_dashboard.html
│   ├── volunteer_dashboard.html
│   ├── admin_dashboard.html
│   └── static/                 # CSS, JS, images
└── uploads/                    # Uploaded event flyer images
```

## Database Schema
Three MySQL tables:

### users
| Column | Type | Notes |
|--------|------|-------|
| id | INT AUTO_INCREMENT | Primary key |
| name | VARCHAR(100) | |
| email | VARCHAR(100) UNIQUE | |
| password | VARCHAR(255) | Werkzeug hashed |
| role | ENUM('organizer','volunteer','participant','admin') | |
| created_at | TIMESTAMP | |

### events
| Column | Type | Notes |
|--------|------|-------|
| id | INT AUTO_INCREMENT | Primary key |
| title | VARCHAR(200) | |
| description | TEXT | |
| flyer_image | VARCHAR(255) | Filename in uploads/ |
| category | VARCHAR(100) | |
| price | DECIMAL(10,2) | |
| event_date | DATE | |
| event_time | TIME | |
| venue | VARCHAR(200) | |
| address | VARCHAR(300) | |
| gmap_link | VARCHAR(500) | Google Maps link |
| max_participants | INT | |
| registration_deadline | DATE | |
| organizer_id | INT | FK → users.id |
| created_at | TIMESTAMP | |

### registrations
| Column | Type | Notes |
|--------|------|-------|
| id | INT AUTO_INCREMENT | Primary key |
| user_id | INT | FK → users.id |
| event_id | INT | FK → events.id |
| payment_status | VARCHAR(50) | Default 'pending' |
| registered_at | TIMESTAMP | |
| UNIQUE (user_id, event_id) | | Prevent duplicate registrations |

## Key Routes in app.py
| Route | Method | Function |
|-------|--------|----------|
| `/` | GET | Homepage |
| `/register` | GET/POST | User registration |
| `/login` | GET/POST | User login |
| `/logout` | GET | Logout |
| `/organizer_dashboard` | GET | Organizer dashboard |
| `/participant_dashboard` | GET | Participant dashboard |
| `/volunteer_dashboard` | GET | Volunteer dashboard |
| `/admin_dashboard` | GET | Admin dashboard |
| `/create_event` | GET/POST | Create a new event |
| `/events` | GET | List all events |
| `/register_event/<id>` | GET | Register for event |
| `/uploads/<filename>` | GET | Serve uploaded images |

## Configuration
All config is loaded from `.env` file via python-dotenv:
- `MYSQL_HOST` — MySQL server hostname
- `MYSQL_USER` — MySQL username
- `MYSQL_PASSWORD` — MySQL password
- `MYSQL_DB` — Database name (default: eventease)
- `SECRET_KEY` — Flask secret for sessions

## Auto Database Setup
The app automatically creates the database and all tables on startup via the `ensure_database_exists()` function in app.py. No manual SQL needed.

## Collaboration
- GitHub repo: https://github.com/Radheya4885/Eventease1
- Each developer runs their own local instance with their own MySQL credentials
- Code is shared via git push/pull
- Database data is local to each developer
- Use `/setup` workflow for first-time setup
- Use `/run` workflow to start the app
- Use `/push-changes` and `/pull-changes` workflows for collaboration
