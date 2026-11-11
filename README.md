
# 📚 Library Catalog & Borrowing System

A web-based Library Management System built with **Python and Django**. This application helps libraries manage their book catalog, members, borrowing and returning, reservations, overdue fines, and payments through a role-based system.

## ✨ Key Features

### 🔐 Accounts & Authentication
- Member registration and login
- Role-based access for Members and Librarians
- Separate dashboards for different user roles
- Automatic library card generation
- Superuser and librarian access management
- Protected views and authentication controls

### 📖 Book Catalog
- Browse and search books by title, author, or ISBN
- View detailed book information and availability
- Add and manage books through librarian access
- ISBN lookup using the Open Library API
- API response caching and error handling
- ISBN format validation
- Automatic book stock management

### 🔄 Borrowing & Returns
- Borrow available books
- Automatic due-date assignment (14 days)
- View personal borrowing history
- Librarian-managed book returns
- Automatic book availability updates
- Safe borrowing operations using database transactions
- Stock consistency checks to prevent incorrect copy counts

### 📌 Reservations
- Reserve books when all copies are borrowed
- FIFO (First In, First Out) reservation queue
- Automatically allocate returned copies to the next waiting member
- Three-day reservation holding period for READY reservations
- Expired reservation processing through a Django management command
- Automatic allocation to the next waiting member after cancellation or expiry
- Cancel eligible reservations
- Separate member and librarian reservation views
- Prevent duplicate and unnecessary reservations

Run the reservation expiry command manually:

```bash
python3 manage.py expire_reservations
```

### 💰 Fines & Payments
- Automatic overdue fine calculation
- Configurable daily fine rate
- Estimated fine display for overdue books
- Record full and partial payments
- Track unpaid, partially paid, and paid fines
- Validate payments against outstanding balances
- Preserve fine payment records

The daily fine rate can be configured using `FINE_RATE_PER_DAY` in Django settings.

### ⚙️ Administration
- Django Admin integration
- CSV import support with `django-import-export`
- Administrative management of library records
- Custom admin actions:
  - Send overdue reminder emails
  - Mark selected fines as fully paid
  - Activate or deactivate library cards
- Automatic library card creation for members registered through admin
- Due-date email notification when a book is borrowed
- Protected borrowing records to prevent direct admin modifications that bypass stock management
- Safe reservation cancellation through admin actions
- Book stock validation during admin updates and CSV imports

#### CSV Import Format

In Django Admin → Books → Import, upload a CSV with these columns:

```csv
isbn,title,author,publisher,publication_year,description,total_copies
```

Books are matched by ISBN:
- Existing books are updated.
- New books are created.
- Available copies are managed automatically.
- Stock adjustments respect active borrowing records and READY reservations.

Leave out a column if you do not want to update it. Blank cells may overwrite existing values.

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
├── reservations/   # Reservation queue and expiry management
├── static/          # CSS and static assets
├── templates/       # HTML templates
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

- **Application:** http://127.0.0.1:8000/
- **Django Admin:** http://127.0.0.1:8000/admin/

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

Process expired reservations:

```bash
python3 manage.py expire_reservations
```

## 🔒 Security Considerations

- Environment variables are used for sensitive configuration.
- Actual `.env` files and local database files are excluded from Git.
- Authentication and role-based authorization protect restricted operations.
- Database transactions and integrity constraints help maintain data consistency.
- Protected member records preserve borrowing and reservation history.
- Admin actions use application services to maintain stock and reservation consistency.
- Production deployment requires appropriate HTTPS, secure cookies, SMTP, `DEBUG`, and `ALLOWED_HOSTS` configuration.

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
- Reservation queue management and expiry handling
- Automated testing

## 🔮 Future Improvements

- Production deployment
- Real SMTP integration for due-date notifications
- Automatic scheduling of reservation expiry processing
- Automated overdue and upcoming due-date reminders
- Advanced library reports and analytics

## 👩‍💻 Author

**Bushra Inam**

- GitHub: [@BushraInam01](https://github.com/BushraInam01)

---

*Developed as a hands-on Python and Django backend development project.*
