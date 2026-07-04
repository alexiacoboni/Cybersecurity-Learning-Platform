# CyberLabs

CyberLabs is an educational cybersecurity training platform built with Flask. It lets users practice recognizing and defending against common web vulnerabilities in a safe, local, simulated environment — no real systems are ever targeted.

Each lab pairs a **vulnerable implementation** with a **secure implementation** of the same feature, so learners can directly compare what breaks and what fixes it.

> ⚠️ **Educational use only.** All attacks are simulated locally against this application's own data. Do not repurpose any payload or technique against systems you do not own or have explicit permission to test.

---

## Live Demo

**[https://cybersecurity-learning-platform-5y8y.onrender.com](https://cybersecurity-learning-platform-5y8y.onrender.com)**

> ⏱️ Hosted on Render's free tier — the instance spins down after periods of inactivity, so the **first request may take up to ~50 seconds** to wake it back up. Subsequent requests are fast.
>
> Note: the free-tier demo uses SQLite on ephemeral storage. Accounts created by visitors may be reset on redeploy/restart. See [Deployment](#deployment) for a persistent database option.

---

## Features

- **User accounts** — registration, login/logout, session-based auth (Flask-Login)
- **Interactive labs**:
  - **SQL Injection** — compare an unsafe, string-concatenated query against a parameterized/prepared statement
  - **Cross-Site Scripting (XSS)** — reflected and stored XSS, with vulnerable (`|safe`) vs. escaped output
  - **Brute Force** — simulate repeated login attempts against an unprotected login vs. a rate-limited/lockout-protected login
- **Quizzes** — a 5-question knowledge check per lab, scored and stored, submittable once
- **Progress tracking** — completion percentage, total score, badges/achievements
- **Personal activity log** — history of lab runs, payloads, results, and scores, shown in local (Romania) time
- **PDF report export** — download a personal progress report
- **Admin panel** — user management (create/delete accounts), platform-wide statistics, most common payloads, recent attacks/logins, full security log
- **CSRF protection** on all forms (Flask-WTF)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Auth | Flask-Login |
| ORM / DB | Flask-SQLAlchemy, SQLite (dev) / PostgreSQL (production, optional) |
| Forms / CSRF | Flask-WTF |
| Frontend | Jinja2 templates, Bootstrap 5.3.3, Bootstrap Icons |
| Charts | Chart.js |
| Password hashing | Werkzeug security |
| Production server | Gunicorn |
| Hosting | Render (or any Python-compatible host) |

---

## Project Structure

```
cyberLabs/
├── app.py                 # App factory, blueprint/extension registration, seed data, ro_time filter
├── config.py               # Configuration (secret key, DB URI, log dir, lockout settings)
├── requirements.txt
├── database.db              # SQLite database (auto-created, gitignored)
├── models/
│   ├── user.py               # User model
│   ├── lab.py                 # Lab model
│   ├── progress.py             # Progress model
│   ├── quiz.py                  # QuizAttempt model
│   └── ...                       # Log, Badge
├── routes/
│   ├── auth.py               # /login, /register, /logout
│   ├── labs.py                 # dashboard, sql/xss/bruteforce labs, quiz, activity, report
│   └── admin.py                 # admin panel, user create/delete
├── utils/
│   ├── helpers.py             # lab_event logging, shared helpers
│   ├── security.py             # brute-force simulation, rate limiting, admin_required
│   ├── quiz.py                   # quiz question bank / scoring
│   └── report.py                  # PDF report generation
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
├── templates/
│   ├── layout.html            # base template, navbar, flash messages
│   ├── login.html / register.html
│   ├── dashboard.html
│   ├── sql_lab.html / xss_lab.html / bruteforce_lab.html
│   ├── quiz.html
│   ├── activity.html
│   └── admin.html
└── logs/
    └── app.log                # rotating application log (gitignored)
```

---

## Getting Started (Local Development)

### Prerequisites

- Python 3.10+
- pip
- git

### Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd cyberLabs
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

> **Windows users:** the app converts timestamps to Romania time using `zoneinfo`, which relies on the `tzdata` package (not bundled with Python on Windows). If you see `ModuleNotFoundError: No module named 'tzdata'`, run:
> ```bash
> pip install tzdata
> ```

### Running the app

```bash
python app.py
```

The app starts at:

```
http://127.0.0.1:5000
```

On first run, the database, tables, default labs, and a default admin account are created automatically.

### Default admin account

| Username | Password |
|---|---|
| `admin` | `admin123` |

> Change this password (or the seeded credentials in `app.py`) before any non-local/shared use.

### Database CLI command

To reset the database to a clean state with default labs and admin account:

```bash
flask --app app init-db
```

---

## Configuration

Environment variables (defaults live in `config.py`, override for production):

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-only-change-before-production` | Flask session/CSRF signing key — **must** be overridden in any real deployment |
| `DATABASE_URL` | `sqlite:///database.db` | SQLAlchemy database URI (swap for a PostgreSQL URL in production) |

Other settings (edit directly in `config.py`):

- `MAX_LOGIN_ATTEMPTS` — attempts allowed before lockout in the Brute Force lab (default `5`)
- `LOCKOUT_SECONDS` — lockout duration in seconds (default `60`)
- `LOG_DIR` — directory for the rotating application log file

---

## Timestamps & Timezone

All timestamps are stored in the database as **UTC** (`datetime.utcnow()`), which is best practice for portability. A Jinja filter (`ro_time`), registered in `app.py`, converts UTC to Europe/Bucharest time (automatically handling EET/EEST daylight saving) wherever a log timestamp is rendered — dashboard, activity, admin pages, and the PDF report.

```python
app.jinja_env.filters["ro_time"] = to_romania_time
```

```html
{{ log.timestamp | ro_time }}
```

---

## Deployment

The app deploys to any platform that runs Python web services. **Render** is a straightforward free option:

### 1. Prepare the repo

```bash
pip install gunicorn
pip freeze > requirements.txt
```

Add a `.gitignore` so local data and secrets never get committed:

```
database.db
logs/
venv/
__pycache__/
*.pyc
.env
```

Push to GitHub:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

### 2. Create the Render Web Service

1. Sign in to [render.com](https://render.com) (GitHub login works)
2. **Dashboard → New → Web Service**
3. Connect your GitHub repo

### 3. Service settings

| Field | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Instance Type | Free |

### 4. Environment variables

| Key | Value |
|---|---|
| `SECRET_KEY` | a random value, e.g. from `python -c "import secrets; print(secrets.token_hex(32))"` |
| `PYTHON_VERSION` | your local Python version, e.g. `3.12.0` |

Click **Create Web Service** — Render builds and deploys automatically, and redeploys on every push to `main`.

### 5. Optional: persistent database (PostgreSQL)

Render's free-tier disk is **ephemeral** — SQLite data resets on redeploy/restart. For a demo this is usually fine, but for persistence:

1. Render → **New → PostgreSQL** (free tier available)
2. Copy the **Internal Database URL**
3. Set it as `DATABASE_URL` on the web service's environment variables
4. Add the Postgres driver:
   ```bash
   pip install psycopg2-binary
   pip freeze > requirements.txt
   ```

No code changes needed — SQLAlchemy reads `DATABASE_URL` automatically via `config.py`.

---

## Security Notes

- Passwords are hashed with Werkzeug's password hashing utilities — never stored in plain text.
- All state-changing forms include CSRF tokens via Flask-WTF.
- The "vulnerable" code paths in each lab (raw SQL string building, `|safe` rendering, unlimited login attempts) are **intentionally insecure** for demonstration purposes only, and operate solely on local, disposable, in-app data.
- Admin-only routes are protected by an `admin_required` decorator tied to the authenticated user's role.

---

## Roadmap / Ideas

- Additional labs (CSRF, insecure deserialization, path traversal)
- Per-user difficulty progression / hints
- Multi-language support
- Docker setup for one-command local deployment

---

## License

Specify your license here (e.g. MIT).
