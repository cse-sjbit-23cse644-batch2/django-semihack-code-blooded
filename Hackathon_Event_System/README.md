# 🎯 EventHub — Hackathon Event Lifecycle & Certification System

A full-stack Django application for managing competitive events with QR attendance, engagement scoring, and PDF certificate generation.

---

## 🚀 Quick Start

### Option A — Automated Setup (Recommended)

```bash
cd Hackathon_Event_System
chmod +x setup.sh
./setup.sh
cd event_system
python manage.py runserver
```

### Option B — Manual Setup

```bash
# 1. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
cd event_system
python manage.py makemigrations
python manage.py migrate

# 4. Create admin user
python manage.py createsuperuser

# 5. Start server
python manage.py runserver
```

---

## 🌐 URLs

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/` | Home page |
| `http://127.0.0.1:8000/register/` | Participant registration |
| `http://127.0.0.1:8000/success/<id>/` | Registration success + QR code |
| `http://127.0.0.1:8000/attendance/<id>/` | QR scan → mark attendance |
| `http://127.0.0.1:8000/certificate/<id>/` | Certificate preview page |
| `http://127.0.0.1:8000/certificate/<id>/download/` | Download PDF certificate |
| `http://127.0.0.1:8000/verify/` | Certificate verification |
| `http://127.0.0.1:8000/verify/<cert_uuid>/` | Direct certificate verify |
| `http://127.0.0.1:8000/admin/` | Django admin panel |

---

## 🏗️ Project Structure

```
Hackathon_Event_System/
├── requirements.txt
├── setup.sh
├── media/
│   └── qr_codes/              # Auto-generated QR code images
└── event_system/
    ├── manage.py
    ├── db.sqlite3             # Created after migrations
    ├── event_system/
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    └── core/
        ├── models.py          # Event, Participant models
        ├── views.py           # All view logic
        ├── urls.py            # URL routing
        ├── admin.py           # Admin configuration
        ├── templates/
        │   ├── home.html
        │   ├── register.html
        │   ├── success.html
        │   ├── attendance.html
        │   ├── certificate.html
        │   └── verify.html
        ├── static/
        │   ├── style.css
        │   └── script.js
        └── migrations/
```

---

## 📊 System Flow

```
Admin creates Events (Django Admin)
        ↓
User fills Registration Form (/register/)
        ↓
QR Code generated → stored in media/qr_codes/
        ↓
User shown QR code (/success/<id>/)
        ↓
QR scanned at event → /attendance/<id>/
        ↓
attended=True, score=random(70–100) assigned
        ↓
Level assigned:
  90–100 → Gold 🥇
  75–89  → Silver 🥈
  <75    → Participation 🥉
        ↓
PDF Certificate generated (reportlab) + downloaded
        ↓
Anyone can verify at /verify/<certificate_id>/
```

---

## 🧱 Database Models

### Event
| Field | Type |
|-------|------|
| id | AutoField |
| name | CharField (unique) |

### Participant
| Field | Type |
|-------|------|
| id | AutoField |
| name | CharField |
| email | EmailField (unique) |
| event | ForeignKey → Event |
| attended | BooleanField |
| score | IntegerField (nullable) |
| certificate_id | UUIDField (auto, unique) |
| qr_code | ImageField |
| registered_at | DateTimeField |

---

## 🔐 Admin Credentials (setup.sh default)

- **URL:** http://127.0.0.1:8000/admin/
- **Username:** `admin`
- **Password:** `admin123`

> Change these in production!

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| Django | Web framework |
| qrcode[pil] | QR code generation |
| reportlab | PDF certificate generation |
| Pillow | Image processing |

---

## 🎯 CO Mapping

| CO | How Demonstrated | SDG Target |
|---|---|---|
| **CO1** | MVT routing for registration/certificate URLs | SDG 4 |
| **CO2** | Participant model + validated forms | SDG 4 |
| **CO3** | Reusable base.html + responsive views | SDG 4 |
| **CO4** | ReportLab PDF with conditional logic | SDG 16 |
| **CO5** | AJAX attendance toggle | SDG 4 |

---

## 📝 SDG Justification

> "Our Event Lifecycle system advances **SDG 4: Quality Education (Target 4.5)** by digitizing academic event management — ensuring equitable access to registration and verified certificates. The conditional PDF issuance (**CO4**) ensures accountability and fair verification of participation, supporting transparent institutions."
