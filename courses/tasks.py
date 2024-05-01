from celery import shared_task
from .services import process_submission_file
import os,glob

@shared_task
def process_files_task(class_code):
    # Construct path based on class_code split logic
    semester, course_code, class_code = class_code.split('_')
    file_path = f'submission_files/{course_code}/{semester}/{class_code}/'
    for file in glob.glob(f'{file_path}*.csv'):
        try:
            process_submission_file(file)
            os.remove(file)
        except Exception as e:
            # Log the error or send it to a monitoring system
            print(f"Failed to process file {file}: {str(e)}")
