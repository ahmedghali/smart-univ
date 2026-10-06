"""Paramètres de production (Railway)."""

import dj_database_url
from decouple import Csv, config

from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS

DEBUG = False

DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=config("DATABASE_SSL_REQUIRE", default=False, cast=bool),
    )
}

# Domaine public fourni par Railway
_railway_domain = config("RAILWAY_PUBLIC_DOMAIN", default="")
if _railway_domain:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, _railway_domain]

CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host not in ("localhost", "127.0.0.1")]
CSRF_TRUSTED_ORIGINS += config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# HTTPS derrière le proxy Railway
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=3600, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": config("LOG_LEVEL", default="INFO")},
}
