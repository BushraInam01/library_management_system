# 📚 Library Catalog & Borrowing System

A web-based Library Management System built with **Python and Django**. This application helps libraries manage their book catalog, members, borrowing and returning, reservations, overdue fines, and payments through a role-based system.

## ✨ Key Features

### 🔐 Accounts & Authentication
- Member registration and login
- Role-based access for Members and Librarians
- Automatic library card generation
- Separate dashboards for different user roles
- Protected views and authentication controls

### 📖 Book Catalog
- Browse and search books by title, author, or ISBN
- View detailed book information and availability
- Add new books through librarian access
- ISBN lookup using the Open Library API
- API response caching and error handling

### 🔄 Borrowing & Returns
- Borrow available books
- Automatic due-date assignment
- View personal borrowing history
- Librarian-managed book returns
- Automatic book availability updates

### 📌 Reservations
- Reserve books when all copies are borrowed
- FIFO (First In, First Out) reservation queue
- Automatically allocate returned copies to the next waiting member
- Cancel eligible reservations
- Separate member and librarian reservation views

### 💰 Fines & Payments
- Automatic overdue fine calculation
- Record full and partial payments
- Track unpaid, partially paid, and paid fines
- Validate payments against outstanding balances

### ⚙️ Administration
- Django Admin integration
- CSV import support with `django-import-export`
- Administrative management of library records
- Custom admin actions:
  - Send overdue reminder emails (Borrow records)
  - Mark selected fines as fully paid (Fines)
  - Activate / deactivate library cards (Library cards)
- Members created in the admin automatically receive a library card
- Due-date email sent automatically when a book is borrowed (Django signal)

#### CSV import format

In Django Admin > Books > Import, upload a CSV with these columns:

```
isbn,title,author,publisher,publication_year,description,total_copies
```

Books are matched by ISBN: existing books are updated, new ones are created.
`available_copies` is managed automatically. Leave out a column (for example
`description`) if you do not want to change it, because blank cells overwrite existing values.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Django | Web framework |
| Django Templates & Forms | User interface and form handling |
| SQLite | Development database |
| HTML & CSS | Frontend |
| Requests | External API integration |
| Open Library API | ISBN-based book lookup |
| django-import-export | CSV data import |
| python-dotenv | Environment configuration |

## 📁 Project Structure

```text
library_management_system/
│
├── accounts/       # User authentication and library cards
├── borrowing/      # Book borrowing and return management
├── catalog/        # Book catalog and ISBN lookup
├── config/         # Django project configuration
├── fines/          # Fine calculation and payments
├── reservations/   # Book reservation queue
├── static/         # CSS and static assets
├── templates/      # HTML templates
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Getting Started

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/BushraInam01/library_management_system.git
cd library_management_system
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create your local environment file:

```bash
cp .env.example .env
```

Open `.env` in your code editor and configure your Django secret key and other environment settings.

**Important:** Never commit your actual `.env` file or expose your secret key.

### 5. Apply Database Migrations

```bash
python3 manage.py migrate
```

### 6. Create an Administrator Account

```bash
python3 manage.py createsuperuser
```

### 7. Start the Development Server

```bash
python3 manage.py runserver
```

Open the application in your browser:

**Application:** http://127.0.0.1:8000/

**Django Admin:** http://127.0.0.1:8000/admin/

## 🧪 Running Tests

Run the complete test suite:

```bash
python3 manage.py test
```

Run Django system checks:

```bash
python3 manage.py check
```

Check for uncreated model migrations:

```bash
python3 manage.py makemigrations --check --dry-run
```

## 🔒 Security Considerations

- Environment variables are used for sensitive configuration.
- Actual `.env` files and local database files are excluded from Git.
- Authentication and role-based authorization protect restricted operations.
- Database transactions and integrity constraints help maintain data consistency.
- Production deployment requires appropriate HTTPS, secure cookie, SMTP, `DEBUG`, and `ALLOWED_HOSTS` configuration.

## 🎯 Learning Objectives

This project demonstrates practical implementation of:

- Django Class-Based Views (CBVs)
- Authentication and role-based authorization
- Django Forms and ModelForms
- Django ORM relationships and `F()` expressions
- Database transactions and integrity constraints
- External API integration using `requests`
- Django caching
- Date calculations using `timedelta`
- Django signals and email configuration
- Custom Django Admin actions
- CSV import workflows
- Automated testing

## 🔮 Future Improvements

- Production deployment
- Real SMTP integration for due-date notifications
- Automated overdue and upcoming due-date reminders
- Advanced library reports and analytics

## 👩‍💻 Author

**Bushra Inam**

- GitHub: [@BushraInam01](https://github.com/BushraInam01)

---

*Developed as a hands-on Python and Django backend development project.*
