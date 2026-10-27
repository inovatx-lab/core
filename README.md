# INOVATX Core local development

## Requirements

- Python 3.12
- PostgreSQL 16 or later

The Django project uses the built-in `auth.User`. Core domain models and admin
configuration are handled by Task 1.3.2. This local bootstrap is not a
production deployment or evidence that tenant RLS works. The URL map is
intentionally empty; API routes belong to Task 1.3.3.
With `DEBUG=true`, Django displays its development install page at `/`; this
placeholder is not an implemented application route.

## Provision local PostgreSQL roles

Run these one-time commands in `psql` as the local PostgreSQL setup authority.
If you already created the roles and database, do not repeat the `CREATE`
commands.

```sql
CREATE ROLE inovatx_owner NOLOGIN;
CREATE ROLE inovatx_migrator LOGIN;
GRANT inovatx_owner TO inovatx_migrator;
CREATE ROLE inovatx_runtime LOGIN;
CREATE DATABASE inovatx_db OWNER inovatx_owner;
REVOKE ALL ON DATABASE inovatx_db FROM PUBLIC;
GRANT CONNECT ON DATABASE inovatx_db TO inovatx_migrator, inovatx_runtime;
```

Set each login password interactively in `psql`; never put passwords in SQL
scripts, source files, or chat:

```text
\password inovatx_migrator
\password inovatx_runtime
\connect inovatx_db
```

Then restrict the public schema and grant runtime schema access:

```sql
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO inovatx_runtime;
```

The migrator settings activate `inovatx_owner` for each connection. The owner
role name is checked as a safe PostgreSQL identifier before it is passed in
connection options.

## Create the local Python environment

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_SECRET_KEY = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
$env:DJANGO_DEBUG = "true"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
$env:POSTGRES_DB = "inovatx_db"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
```

These values are process-local. Do not store secrets in source files or commit
a `.env` file.

## Apply migrations

Set the migration login credentials from secure prompts, then run migrations
using the dedicated migration settings module:

```powershell
$env:POSTGRES_MIGRATOR_USER = "inovatx_migrator"
$securePassword = Read-Host -AsSecureString -Prompt "Local PostgreSQL migrator password"
$env:POSTGRES_MIGRATOR_PASSWORD = (New-Object System.Net.NetworkCredential("", $securePassword)).Password
Remove-Variable securePassword
$env:POSTGRES_OWNER_ROLE = "inovatx_owner"
python manage.py check --settings=config.migration_settings
python manage.py migrate --settings=config.migration_settings
```

After migrations create `django_migrations`, connect to `inovatx_db` as the
local setup authority and grant the runtime role only the read access Django
needs for its migration-history startup check:

```sql
GRANT SELECT ON TABLE public.django_migrations TO inovatx_runtime;
```

## Run Django with runtime credentials

Set the separate runtime login credentials from a secure prompt and run the
default settings. The runtime identity has no migration or owner credentials:

```powershell
$env:POSTGRES_RUNTIME_USER = "inovatx_runtime"
$securePassword = Read-Host -AsSecureString -Prompt "Local PostgreSQL runtime password"
$env:POSTGRES_RUNTIME_PASSWORD = (New-Object System.Net.NetworkCredential("", $securePassword)).Password
Remove-Variable securePassword
python manage.py check
python manage.py runserver
```

`runserver` checks migration history during startup, so it needs PostgreSQL,
schema `USAGE`, and `SELECT` on `django_migrations`. No SQLite fallback is
configured. Domain migrations and their grants belong to Task 1.3.2 and later
approved implementation work.
