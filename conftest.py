import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-32-chars-minimum-ok")
os.environ.setdefault("DEMO_MODE", "true")


def pytest_configure(config):
    """Initialise DB tables before any test runs (startup events don't fire in ASGITransport)."""
    from backend.db import history as hist_db
    from backend.db import users as users_db
    hist_db.init_db()
    users_db.init_users_table()
