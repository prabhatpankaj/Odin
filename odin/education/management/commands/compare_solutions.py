import difflib
from pprint import pprint
from collections import deque

from django.core.management.base import BaseCommand, CommandError

from odin.education.models import Course, Solution

MIN_ALLOWED_DIFFERENCE_PERCENTAGE = 35


def compare_code_solutions(first_solution, second_solution):
    current_code = first_solution.code.splitlines()
    next_code = second_solution.code.splitlines()
    diff_percentage, unified_diff = calculate_difference_percentage(current_code, next_code)

    if diff_percentage < MIN_ALLOWED_DIFFERENCE_PERCENTAGE:
        print(
            f"""
            Matching contents in solutions
            {first_solution} from {first_solution.student.email} and
            {second_solution} from {second_solution.student.email}
            on task {first_solution.task.name}
            Differences:
            """
        )
        pprint(unified_diff)


def compare_file_solutions(first_solution, second_solution):
    current_code = first_solution.file.read().decode('utf-8').splitlines()
    next_code = second_solution.file.read().decode('utf-8').splitlines()
    diff_percentage, unified_diff = calculate_difference_percentage(current_code, next_code)

    if diff_percentage < MIN_ALLOWED_DIFFERENCE_PERCENTAGE:
        print(
            f"""
            Matching contents in files
            {first_solution.file.name} from {first_solution.student.email} and
            {second_solution.file.name} from {second_solution.student.email}
            on Task: {first_solution.task.name}
            Differences:
            """
        )
        pprint(unified_diff)


def calculate_difference_percentage(first_chunk, second_chunk):
    differences = list(difflib.unified_diff(first_chunk, second_chunk))[3:]
    diff_count = 0
    for difference in differences:
        diff_count += difference.startswith('-') or difference.startswith('+')
    return diff_count / len(first_chunk) * 100, differences


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('course_id', nargs="+", type=int)

    def handle(self, *args, **options):
        for course_id in options['course_id']:
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CommandError(f'Course with ID: {course_id} does not exist')

            topics = course.topics.all()
            for topic in topics:
                tasks = topic.tasks.all()

                for task in tasks:
                    if not task.gradable:
                        break

                    passing_solutions = deque(
                        task.solutions.filter(status=Solution.OK).order_by('student__email').distinct('student__email')
                    )
                    print(f'{len(passing_solutions)} people have solved {task.name}')

                    while passing_solutions:
                        current_solution = passing_solutions.popleft()
                        for next_solution in passing_solutions:
                            if task.test.is_source():
                                compare_code_solutions(current_solution, next_solution)
                            else:
                                compare_file_solutions(current_solution, next_solution)
