from .common import *

DEBUG = False

# FIXME localhost는 dev 환경 구축 후 제거
ALLOWED_HOSTS = [
    "seeya.wafflestudio.com",
    "seeya-api.wafflestudio.com",
    "localhost",
]

CSRF_TRUSTED_ORIGINS = ALLOWED_HOSTS
CSRF_COOKIE_DOMAIN = ".wafflestudio.com"

CORS_ORIGIN_WHITELIST = [
    "https://seeya.wafflestudio.com",
    "http://localhost:5173",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("SEEYA_DB_NAME"),
        "USER": os.getenv("SEEYA_DB_USER"),
        "PASSWORD": os.getenv("SEEYA_DB_PASSWORD"),
        "HOST": os.getenv("SEEYA_DB_HOST"),
        "PORT": os.getenv("SEEYA_DB_PORT"),
    }
}
