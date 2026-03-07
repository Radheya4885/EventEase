# 🎉 EventEase - Event Management Platform

A Flask-based event management platform where organizers can create events and participants can register for them.

**🔗 Repository:** [github.com/Radheya4885/EventEase](https://github.com/Radheya4885/EventEase)

---

## 🚀 Quick Setup (For New Collaborators)

### Prerequisites
- **Python 3.10+** installed
- **MySQL Server 8.0+** installed and running
- **Git** installed

### Step 1: Clone the Repository
```bash
git clone https://github.com/Radheya4885/EventEase.git
cd EventEase
```

### Step 2: Create a Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment
**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```
**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```
**Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

> ⚠️ **Note for Windows users:** If `mysqlclient` fails to install, you may need to install [MySQL Connector/C](https://dev.mysql.com/downloads/connector/c/) or install via: `pip install mysqlclient` after installing the Visual C++ Build Tools.

### Step 5: Configure Your Environment
1. Copy the example env file:
   ```bash
   copy .env.example .env       # Windows
   cp .env.example .env         # Mac/Linux
   ```
2. Edit `.env` and fill in **YOUR** MySQL credentials:
   ```env
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password_here
   MYSQL_DB=eventease
   SECRET_KEY=any-random-string-here
   ```

### Step 6: Set Up the Database
```bash
python setup_database.py
```
This will create the `eventease` database and all required tables automatically.

### Step 7: Run the App
```bash
python app.py
```

Open your browser and go to: **http://127.0.0.1:5000** 🎉

---

## 📁 Project Structure
```
EventEase/
├── app.py                  # Main Flask application (all routes & logic)
├── setup_database.py       # Database setup script (run once on new machine)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── .env                    # YOUR local config (⚠️ not tracked by git)
├── .gitignore              # Files excluded from git
├── README.md               # This file
├── templates/              # HTML templates (Jinja2)
│   ├── index.html          # Landing page
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   ├── events.html         # Event listing page
│   ├── create_event.html   # Create new event form
│   ├── organizer_dashboard.html
│   ├── participant_dashboard.html
│   ├── volunteer_dashboard.html
│   ├── admin_dashboard.html
│   └── static/css/         # Stylesheets
└── uploads/                # Uploaded event flyer images (runtime)
```

---

## 👥 Collaboration Workflow

### Getting Latest Changes
```bash
git pull origin main
```

### Making Changes
```bash
git add .
git commit -m "Describe what you changed"
git push origin main
```

### ⚠️ Important Rules
- **Never commit your `.env` file** — it contains your local MySQL password
- The `.env.example` file shows what variables are needed
- Each person uses their own MySQL credentials locally
- Always `git pull` before starting new work to avoid merge conflicts

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| **"Unknown database 'eventease'"** | Run `python setup_database.py` to create the database |
| **`mysqlclient` won't install** | Install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) first, then retry |
| **App won't start** | Check: venv activated? Dependencies installed? `.env` file exists? |
| **MySQL connection refused** | Make sure MySQL Server is running on your machine |
| **"Access denied" for MySQL** | Double-check `MYSQL_USER` and `MYSQL_PASSWORD` in your `.env` file |

---

## 🛠️ Tech Stack
- **Backend:** Python Flask
- **Database:** MySQL 8.0+
- **Templating:** Jinja2
- **Auth:** Werkzeug (password hashing)
- **Config:** python-dotenv
