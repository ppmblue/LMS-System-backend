from rest_framework import permissions, exceptions
from courses.models import CourseTeacher, Course, CourseSemester, Lab


class IsTeacherForCourse(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            CourseTeacher.objects.filter(course=obj, teacher=request.user)
            .select_related("course", "teacher")
            .exists()
        )


class CanAccessSemesterObj(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        course_code = view.kwargs.get("course_code")
        user = request.user
        if user is not None and course_code is not None:
            return (
                CourseTeacher.objects.filter(
                    course__course_code=course_code, teacher=user, course_semester=obj
                )
                .prefetch_related("course_semester")
                .exists()
            )
        return False


class CanManageLabData(permissions.BasePermission):

    def has_permission(self, request, view):
        course_code = view.kwargs.get("course_code")
        semester_name = view.kwargs.get("semester_name")
        user = request.user
        if user is not None and course_code is not None and semester_name is not None:
            return (
                CourseTeacher.objects.filter(
                    course__course_code=course_code,
                    teacher=user,
                    course_semester__semester_name=semester_name,
                )
                .prefetch_related("course_semester")
                .exists()
            )
        return False


class CanManageCourseData(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated:
            course_teacher_query = (
                CourseTeacher.objects.filter(
                    course__course_code=view.kwargs.get("course_code"), teacher=user
                )
                .prefetch_related("course_semester")
                .exists()
            )
            return user.is_superuser or course_teacher_query
        return false


class IsLecturerOrHeadLecturer(permissions.BasePermission):
    """
    Only allow lecturers or head lecturers.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role in [
            "Lecturer",
            "HeadLecturer",
        ]
