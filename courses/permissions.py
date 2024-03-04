from rest_framework import permissions
from courses.models import CourseTeacher, Course, CourseSemester, Lab


class IsTeachingCourse(permissions.BasePermission):
    """
    Only allow teachers who teaching that course.
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_teacher:
            course_pk = view.kwargs.get("course_pk")
            semester_name = view.kwargs.get("semester_name")
            if semester_name:
                return CourseTeacher.objects.filter(
                    course_semester__course__pk=course_pk,
                    course_semester__semester_name=semester_name,
                ).exists()
            else:
                return CourseTeacher.objects.filter(
                    course_semester__course__pk=course_pk
                ).exists()
        else:
            return False

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
            elif isinstance(obj, CourseTeacher):
                return CourseTeacher.objects.filter(
                    teacher=request.user, pk=obj.pk
                ).exists()
            elif isinstance(obj, Lab):
                return CourseTeacher.objects.filter(
                    teacher=request.user, course_semester=obj.course_semester
                )
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
