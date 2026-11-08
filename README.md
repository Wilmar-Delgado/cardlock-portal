# Card-Lock Portal

A multi-company card-lock management portal built with Django and PostgreSQL for managing companies, employees, fuel cards, assignments, stations, fuel transactions, invoices, and Stripe-based payments.

The project was built as a hands-on Django learning project with a focus on realistic backend architecture, relational data modeling, company-scoped authorization, historical record preservation, external payment integration, and automated testing.

## Tech Stack

- Python 3.12
- Django 5.2
- PostgreSQL
- Psycopg
- Django Templates
- HTML / CSS
- Stripe Checkout
- Stripe Webhooks
- Faker
- WSL2 / Ubuntu
- Git / GitHub

## Main Features

### Company and User Management

- Customer company records
- Employee management
- Django authentication
- Company memberships
- Role-based permissions:
  - Admin
  - Manager
  - Viewer
- Company-scoped data access
- Django Admin for internal management

### Fuel Card Management

- Create and edit fuel cards
- Card statuses:
  - Active
  - Suspended
  - Lost
  - Cancelled
- Search and filter fuel cards
- View card details
- Company-scoped card access
- Prevent cross-company record access

### Employee Card Assignments

Fuel cards can be assigned to employees while preserving assignment history.

A card can only have one active assignment at a time, but an employee can have multiple cards.

Assignments are not deleted when a card is unassigned. Instead, the `unassigned_at` date is recorded so historical ownership remains available.

Example:

```text
Fuel Card
├── Employee A: Jan 1 → Jun 30
└── Employee B: Jul 1 → Present
```

### Card-Lock Stations and Fuel Prices

The application includes models for:

- Card-lock stations
- Fuel networks
- Station locations
- Fuel types
- Fuel prices
- Effective pricing dates

### Fuel Transactions

Fuel transactions track:

- Fuel card
- Station
- Fuel type
- Litres
- Price per litre
- Total amount
- Transaction date
- External reference

External references can be used to prevent duplicate transaction imports when integrating with external providers.

### Dashboard

The dashboard provides an overview of operational data including:

- Companies
- Employees
- Fuel cards
- Card-lock stations
- Fuel transactions
- Fuel spend
- Fuel volume
- Recent transactions

Normal users only see information belonging to their company.

Django superusers have global access.

### Invoice Management

Invoices belong to individual companies and contain:

- Invoice number
- Billing period
- Subtotal
- Tax
- Total
- Due date
- Payment status
- Stripe payment information
- Paid date

Supported statuses include:

- Draft
- Open
- Paid
- Overdue
- Void

## Stripe Payment Integration

Open invoices can be paid through Stripe Checkout.

The payment flow is:

```text
Invoice
    ↓
Pay with Stripe
    ↓
Stripe Checkout Session
    ↓
Customer completes payment
    ↓
Stripe webhook
    ↓
Django verifies webhook signature
    ↓
Invoice marked as Paid
```

The success page does not mark the invoice as paid.

Payment confirmation is handled through a signed Stripe webhook so the application does not trust browser redirects as proof of payment.

The webhook stores:

- Stripe Checkout Session ID
- Stripe Payment Intent ID
- Payment timestamp
- Invoice payment status

Webhook processing is designed to be idempotent so repeated Stripe events do not repeatedly process an already-paid invoice.

## Authorization and Company Data Isolation

The application uses `CompanyMembership` to associate a Django user with a company.

Authentication answers:

```text
Who is the user?
```

Authorization determines:

```text
What is the user allowed to do?
```

Company-scoped authorization determines:

```text
Which company's records can the user access?
```

The general request flow is:

```text
Authenticated User
        ↓
CompanyMembership
        ↓
Company + Role
        ↓
Company-scoped QuerySet
        ↓
Object lookup
        ↓
View / Form
        ↓
Template
```

Company isolation is enforced in backend queries rather than only in the user interface.

For example:

```python
employees = Employee.objects.filter(
    company=company
)
```

Individual records are retrieved from an already-scoped QuerySet:

```python
employee = get_object_or_404(
    employees,
    pk=pk,
)
```

This means changing an ID in the URL cannot expose another company's record.

## Project Structure

```text
cardlock-portal/
├── billing/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── templates/
│
├── cards/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── templates/
│
├── companies/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── access.py
│   ├── tests.py
│   └── templates/
│
├── dashboard/
├── stations/
├── transactions/
│
├── config/
│   ├── settings.py
│   └── urls.py
│
├── templates/
├── manage.py
├── requirements.txt
├── .gitignore
└── .env
```

## Important Domain Relationships

```text
Company
├── Employees
├── Fuel Cards
├── Company Memberships
└── Invoices

Fuel Card
├── Card Assignments
└── Fuel Transactions

Card Assignment
└── Employee

Fuel Transaction
├── Fuel Card
└── Card-Lock Station

Card-Lock Station
└── Fuel Prices
```

## Local Development Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd cardlock-portal
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database and application user.

Example database name:

```text
cardlock_portal
```

### 5. Configure environment variables

Create a local `.env` file.

Example:

```env
DB_NAME=cardlock_portal
DB_USER=cardlock_user
DB_PASSWORD=your_local_password
DB_HOST=localhost
DB_PORT=5432

STRIPE_SECRET_KEY=your_stripe_test_secret_key
STRIPE_WEBHOOK_SECRET=your_local_webhook_secret
```

Never commit `.env` or real credentials to Git.

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Seed demo data

```bash
python manage.py seed_demo
```

### 8. Create a Django superuser

```bash
python manage.py createsuperuser
```

### 9. Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Stripe Webhook Testing

For local Stripe webhook development, start the Django server in one terminal:

```bash
python manage.py runserver
```

In another terminal, start the Stripe CLI listener:

```bash
stripe listen \
  --events checkout.session.completed,checkout.session.async_payment_succeeded \
  --forward-to http://localhost:8000/invoices/stripe/webhook/
```

The Stripe CLI will provide a webhook signing secret.

Add it to `.env`:

```env
STRIPE_WEBHOOK_SECRET=whsec_...
```

Restart Django after changing `.env`.

Stripe test card:

```text
4242 4242 4242 4242
```

Use any valid future expiry date and any three-digit CVC while working in Stripe sandbox mode.

## Automated Tests

The project includes tests covering:

- Company data isolation
- Cross-company URL access
- Admin / Manager / Viewer permissions
- Fuel card authorization
- Employee authorization
- Form tampering protection
- Users without company memberships
- Stripe Checkout creation
- Invalid Stripe webhook signatures
- Successful webhook processing
- Invoice payment updates
- Webhook idempotency

Run the complete test suite:

```bash
python manage.py test
```

Run tests for a specific application:

```bash
python manage.py test cards
python manage.py test companies
python manage.py test billing
```

## Useful Django Commands

```bash
python manage.py runserver
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py shell
python manage.py createsuperuser
python manage.py seed_demo
python manage.py test
```

Inspect SQL generated by a migration:

```bash
python manage.py sqlmigrate app_name migration_number
```

## Laravel to Django Reference

| Laravel | Django |
| --- | --- |
| `php artisan` | `python manage.py` |
| `routes/web.php` | `urls.py` |
| Controller | View |
| Eloquent | Django ORM |
| Eloquent Model | Django Model |
| Blade | Django Templates |
| FormRequest / Validator | Form / ModelForm |
| Seeder | Management Command |
| Migration | Migration |
| `hasMany` / `belongsTo` | `ForeignKey` / `related_name` |
| `with()` | `select_related()` / `prefetch_related()` |
| `firstOrCreate()` | `get_or_create()` |
| `updateOrCreate()` | `update_or_create()` |
| `@csrf` | `{% csrf_token %}` |

## Key Design Decisions

### Preserve Historical Data

Important business records are generally not hard-deleted.

The project uses:

- `PROTECT`
- Status fields
- Active/inactive flags
- Assignment history
- Payment timestamps

This prevents useful historical business information from being unintentionally removed.

### Server-Controlled Company Ownership

Normal users do not choose arbitrary company IDs when creating records.

The company is determined from the authenticated user's membership.

This protects against manipulated POST requests attempting to create records under another company.

### Backend Authorization

Security is enforced through Django views and QuerySets rather than by simply hiding buttons or records in HTML.

### Decimal Values for Financial Data

`DecimalField` is used for money, fuel prices, litres, and other values where predictable decimal precision is important.

### External API Idempotency

External transaction references and payment state checks help prevent duplicate processing when external systems retry requests.

## Development Environment

The project was developed using:

```text
Windows
└── WSL2
    └── Ubuntu 24.04
        ├── Python
        ├── Django
        ├── PostgreSQL
        ├── Git
        └── Stripe CLI
```

Cursor runs on Windows and connects to the project inside WSL2.

## Project Purpose

This project was created primarily as a practical Django and PostgreSQL learning project using concepts from a realistic card-lock and fuel-management environment.

The focus is not only on building CRUD pages, but also on understanding:

- Django architecture
- ORM relationships
- PostgreSQL
- Authentication
- Authorization
- Company data isolation
- Business-domain modeling
- Historical record preservation
- External API integrations
- Webhooks
- Payment processing
- Automated testing
- Linux-based development workflows

## Status

The current training version includes the core Card-Lock Portal functionality, company-scoped authorization, employee and fuel-card management, assignment history, stations, transactions, invoicing, Stripe Checkout integration, webhook payment confirmation, and automated tests.

Additional production features such as advanced payment history, refunds, Stripe Customers, reporting, external transaction imports, deployment automation, and CI/CD are intentionally outside the current scope.