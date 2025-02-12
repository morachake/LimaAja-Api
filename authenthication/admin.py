from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "email",
        "full_name",
        "phone_number",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("full_name", "phone_number", "profile_picture")}),
        ("Personal Info", {"fields": ("full_name", "phone_number", "profile_picture")}),
        ("Adress", {"fields": {"adress", "city", "country"}}),
        ("Permissions", {"fields": ("role", "is_staff", "is_active")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "phone_number",
                    "password1",
                    "password2",
                    "role",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email", "full_name", "phone_number")
    ordering = "email"
