---
description: How to set up the EventEase project on a new machine for the first time
---

# EventEase Project Setup

Follow these steps to set up the project on a new machine:

## Prerequisites
- Python 3.10+ must be installed
- MySQL Server 8.0+ must be installed and running
- Git must be installed

## Setup Steps

// turbo-all

1. Create a virtual environment:
```
python -m venv venv
```

2. Activate the virtual environment:
   - Windows PowerShell: `venv\Scripts\Activate.ps1`
   - Windows CMD: `venv\Scripts\activate.bat`
   - Mac/Linux: `source venv/bin/activate`

3. Install all Python dependencies:
```
pip install -r requirements.txt
```

4. Create the environment file by copying the template:
```
copy .env.example .env
```

5. **IMPORTANT - Manual step:** Edit the `.env` file and set your MySQL credentials:
   - `MYSQL_USER` — your MySQL username (usually `root`)
   - `MYSQL_PASSWORD` — your MySQL password
   - `MYSQL_DB` — leave as `eventease` unless you want a different name
   - `SECRET_KEY` — change to any random string

6. Run the application:
```
python app.py
```

The app will automatically create the database and all tables on first run.

7. Open the website at: http://127.0.0.1:5000

## Troubleshooting

- If `pip install mysqlclient` fails on Windows, install Visual C++ Build Tools first
- If you get a MySQL connection error, make sure MySQL Server is running and your .env credentials are correct
- If you see "Unknown database", just run `python setup_database.py`
