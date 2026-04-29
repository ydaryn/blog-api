from django.contrib.admin import ModelAdmin
from django.contrib import admin
#Project imports
from apps.users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    """
    Docstring for CustomUserAdmin
    """
    list_display = [ 
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_superuser",
        "data_jonded",
        "created_at",
        "updated_at",
        "deleted_at",
    ]
    search_fields = (
        "email",
        "first_name",
        "last_name",
    
    )

    list_display_links = (
        "email",
        "first_name",)

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
)

