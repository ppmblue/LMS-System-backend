# Create your views here.
from django.shortcuts import render

from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser 
from rest_framework import status
 
from courses.models import Course
from courses.serializers import CourseSerializer
from rest_framework.decorators import api_view


@api_view(['GET', 'POST', 'DELETE'])
def course_list(request):
    # GET list of courses or find courses by course_name
    if request.method == 'GET':
        courses = Course.objects.all()

        course_name = request.GET.get('course_name', None)
        if course_name is not None:
            courses = courses.filter(course_name__icontains=course_name)
        courses_serializer = CourseSerializer(courses, many=True)
        return JsonResponse({'course_name filter':course_name, 'data':courses_serializer.data }, safe=False)
    # POST a new course
    elif request.method == 'POST':
        course_data = JSONParser().parse(request)
        courses_serializer = CourseSerializer(data=course_data)
        if courses_serializer.is_valid():
            courses_serializer.save()
            return JsonResponse(courses_serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(courses_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
 
@api_view(['GET', 'PUT', 'DELETE'])
def course_detail(request, pk):
    # find course by pk (id)
    try: 
        course = Course.objects.get(pk=pk) 
    except Course.DoesNotExist: 
        return JsonResponse({'message': 'Course does not exist'}, status=status.HTTP_404_NOT_FOUND) 
    # GET a course
    if request.method == 'GET':
        course_serializer = CourseSerializer(course)
        return JsonResponse(course_serializer.data)
    # PUT a course
    elif request.method == 'PUT':
        course_data = JSONParser().parse(request)
        course_serializer = CourseSerializer(course, data=course_data)
        if course_serializer.is_valid():
            course_serializer.save()
            return JsonResponse(course_serializer.data)
        return JsonResponse(course_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # DELETE a course
    elif request.method == 'DELETE':
        course.delete()
        return JsonResponse({'message':'Course was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
    
