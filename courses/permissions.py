from rest_framework import permissions
from courses.models import CourseTeacher, Course, CourseSemester


class IsTeachingCourse(permissions.BasePermission):
    """
    Only allow teachers who teaching that course.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_teacher:
            if isinstance(obj, Course):
                return CourseTeacher.objects.filter(
                    course_semester__course=obj, teacher=request.user
                ).exists()
            elif isinstance(obj, CourseSemester):
                return CourseTeacher.objects.filter(
                    course_semester=obj, teacher=request.user
                ).exists()
        return False


class IsLecturerOrHeadLecturer(permissions.BasePermission):
    """
    Only allow lecturers or head lecturers.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role in [
            "Lecturer",
            "HeadLecturer",
        ]
