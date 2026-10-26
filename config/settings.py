import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _required_env(name):
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise ImproperlyConfigured(f"{name} must be set to a non-empty value.")
    return value


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.lower()
    if normalized not in {"true", "false"}:
        raise ImproperlyConfigured(f"{name} must be 'true' or 'false'.")
    return normalized == "true"


SECRET_KEY = _required_env("DJANGO_SECRET_KEY")
DEBUG = _env_bool("DJANGO_DEBUG")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _required_env("POSTGRES_DB"),
        "USER": _required_env("POSTGRES_USER"),
        "PASSWORD": _required_env("POSTGRES_PASSWORD"),
        "HOST": _required_env("POSTGRES_HOST"),
        "PORT": _required_env("POSTGRES_PORT"),
        "CONN_MAX_AGE": 0,
    }
}

AUTH_USER_MODEL = "auth.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
