from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile
from courses.models import (
    Course,
    Semester,
    Class,
    Lab,
    LearningOutcome,
    LabLOContribution,
    Exercise,
    Submission,
)


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
admin.site.register(Course)
admin.site.register(Semester)
admin.site.register(Class)
admin.site.register(Lab)
admin.site.register(LearningOutcome)
admin.site.register(LabLOContribution)
admin.site.register(Exercise)
admin.site.register(Submission)
