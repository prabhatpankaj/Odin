from test_plus import TestCase

from django.urls import reverse

from ..services import add_student, add_teacher
from ..factories import CourseFactory, StudentFactory, TeacherFactory
from ..models import Student

from odin.users.factories import ProfileFactory

from odin.common.faker import faker


class TestUserCoursesView(TestCase):

    def setUp(self):
        self.test_password = faker.password()
        self.course = CourseFactory()
        self.student = StudentFactory(password=self.test_password)
        self.teacher = TeacherFactory(password=self.test_password)
        self.url = reverse('dashboard:education:user-courses')
        self.student.is_active = True
        self.teacher.is_active = True
        self.student.save()
        self.teacher.save()

    def test_get_course_list_view_when_logged_in(self):
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_get_course_list_redirects_to_login_when_not_logged(self):
        response = self.get(self.url)
        self.assertEqual(302, response.status_code)

    def test_course_is_not_shown_if_student_is_not_in_it(self):
        course = CourseFactory()
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, course.name)

    def test_course_is_not_shown_if_teacher_is_not_in_it(self):
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, self.course.name)

    def test_user_courses_are_shown_for_student_in_course(self):
        with self.login(email=self.student.email, password=self.test_password):
            add_student(self.course, self.student)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, self.course.name)

<<<<<<< ceef9e838cea5d893e6e8356bbed937d74969154
=======
    def test_course_is_not_shown_if_teacher_is_not_in_it(self):
        course = CourseFactory()
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, course.name)

>>>>>>> Add hidden field to Teacher, add signals, fix tests
    def test_user_courses_are_shown_for_teacher_in_course(self):
        course = CourseFactory()
        with self.login(email=self.teacher.email, password=self.test_password):
            add_teacher(course, self.teacher)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, course.name)

    def test_course_is_shown_if_user_is_teacher_and_student_in_different_courses(self):
        course = CourseFactory()
        student = Student.objects.create_from_user(self.teacher.user)
        student.is_active = True
        student.save()
        with self.login(email=self.teacher.email, password=self.test_password):
            add_teacher(self.course, self.teacher)
            add_student(course, student)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, self.course.name)
            self.assertContains(response, course.name)


class TestCourseDetailView(TestCase):

    def setUp(self):
        self.test_password = faker.password()
        self.course = CourseFactory()
        self.student = StudentFactory(password=self.test_password)
        self.teacher = TeacherFactory(password=self.test_password)
        self.url = reverse('dashboard:education:user-course-detail', kwargs={'course_id': self.course.pk})
        self.student.is_active = True
        self.teacher.is_active = True
        self.student.save()
        self.teacher.save()

    def test_can_not_access_course_detail_if_not_student_or_teacher(self):
        response = self.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_can_access_course_detail_if_student(self):
        add_student(self.course, self.student)
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_course_teachers_appear_if_there_is_any(self):
        ProfileFactory(user=self.teacher.user)
        add_teacher(self.course, self.teacher)
        add_student(self.course, self.student)
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, self.teacher.get_full_name())
            self.assertContains(response, self.teacher.profile.description)

    def test_course_teachers_do_not_appear_if_there_is_none(self):
        ProfileFactory(user=self.teacher.user)
        add_student(self.course, self.student)
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, self.teacher.get_full_name())
            self.assertNotContains(response, self.teacher.profile.description)
