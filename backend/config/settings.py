import os
import re
from pathlib import Path
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-synthetic-development-only")
if not DEBUG and SECRET_KEY == "local-synthetic-development-only":
    raise RuntimeError("Configura DJANGO_SECRET_KEY para entornos no locales")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "apps.accounts",
    "apps.banking",
    "apps.forecast",
    "apps.classify",
    "apps.invoices",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "config.web.SecurityHeadersMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
if not DEBUG and not os.environ.get("POSTGRES_HOST"):
    raise RuntimeError("Producción requiere POSTGRES_HOST; SQLite solo se permite en desarrollo")
if os.environ.get("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["POSTGRES_HOST"],
            "NAME": os.environ.get("POSTGRES_DB", "liquidity"),
            "USER": os.environ.get("POSTGRES_USER", "liquidity"),
            "PASSWORD": os.environ["POSTGRES_PASSWORD"],
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "OPTIONS": {
                "connect_timeout": 5,
                "sslmode": os.environ.get("POSTGRES_SSLMODE", "prefer"),
            },
        }
    }
    schema = os.environ.get("POSTGRES_SCHEMA", "public")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
        raise RuntimeError("POSTGRES_SCHEMA no es válido")
    DATABASES["default"]["OPTIONS"]["options"] = f"-c search_path={schema}"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_RATES": {"login": "10/min"},
}
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKGROUND_MODE = os.environ.get("BACKGROUND_MODE", "celery")
if BACKGROUND_MODE not in ("celery", "database"):
    raise RuntimeError("BACKGROUND_MODE debe ser celery o database")

# Solo los orígenes locales de Vite se autorizan por defecto en desarrollo.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173" if DEBUG else "",
    ).split(",")
    if origin.strip()
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_RESET_TIMEOUT = 3600
FRONTEND_URL = os.environ.get(
    "FRONTEND_URL", os.environ.get("RENDER_EXTERNAL_URL", "http://127.0.0.1:5173")
)
if not DEBUG:
    frontend_origin = urlsplit(FRONTEND_URL)
    if (
        frontend_origin.scheme != "https"
        or not frontend_origin.hostname
        or frontend_origin.username is not None
        or frontend_origin.password is not None
        or frontend_origin.path not in ("", "/")
        or frontend_origin.query
        or frontend_origin.fragment
        or frontend_origin.hostname in ("localhost", "127.0.0.1", "::1")
    ):
        raise RuntimeError(
            "Producción requiere FRONTEND_URL como origen HTTPS externo sin secretos"
        )
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.filebased.EmailBackend"
    if DEBUG
    else (
        "config.email.EmailBackend"
        if RESEND_API_KEY
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)
EMAIL_FILE_PATH = BASE_DIR.parent / ".local-logs" / "emails"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Horizonte <no-reply@localhost>")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
EMAIL_TIMEOUT = 10

# El build React y la API comparten origen en la distribución web/escritorio.
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
WHITENOISE_ROOT = FRONTEND_DIST
WHITENOISE_USE_FINDERS = False
if os.environ.get("DJANGO_TRUST_PROXY", "0") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
