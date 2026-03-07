# 🎉 EventEase - Event Management Platform

A Flask-based event management platform where organizers can create events and participants can register for them.

---

## 🚀 Quick Setup (For New Collaborators)

### Prerequisites
- **Python 3.10+** installed
- **MySQL Server 8.0+** installed and running
- **Git** installed

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd EventEase
```

### Step 2: Create a Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment
**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```
**Windows (CMD):**
```bash
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
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password_here
   MYSQL_DB=eventease
   SECRET_KEY=any-random-string-here
   ```

### Step 6: Run the App
```bash
python app.py
```

The app will **automatically create the database and tables** on first run! 🎉

Open your browser and go to: **http://127.0.0.1:5000**

---

## 📁 Project Structure
```
EventEase/
├── app.py                  # Main Flask application
├── setup_database.py       # Standalone DB setup script (optional)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── .env                    # YOUR local config (not in git!)
├── .gitignore              # Files excluded from git
├── templates/              # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── events.html
│   ├── create_event.html
│   ├── organizer_dashboard.html
│   ├── participant_dashboard.html
│   ├── volunteer_dashboard.html
│   ├── admin_dashboard.html
│   └── static/             # CSS, JS, images
└── uploads/                # Uploaded event flyers
```

---

## 🔧 Troubleshooting

### "Unknown database 'eventease'"
The app now auto-creates the database on startup. If you still see this error:
1. Make sure MySQL Server is **running**
2. Check your `.env` file has the correct `MYSQL_USER` and `MYSQL_PASSWORD`
3. Try running: `python setup_database.py`

### Can't install `mysqlclient`
On Windows, try:
```bash
pip install mysqlclient
```
If that fails, install the [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) first.

### App won't start
- Make sure your virtual environment is **activated** (you should see `(venv)` in your terminal)
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check the `.env` file exists and has correct values

---

## 👥 For Collaborators

- **Never commit your `.env` file** — it contains your local MySQL password
- The `.env.example` file shows what variables you need to set
- Each person uses their own MySQL credentials locally
- The database schema is auto-created, so everyone gets the same tables
