from typing import TypeVar

from django.db import models

from src.common.models import BaseModel

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)
DjangoModelType = TypeVar("DjangoModelType", bound=models.Model)
