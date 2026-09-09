import os
import tempfile

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-32-chars-minimum-ok")
os.environ.setdefault("DEMO_MODE", "true")

# Use a fresh temp DB for every test session — prevents cross-run state leaks
_TEST_DB = tempfile.mktemp(suffix=".db")
os.environ["TEST_DB_PATH"] = _TEST_DB


def pytest_configure(config):
    """Patch DB path to a fresh temp file, then init tables."""
    import backend.db.history as hist_mod
    import backend.db.users as users_mod
    from pathlib import Path
    hist_mod._DB_PATH  = Path(_TEST_DB)
    users_mod._DB_PATH = Path(_TEST_DB)
    hist_mod.init_db()
    users_mod.init_users_table()


def pytest_sessionfinish(session, exitstatus):
    """Clean up temp DB after all tests complete."""
    try:
        os.unlink(_TEST_DB)
    except OSError:
        pass
