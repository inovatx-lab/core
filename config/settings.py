from .base_settings import *

DATABASES = {
    "default": database_settings("POSTGRES_RUNTIME_USER", "POSTGRES_RUNTIME_PASSWORD")
}
