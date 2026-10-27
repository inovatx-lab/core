import os
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.base_settings import database_settings


class DatabaseSettingsTests(SimpleTestCase):
    def test_runtime_database_uses_runtime_credentials_without_startup_role(self):
        with patch.dict(
            os.environ,
            {
                "POSTGRES_DB": "inovatx_db",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "RUNTIME_USER": "inovatx_runtime",
                "RUNTIME_PASSWORD": "runtime-test-password",
            },
        ):
            config = database_settings("RUNTIME_USER", "RUNTIME_PASSWORD")

        self.assertEqual(config["USER"], "inovatx_runtime")
        self.assertNotIn("OPTIONS", config)

    def test_migration_database_requests_owner_role(self):
        with patch.dict(
            os.environ,
            {
                "POSTGRES_DB": "inovatx_db",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "MIGRATOR_USER": "inovatx_migrator",
                "MIGRATOR_PASSWORD": "migrator-test-password",
                "OWNER_ROLE": "inovatx_owner",
            },
        ):
            config = database_settings(
                "MIGRATOR_USER",
                "MIGRATOR_PASSWORD",
                startup_role_env="OWNER_ROLE",
            )

        self.assertEqual(config["USER"], "inovatx_migrator")
        self.assertEqual(config["OPTIONS"], {"options": "-c role=inovatx_owner"})

    def test_migration_database_rejects_unsafe_owner_role(self):
        with patch.dict(
            os.environ,
            {
                "POSTGRES_DB": "inovatx_db",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "MIGRATOR_USER": "inovatx_migrator",
                "MIGRATOR_PASSWORD": "migrator-test-password",
                "OWNER_ROLE": "inovatx_owner -c search_path=public",
            },
        ):
            with self.assertRaises(ImproperlyConfigured):
                database_settings(
                    "MIGRATOR_USER",
                    "MIGRATOR_PASSWORD",
                    startup_role_env="OWNER_ROLE",
                )
