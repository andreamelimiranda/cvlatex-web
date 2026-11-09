"""
Configuración de Django para MICV.

Todo lo que cambia entre tu computador y el servidor (claves, base de datos,
correo) se lee desde «variables de entorno». Así el mismo código sirve en
los dos lugares y nunca subes contraseñas a GitHub.

Variables de entorno que se usan (todas opcionales en tu computador):
  SECRET_KEY            clave secreta de Django (obligatoria en el servidor)
  DEBUG                 "1" en desarrollo, "0" en el servidor
  ALLOWED_HOSTS         dominios permitidos, separados por comas
  DATABASE_URL          base de datos (si no está, se usa SQLite local)
  CSRF_TRUSTED_ORIGINS  orígenes https de confianza, separados por comas
  EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL
                        correo para recuperar contraseñas
"""

import os
from pathlib import Path

import dj_database_url

# Carpeta django_app/ (donde está manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpeta de arriba: la raíz del repositorio, donde viven index.html y las guías.
# Django muestra esos mismos archivos, así no hay que mantener dos copias del sitio.
SITIO_DIR = BASE_DIR.parent


def lista_env(nombre, por_defecto=""):
    """Lee una variable de entorno con valores separados por comas."""
    return [v.strip() for v in os.environ.get(nombre, por_defecto).split(",") if v.strip()]


# --- Seguridad básica -------------------------------------------------------
DEBUG = os.environ.get("DEBUG", "1") == "1"

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("Falta la variable de entorno SECRET_KEY en el servidor.")
    SECRET_KEY = "solo-para-desarrollo-no-usar-en-el-servidor"

ALLOWED_HOSTS = lista_env("ALLOWED_HOSTS", "localhost,127.0.0.1")
# Render agrega automáticamente esta variable con el dominio del servicio.
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

CSRF_TRUSTED_ORIGINS = lista_env("CSRF_TRUSTED_ORIGINS")
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    CSRF_TRUSTED_ORIGINS.append("https://" + os.environ["RENDER_EXTERNAL_HOSTNAME"])


# --- Aplicaciones -----------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",          # usuarios y contraseñas
    "django.contrib.contenttypes",
    "django.contrib.sessions",      # recordar quién inició sesión
    "django.contrib.messages",      # mensajes tipo «¡Guardado!»
    "django.contrib.staticfiles",   # archivos CSS y JS
    # Nuestras apps:
    "cuentas",  # registro, inicio de sesión y contraseñas
    "cvs",      # páginas públicas, «Mis CVs» y guardado de currículums
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # sirve el CSS/JS en el servidor
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "micv.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # base.html común a todas las páginas
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "micv.wsgi.application"


# --- Base de datos ----------------------------------------------------------
# En tu computador: un archivo SQLite (db.sqlite3), sin instalar nada.
# En el servidor: la dirección de Postgres que pongas en DATABASE_URL.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Contraseñas ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "entrar"
LOGIN_REDIRECT_URL = "mis_cvs"
LOGOUT_REDIRECT_URL = "/"


# --- Idioma y hora ----------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos (CSS y JS propios de Django) -------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if os.environ.get("ENTORNO") == "produccion":
    # En el servidor, WhiteNoise comprime los archivos y les pone un código
    # en el nombre para que el navegador los guarde en caché sin problemas.
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# Un CV con foto puede pesar unos MB: dejamos pasar hasta 4 MB por petición.
DATA_UPLOAD_MAX_MEMORY_SIZE = 4 * 1024 * 1024


# --- Correo (para «¿Olvidaste tu contraseña?») ------------------------------
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "MICV <no-responder@micvpremium.cl>")
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = True
else:
    # Sin servidor de correo, el mensaje se muestra en la terminal.
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# --- Seguridad extra solo en el servidor (https) ----------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_CONTENT_TYPE_NOSNIFF = True
