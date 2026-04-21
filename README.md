# 🏛️ Tumakuru City Corporation — Public Issue Reporting System

**A professional Django-based civic engagement portal for Tumakuru City, Karnataka.**

---

## 📋 Overview

The **TCC Civic Issue Portal** empowers citizens of Tumakuru to report civic problems directly to the city corporation. Citizens earn **5 Civic Points** per approved report, and upon reaching **100 points**, they receive an official **Best Citizen Certificate** — downloadable as a professional PDF.

---

## ✨ Key Features

| Feature | Details |
|---|---|
| 🏙️ **Issue Reporting** | Submit civic issues with photos, location, ward, and priority |
| ⭐ **Points System** | Earn 5 points per submitted report automatically |
| 🏆 **Best Citizen Award** | Auto-generated at every 100-point milestone |
| 📄 **PDF Certificate** | Professional A4 landscape PDF certificate with official design |
| 📊 **Dashboard** | Personal dashboard with stats, progress, and certificate list |
| 🥇 **Leaderboard** | Top citizens ranked by civic points |
| 🔍 **Issue Tracker** | Filter and search all reported issues citywide |
| 👑 **Admin Panel** | Full admin control over reports, citizens, status updates |
| 🗺️ **35 Wards** | Full coverage of all Tumakuru wards |
| 📸 **Photo Upload** | Citizens can upload up to 2 photos per issue |
| 💬 **Comments** | Public & official commenting on reports |
| 👍 **Upvotes** | Citizens can upvote issues to signal community priority |

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# 1. Navigate to project
cd tumakuru_civic

# 2. Run automated setup
chmod +x setup.sh
./setup.sh

# 3. Start the server
source venv/bin/activate
python manage.py runserver
```

### Manual Setup (if script fails)

```bash
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py makemigrations accounts
python manage.py makemigrations reports
python manage.py migrate

python manage.py loaddata categories_fixture.json

python manage.py createsuperuser

python manage.py runserver
```

---

## 🌐 URLs

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Home Page |
| `http://127.0.0.1:8000/accounts/register/` | Citizen Registration |
| `http://127.0.0.1:8000/accounts/login/` | Citizen Login |
| `http://127.0.0.1:8000/dashboard/` | Citizen Dashboard |
| `http://127.0.0.1:8000/reports/submit/` | Submit an Issue |
| `http://127.0.0.1:8000/reports/` | All Reports |
| `http://127.0.0.1:8000/leaderboard/` | Citizens Leaderboard |
| `http://127.0.0.1:8000/admin/` | Admin Panel |

---

## 🎯 Points & Certificate System

```
Each Valid Report Submitted → +5 Civic Points
────────────────────────────────────────────
0  pts → New Citizen
20 pts → Bronze Citizen
50 pts → Silver Citizen
100 pts → Gold Citizen + 🏆 BEST CITIZEN CERTIFICATE
200 pts → Platinum Citizen + 🏆 Second Certificate
...and so on every 100 points
```

The **Best Citizen Certificate** is:
- Auto-generated when the 100-point threshold is crossed
- Displayed on the citizen's dashboard
- Downloadable as a **professional PDF** (requires `reportlab`)
- Has a unique certificate number format: `TCC-BC-YYYY-NNNN-M1`

---

## 🗂️ Project Structure

```
tumakuru_civic/
├── manage.py
├── requirements.txt
├── setup.sh                    ← One-click setup
├── categories_fixture.json     ← 12 pre-built issue categories
│
├── tumakuru_civic/             ← Django project config
│   ├── settings.py
│   └── urls.py
│
├── accounts/                   ← Citizen management
│   ├── models.py               ← CitizenProfile, CitizenCertificate
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── reports/                    ← Issue reporting
│   ├── models.py               ← IssueReport, IssueCategory, etc.
│   ├── views.py                ← Core logic + points + certificates
│   ├── forms.py
│   ├── urls.py
│   └── utils.py                ← PDF certificate generator
│
├── static/
│   ├── css/main.css            ← Full custom professional CSS
│   └── js/main.js
│
└── templates/
    ├── base.html               ← Gov strip, navbar, footer
    ├── home.html               ← Hero + stats + categories
    ├── accounts/
    │   ├── login.html
    │   ├── register.html
    │   └── profile.html
    └── reports/
        ├── dashboard.html
        ├── report_form.html
        ├── report_detail.html
        ├── report_list.html
        ├── my_reports.html
        ├── leaderboard.html
        └── certificate.html
```

---

## ⚙️ Configuration (`settings.py`)

```python
POINTS_PER_REPORT = 5           # Points per approved report
POINTS_FOR_CERTIFICATE = 100    # Points needed for certificate
CITY_NAME = "Tumakuru"
```

---

## 🔒 Admin Features

Login to `/admin/` with your superuser credentials to:
- **View & manage** all citizen reports
- **Update report status** (Pending → Acknowledged → In Progress → Resolved)
- **Assign reports** to departments
- **Verify citizens**
- **Manage issue categories**
- **View all certificates issued**

---

## 🖨️ PDF Certificate

Requires `reportlab`:
```bash
pip install reportlab
```

The certificate includes:
- Official Tumakuru City Corporation header in Kannada + English
- Citizen name, ward, certificate number
- Points milestone achieved
- Municipal Commissioner & Mayor signature lines
- Official gold-and-navy government design

---

## 🎨 Design

- **Aesthetic**: Authoritative Indian Government + Modern Civic Portal
- **Colors**: Navy (#0D2137), Saffron (#E8611A), Gold (#C9A84C), India Green (#138808)
- **Fonts**: Playfair Display (headings) + DM Sans (body)
- **Tricolor accents** throughout — saffron, white, green

---

## 📱 Responsive

Fully responsive — works on mobile, tablet, and desktop.

---

*Built for Tumakuru City Corporation, Karnataka — ತುಮಕೂರು ನಗರ ನಿಗಮ*
