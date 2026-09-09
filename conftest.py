import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-32-chars-minimum-ok")
os.environ.setdefault("DEMO_MODE", "true")
