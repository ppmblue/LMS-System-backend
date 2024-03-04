from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class UserProfileAdmin(UserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_teacher",
        "phone_number",
    ]
    search_fields = ["username", "email", "first_name", "last_name", "is_teacher"]
    list_filter = ["is_teacher", "is_superuser"]
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "student_id",
                    "major",
                )
            },
        ),
        ("Permissions", {"fields": ("is_teacher", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


admin.site.register(UserProfile, UserProfileAdmin)
