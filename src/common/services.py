from typing import Generic

from src.common.types import BaseModelType
from src.users.models import BaseUser


class BaseService(Generic[BaseModelType]):
    def create_base(self, instance: BaseModelType, performed_by: BaseUser | None = None) -> BaseModelType:
        instance.created_by = performed_by
        instance.updated_by = performed_by

        instance.full_clean()
        instance.save()

        return instance

    def edit_base(self, instance: BaseModelType, updated_by: BaseUser | None = None) -> BaseModelType:
        instance.updated_by = updated_by

        instance.full_clean()
        instance.save()

        return instance

    def delete_base(self, instance: BaseModelType) -> None:
        instance.delete()
