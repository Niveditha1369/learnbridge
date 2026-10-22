# LearnBridge – Full-Stack Tutoring Marketplace

> *"Connect with the right tutor. Learn with confidence."*

LearnBridge is a modern, full-stack education marketplace inspired by the functional workflows of TeacherOn, built with a refined, trustworthy visual identity, robust relational database architecture, and production deployment configuration for Render and PostgreSQL.

---

## 🎨 Visual Identity & Color Palette

LearnBridge uses an elegant, distraction-free aesthetic tailored for academic trust:

- **Background:** `#F8FAFC`
- **Primary Blue:** `#315B72`
- **Muted Sage Green:** `#82A69A`
- **Main Text:** `#263746`
- **Secondary Text:** `#718096`
- **Cards & Surfaces:** `#FFFFFF`
- **Borders:** `#E2E8F0`
- **Soft Highlights:** `#EDF4F5`

---

## 🚀 Technical Stack

- **Backend:** Python 3.11+, Flask, Flask-SQLAlchemy, Gunicorn WSGI
- **Database:** Hosted PostgreSQL in Production (SQLite in local testing & development)
- **Frontend:** Semantic HTML5, Responsive CSS3, Bootstrap 5.3, Bootstrap Icons, Vanilla JavaScript
- **Authentication:** Session-based authentication, Werkzeug cryptographic password hashing (PBKDF2-SHA256)
- **Security:** Server-side CSRF validation, HTTP-only secure cookies, strict role-based access control (RBAC)
- **Hosting & Infrastructure:** Render Web Service, Managed PostgreSQL Datastore, Render Blueprint (`render.yaml`)

---

## 📂 Project Structure

```
learnbridge/
├── app.py                   # Main Flask application, routes, APIs, and error handlers
├── config.py                # Environment-driven configuration (DB URLs, secrets)
├── extensions.py            # SQLAlchemy database instance
├── models.py                # Database models (User, TutorProfile, Subject, etc.)
├── seed.py                  # Idempotent database seeder (14+ subjects, demo tutors & requests)
├── Procfile                 # Production WSGI entry point (Gunicorn)
├── render.yaml              # Render Blueprint for Web Service + Managed PostgreSQL
├── requirements.txt         # Production Python dependencies
├── .env.example             # Template for local & production environment variables
├── .gitignore               # Ignored files (pycache, local DBs, secrets)
├── static/
│   ├── css/style.css        # Custom responsive styling and theme variables
│   ├── js/main.js           # Client-side form handlers, filters, and modals
│   └── uploads/             # Static profile uploads
├── templates/
│   ├── base.html            # Core layout with navigation, brand logo SVG, and footer
│   ├── index.html           # Homepage with hero search, categories, featured tutors, FAQs
│   ├── tutors.html          # Tutor directory with multi-field search, filters, and pagination
│   ├── tutor_profile.html   # Detailed public tutor profile with request modal
│   ├── find_tuition.html    # Student requirement board & tutor expression of interest
│   ├── login.html           # Authentication sign-in
│   ├── register.html        # Student account registration
│   ├── become_tutor.html    # Dedicated tutor onboarding with credentials & subjects
│   ├── student_dashboard.html # Student enquiry tracking, cancel action, profile edit
│   ├── tutor_dashboard.html # Tutor enquiries, accept/reject workflow, profile editor
│   ├── about.html           # Platform mission and educational principles
│   ├── contact.html         # User inquiry and support form
│   ├── privacy.html         # Privacy policy & data protection terms
│   ├── terms.html           # Terms of service & marketplace rules
│   ├── 404.html             # Friendly not-found error page
│   └── 500.html             # Internal server error page
└── tests/
    ├── conftest.py          # Pytest fixtures and in-memory test database setup
    ├── test_pages.py        # Static route and navigation tests
    ├── test_auth.py         # Authentication and RBAC tests
    ├── test_tutors.py       # Tutor discovery and filter tests
    ├── test_requests.py     # Tuition request lifecycle tests (send, accept, cancel)
    ├── test_requirements.py # Student requirements and tutor responses
    └── test_suite.py        # Unittest test runner
```

---

## ⚡ Core Features

1. **Tutor Discovery & Multi-Param Filtering:**
   - Filter by subject, tutor name/keyword, city, teaching mode (Online / In-Person), budget range (Min/Max INR), experience, language, and student level.
   - Sort by lowest fee, highest fee, or years of experience.
   - Full server-side pagination with clean URLs.

2. **Tutor Profiles & Privacy:**
   - Displays qualifications, teaching philosophy, subjects, hourly rates, and availability.
   - No sensitive information (email addresses, phone numbers, password hashes) is leaked publicly.

3. **Tuition Request Lifecycle:**
   - Students submit direct tuition enquiries specifying subject, level, mode, offered budget, and schedule.
   - Real-time status states: `pending`, `accepted`, `rejected`, `cancelled`.
   - Students can cancel pending requests; tutors can accept or reject requests assigned to them.

4. **Student Requirements Board (Find Tuition):**
   - Students can post open learning requirements.
   - Tutors can browse open requirements and submit proposals with their offered hourly fee and teaching methodology.

5. **Role-Based Dashboards:**
   - **Student Dashboard:** Track sent enquiries, cancel pending requests, manage posted requirements, and edit account profile.
   - **Tutor Dashboard:** Track incoming enquiries with 1-click Accept / Reject, profile completeness indicator, profile editor, and open student requirements feed.

---

## 🛠️ Local Setup & Running Locally

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd learnbridge
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize and Seed the Database:**
   ```bash
   python seed.py
   ```

5. **Start the local server:**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
python -m unittest tests/test_suite.py
```
Or with pytest:
```bash
pytest -v
```

---

## 🌐 Production Deployment on Render

This project is fully configured for automated deployment to **Render** using Blueprint Infrastructure-as-Code (`render.yaml`).

### Deployment Steps:
1. Push your repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** > **Blueprint**.
3. Connect your GitHub repository.
4. Render detects `render.yaml` and provisions:
   - A managed **PostgreSQL** database (`learnbridge-db`).
   - A Python **Web Service** (`learnbridge`) running Gunicorn.
5. Environment variables `DATABASE_URL` and `SECRET_KEY` are automatically configured.
6. Build command runs `pip install -r requirements.txt && python seed.py` to ensure all subjects and initial demo profiles are seeded safely and idempotently.
7. Render verifies the service with the health check at `/healthz`.
