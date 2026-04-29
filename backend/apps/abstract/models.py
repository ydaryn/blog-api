from django.db.models import Model, DateTimeField
from typing import Any 
from django.utils import timezone as django_timezone



class AbstractTimeStampModel(Model):

    created_at = DateTimeField(
        auto_now_add=True,
    )
    updated_at = DateTimeField(
        auto_now=True,
    )
    deleted_at = DateTimeField(
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        abstract = True 

    def delete(self,*args:tuple[Any,...],**kwargs:dict[Any,Any])->None:
            """
            Docstring for delete
            
            :param self: Description
            :param args: Description
            :type args: tuple[Any, ...]
            :param kwargs: Description
            :type kwargs: dict[Any, Any]
            """

            self.deleted_at = django_timezone
            self.save(update_fields=["deleted_at"])

