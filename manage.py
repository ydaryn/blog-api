import os
import sys

from pathlib import Path
from decouple import Config, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / "settings"/".env"

config = Config(RepositoryEnv(env_file))
env_id = config("BLOG_ENV_ID", default="local")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{env_id}")

from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)