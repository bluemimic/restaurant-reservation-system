import os

from src.files.enums import FileUploadStorage, FileUploadStrategy

from config.env import BASE_DIR, env, env_to_enum

FILE_UPLOAD_STRATEGY = env_to_enum(FileUploadStrategy, env("FILE_UPLOAD_STRATEGY", default="standard"))
FILE_UPLOAD_STORAGE = env_to_enum(FileUploadStorage, env("FILE_UPLOAD_STORAGE", default="local"))

FILE_MAX_SIZE = env.int("FILE_MAX_SIZE", default=20 * 1024 * 1024)  # 20 MB

if FILE_UPLOAD_STORAGE == FileUploadStorage.LOCAL:
    MEDIA_ROOT_NAME = "media"
    MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_ROOT_NAME)
    MEDIA_URL = f"/{MEDIA_ROOT_NAME}/"

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
