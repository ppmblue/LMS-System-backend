import csv
from datetime import datetime
from django.utils.timezone import make_aware
from .models import Submission, Exercise


def process_submission_file(file_path):
    submissions = parse_csv_submission(file_path)
    Submission.objects.bulk_create(submissions)


def parse_csv_submission(file_path):
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReade(csvfile)
        submissions = []
        for row in reader:
            student_id = int(row["ID number"])
            started_time = make_aware(
                datetime.strptime(row["Started on"], "%d %B %Y %I:%M %p")
            )
            submitted_time = make_aware(
                datetime.strptime(row["Completed"], "%d %B %Y %I:%M %p")
            )
            time_taken = parse_duration(row["Time taken"])
            score = float(row["Grade/100"])
            exercise_id = int(row["questionID"])

            exercise, created = Exercise.objects.get_or_create(
                id=exercise_id,
                defaults={},  # Add default values for new exercises
            )
            submission = Submission(
                student=student_id,
                started_time=started_time,
                submitted_time=submitted_time,
                time_taken=time_taken,
                score=score,
                exercise=exercise,
            )
            submissions.append(submission)


def parse_duration(duration_str):
    duration = timedelta()
    units = {
        "hour": timedelta(hours=1),
        "min": timedelta(minutes=1),
        "day": timedelta(days=1),
    }
    for part in duration_str.split():
        if part.isdigit():
            number = int(part)
        else:
            unit = next((u for u in units if part.startswith(u)), None)
            if unit:
                duration += units[unit] * number
    return duration
