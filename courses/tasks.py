from decimal import Decimal
from courses.models import (
    Exercise,
    Submission,
    UploadForm,
    Enrollment,
    Class,
    OutcomeProgress,
    LabLOContribution,
    LearningOutcome,
    Lab
)
from students.models import Student
from celery import shared_task
from datetime import datetime
import base64
from django.core.files.storage import default_storage
import os
from django.core.files import File

@shared_task
def process_submission_file_task(class_code, file_name, file_id):
    # Find file location based on file_name 
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    storage_path = os.path.join(BASE_DIR, 'file_storage')
    full_path=os.path.join(storage_path, file_name)
    
    with open(full_path, 'r') as f:
        file = File(f)
        lines = file.readlines()
        
        print('File info: ', full_path, len(lines))
        
        submissions = []
        target_class = Class.objects.get(
            class_code = class_code
        )
        for line in lines[1:]:
            fields = line.split(',') if (',' in line) else line.split(';')
            if (len(fields) != 10): continue
            
            print('Line ', line)
            # Validate student. Create new student if not existed
            student_id = ProcessFileHelper.get_integer_value(fields[2], 2012715)
            student = Student()
            if not (Student.objects.filter(student_id=student_id).exists()):
                student = Student(student_id=student_id)
                student.first_name = fields[0]
                student.last_name = fields[1]
                student.secured_student_id = base64.urlsafe_b64encode(str(student_id).encode())
                student.save()
            else:
                student = Student.objects.get(student_id=student_id)
                
            # Validate enrollment. Create new enrollment if not existed
            if not (Enrollment.objects.filter(student__student_id=student_id, class_code__id=target_class.id).exists()):
                # Enroll student into class
                Enrollment(class_code=target_class, student=student).save()
                
            # Validate exercise. Create new exercise if not existed
            question_id = ProcessFileHelper.get_integer_value(fields[9], 0)
            exercise = Exercise()
            if not (Exercise.objects.filter(exercise_id=question_id, class_code=class_code).exists()):
                exercise = Exercise(exercise_id=question_id, class_code=class_code)
                exercise.save()
            else:
                exercise = Exercise.objects.get(exercise_id=question_id, class_code=class_code)
            
            start_time = ProcessFileHelper.convertDate(str(fields[4]))
            end_time = ProcessFileHelper.convertDate(str(fields[5]))
            
            # Validate submission. Only create if not existed
            if not (Submission.objects.filter(student__student_id=student.student_id, started_time=start_time, submitted_time=end_time, exercise__id=exercise.id).exists()):
                submit = Submission()
                submit.student = student
                submit.exercise = exercise
                submit.score = ProcessFileHelper.get_float_value(fields[7])
                submit.time_taken = end_time - start_time
                submit.started_time = start_time
                submit.submitted_time = end_time
                submissions.append(submit)
            
        # Save into database
        Submission.objects.bulk_create(submissions, batch_size=100)
        
        # Clean file both from database and file_storage
        UploadForm.objects.get(id=file_id).delete()
        if (os.path.isfile(full_path)):
            os.remove(full_path)
            
        # Log success
        print(f"Import submission file for class {class_code} successfully!")
            
        # Calculate outcome progress
        OutcomeProgressHelper.calculate_outcome_progress(class_code)

class OutcomeProgressHelper:
    def calculate_outcome_progress(class_code):
        student_ids = Enrollment.objects.filter(class_code__class_code=class_code).values_list('student__student_id', flat=True).distinct()
        target_class = Class.objects.get(class_code=class_code)
        
        # Find all outcomes
        matrix = [[f'{x}-pre', f'{x}-in', f'{x}-post'] for x in range(1, target_class.num_of_lab + 1)]
        lab_names = [item for row in matrix for item in row]
        list_progress = []
        for outcome in LearningOutcome.objects.all():
            # Calculate outcome progress for each student
            for student_id in student_ids:
                max_contribution = 0
                curr_progress = 0
                
                # Calculate outcome progress through first lab -> current lab
                for lab_name in lab_names:
                    lab = Lab.objects.get(class_code__class_code=class_code, lab_name=lab_name)
                    submissions = Submission.objects.filter(student__student_id=student_id
                        , exercise__lab__lab_name=lab_name
                        , exercise__outcome__outcome_code=outcome.outcome_code)
                    
                    # Pass threshold
                    threshold = LearningOutcome.objects.get(outcome_code=outcome.outcome_code
                        , course__course_code = lab.class_code.course.course_code).threshold
        
                    # Update max_progress of a student
                    try:
                        contribution = LabLOContribution.objects.get(lab__lab_name=lab_name
                            , lab__class_code__class_code=class_code
                            , outcome__outcome_code=outcome.outcome_code).contribution_percentage
                    except:
                        contribution = 0
                    
                    max_contribution += contribution
                    correct_submit = 0
                    for submit in submissions:
                        if submit.score > threshold:
                            correct_submit += 1
                            
                    # Update current_progress after finishing lab
                    submission_count = submissions.count()
                    if (submission_count > 0):
                        curr_progress += Decimal(correct_submit / submission_count) * contribution

                    # Save into list progress
                    if not OutcomeProgress.objects.filter(lab=lab, student__student_id=student_id, outcome=outcome).exists():
                        student = Student.objects.get(student_id=student_id)
                        new_progress = OutcomeProgress(lab=lab, student=student, outcome=outcome, progress=round(curr_progress, 2), max_progress=max_contribution)
                        list_progress.append(new_progress)
        
        # Save into database for fast query later           
        OutcomeProgress.objects.bulk_create(list_progress, batch_size=100)
        
        # Log success
        print(f"Calculate outcome progress for class {class_code} successfully!")

class ProcessFileHelper:    
    def get_integer_value(str, default_val):
        try:
            int_value = int(str)
            return int_value
        except (TypeError, ValueError):
            return default_val
        
    def get_float_value(str):
        try:
            float_val = float(str)
            return float_val
        except (TypeError, ValueError):
            return 0
        
    # Convert month
    def convertMonth(month):
        map = { "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
                "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12" }
        for x in map.keys():
            month = month.replace(x, map[x])
        return month
    
    # Convert date
    def convertDate(date_str):
        date_str = ProcessFileHelper.convertMonth(date_str)
        date_format = '%d %m %Y %I:%M %p'

        date_obj = datetime.strptime(date_str, date_format)
        return date_obj