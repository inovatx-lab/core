from .base_settings import *

DATABASES = {
    "default": database_settings(
        "POSTGRES_MIGRATOR_USER",
        "POSTGRES_MIGRATOR_PASSWORD",
        startup_role_env="POSTGRES_OWNER_ROLE",
    )
}
