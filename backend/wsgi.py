"""Production entry point: gunicorn wsgi:app"""

import sys

from app import create_app
from app.config import Config

errors = Config.validate()
if errors:
    sys.exit("Configuration errors: " + "; ".join(errors))

app = create_app()
