# 📊 Student Result API

A production-style REST API built with **Django REST Framework** that automatically generates student result PDFs and delivers them to students via email. Simulates the result distribution systems used by real universities and institutions.

---

## ✨ Features 

- 🔗 Full REST API with Django REST Framework
- 📄 Auto-generates formatted PDF result cards per student
- 📧 Emails result PDFs directly to student email addresses
- 🗄️ Django ORM for clean data modeling 
- ✅ JSON responses for all endpoints
- 🔒 Environment-based email configuration (no hardcoded credentials)

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| Framework | Django, Django REST Framework |
| PDF Generation | ReportLab / WeasyPrint |
| Email | Django SMTP Email Backend |
| Database | SQLite (Django default) |

---

## 📁 Project Structure

```
student-result-api/
└── drfproj/
    ├── manage.py
    ├── drfproj/          # Project settings & URLs
    ├── results/          # Core app — models, views, serializers
    │   ├── models.py     # Student & Result models
    │   ├── views.py      # API views
    │   ├── serializers.py
    │   ├── urls.py
    │   └── utils.py      # PDF generation & email logic
    └── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip
- Gmail account (for SMTP email)

### Installation

```bash
# Clone the repo
git clone https://github.com/senseihx4/student-result-api-with-pdf-send-to-email.git
cd student-result-api-with-pdf-send-to-email/drfproj

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

### Environment Setup

Create a `.env` file inside `drfproj/`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SECRET_KEY=your-django-secret-key
DEBUG=True
```

> ⚠️ Use a [Gmail App Password](https://support.google.com/accounts/answer/185833), not your main Gmail password.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/results/` | List all student results |
| `GET` | `/api/results/<id>/` | Get result by student ID |
| `POST` | `/api/results/` | Add a new student result |
| `POST` | `/api/results/<id>/send/` | Generate PDF & email it to student |

---

## 🔄 How It Works

```
POST /api/results/<id>/send/
        │
        ▼
  Fetch student data from DB
        │
        ▼
  Generate PDF result card
        │
        ▼
  Attach PDF to email
        │
        ▼
  Send to student's email via SMTP
```

---

## 🔮 Planned Improvements

- [ ] JWT authentication for secure endpoints
- [ ] Bulk result sending (send to all students at once)
- [ ] Result grade calculation (GPA/percentage)
- [ ] Admin dashboard UI
- [ ] Deploy to Railway / Render

---

## 👨‍💻 Author

**Kartik Sharma** — [GitHub](https://github.com/senseihx4) · [LinkedIn](https://www.linkedin.com/in/kartik-sharma-023a85322/)
