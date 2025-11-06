import os, sys
INTERP = "/var/www/u3292150/data/venv/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from app import app as application  # в app.py должен быть application = Flask(__name__)