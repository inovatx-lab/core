from .base_settings import _required_env
from .migration_settings import *

DATABASES["default"]["TEST"] = {"NAME": _required_env("POSTGRES_TEST_DB")}
