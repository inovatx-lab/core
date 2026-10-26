# INOVATX Core local development

## Requirements

- Python 3.12
- PostgreSQL 16 or later for database-backed migration work

The Django project uses the built-in `auth.User`. Core domain models and admin
configuration are handled by Task 1.3.2. This local bootstrap is not a
production deployment or evidence that tenant RLS works. The URL map is
intentionally empty; API routes belong to Task 1.3.3.

## Create the local environment

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_SECRET_KEY = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
$env:DJANGO_DEBUG = "true"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
$env:POSTGRES_DB = "inovatx_db"
$env:POSTGRES_USER = "your-local-postgres-user"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$securePassword = Read-Host -AsSecureString -Prompt "Local PostgreSQL password"
$env:POSTGRES_PASSWORD = (New-Object System.Net.NetworkCredential("", $securePassword)).Password
Remove-Variable securePassword
```

The secret key and PostgreSQL password are process-local environment values.
Do not put them in source files or commit a `.env` file.

## Check and run

```powershell
python manage.py check
python manage.py migrate
python manage.py runserver
```

`migrate` requires a reachable PostgreSQL server and the configured database.
`runserver` also checks migration history during startup, so it requires
PostgreSQL to be reachable. SQLite is not configured as a fallback. Domain
migrations will be added with Task 1.3.2.
