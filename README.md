# 🚛 SGM Drivers — Fleet Management System

A professional UK fleet management web application for SGM Drivers Ltd.  
Compliant with **Driver CPC**, **DVLA**, **HMRC**, and **UK GDPR** regulations.

---

## 📦 Features

| Module | Description |
|--------|-------------|
| 👥 **Drivers** | Full CRUD for driver records — personal info, NI, licence type, salary |
| 🪪 **Licences** | DVLA licence tracking — LGV, PCV, Car/Van with expiry alerts |
| 🎓 **Training & CPC** | Driver CPC periodic training hours (35hr per 5-year cycle) |
| 📋 **Contracts** | Full-time, Part-time, Temporary, Agency contracts |
| 💷 **Payments** | PAYE, National Insurance, pension, BACS payroll records |
| 📁 **Documents** | DBS, CPC Card, Tachograph, Passport, Right to Work archive |
| 📈 **Reports** | CSV export for all data modules |
| 🔑 **Users** | Role-based access: Admin, HR, Driver |

---

## 🚀 Quick Start (Local)

### 1. Clone or extract the project
```bash
cd sgm-drivers
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 5. Run the app
```bash
python app.py
```

Open: **http://localhost:5000**

### Default credentials
| Username | Password | Role |
|----------|----------|------|
| `admin` | `Admin@2024!` | Administrator |
| `hr` | `Hr@2024!` | HR User |

> ⚠️ Change passwords immediately after first login!

---

## ☁️ Hosting on Render.com (FREE)

Render.com offers a free web service tier — no credit card required.

### Steps:
1. Create a free account at [render.com](https://render.com)
2. Click **New → Web Service**
3. Connect your GitHub repository (or upload files)
4. Set these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers=2 --bind=0.0.0.0:$PORT`
   - **Python Version:** 3.11
5. Add environment variable:
   - `SECRET_KEY` = (click "Generate" for a random value)
6. Click **Deploy**

Your app will be live at `https://sgm-drivers.onrender.com`

---

## 🚂 Hosting on Railway.app

1. Create account at [railway.app](https://railway.app)
2. Click **New Project → Deploy from GitHub repo**
3. Add environment variable: `SECRET_KEY` = your secret key
4. Railway auto-detects `railway.json` and deploys

---

## 🐍 Hosting on PythonAnywhere (UK servers)

1. Create free account at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload all files via the Files tab
3. Open a Bash console and run:
```bash
pip install -r requirements.txt
```
4. Go to **Web tab → Add new web app → Flask**
5. Set source code path to `/home/yourusername/sgm-drivers`
6. Set WSGI file to point to `app`
7. Set environment variables in the WSGI config file

---

## 🗄️ Database

The app uses **SQLite** by default (stored in `instance/sgm_drivers.db`).

For production with multiple users, use **PostgreSQL**:

1. Add a PostgreSQL database on your hosting platform
2. Set `DATABASE_URL` environment variable:
   ```
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```
3. Install `psycopg2-binary`:
   ```bash
   pip install psycopg2-binary
   ```

The database is **auto-seeded** with 8 sample drivers and realistic data on first run.

---

## 🔒 Security Notes

- All passwords hashed with **Werkzeug pbkdf2** (bcrypt-equivalent)
- Session management via **Flask-Login** with secure cookies
- CSRF protection via Flask session tokens
- Input validation on all API endpoints
- Role-based access control (Admin / HR / Driver)
- UK GDPR compliance: data stored locally, no third-party data sharing

---

## 📁 Project Structure

```
sgm-drivers/
├── app.py                  # Main Flask application + all routes + models
├── requirements.txt        # Python dependencies
├── Procfile               # Heroku/Render process file
├── render.yaml            # Render.com deployment config
├── railway.json           # Railway.app deployment config
├── runtime.txt            # Python version
├── .env.example           # Environment variables template
├── .gitignore
├── README.md
├── templates/
│   ├── login.html         # Login page
│   └── index.html         # Main app (all pages)
└── static/
    ├── css/
    │   └── app.css        # All styles
    └── js/
        └── app.js         # All JavaScript + API calls
```

---

## 🔧 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/login` | Authenticate user |
| GET | `/api/stats` | Dashboard statistics |
| GET/POST | `/api/drivers` | List / create drivers |
| GET/PUT/DELETE | `/api/drivers/<id>` | Read / update / delete driver |
| GET/POST | `/api/licences` | List / create licences |
| PUT/DELETE | `/api/licences/<id>` | Update / delete licence |
| GET/POST | `/api/training` | List / create training records |
| GET/POST | `/api/contracts` | List / create contracts |
| GET/POST | `/api/payments` | List / create payments |
| GET/POST | `/api/documents` | List / create documents |
| GET | `/api/export/<entity>` | Export CSV (drivers/licences/training/payments/contracts) |
| GET/POST | `/api/users` | List / create users (admin only) |
| GET | `/api/chart/licences` | Chart data for dashboard |

---

## 🇬🇧 UK Compliance

- **Driver CPC**: Tracks 35-hour periodic training cycle per JAUPT requirements
- **DVLA**: LGV (Large Goods Vehicle) and PCV (Passenger Carrying Vehicle) licence categories
- **HMRC**: PAYE tax, Employee/Employer National Insurance, pension deductions
- **UK Employment Law**: Notice periods, holiday entitlement (28 days statutory minimum)
- **GDPR**: Data stored securely, access logged, role-based permissions

---

## 📞 Support

For issues or customisation requests, contact your system administrator.

Built for SGM Drivers Ltd · UK Fleet Management · 2024
