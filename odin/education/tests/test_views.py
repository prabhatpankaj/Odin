from test_plus import TestCase

from django.urls import reverse

from ..services import add_student, add_teacher
from ..factories import (
    CourseFactory,
    StudentFactory,
    TeacherFactory,
    WeekFactory,
    TopicFactory,
    MaterialFactory,
    IncludedMaterialFactory,
    TaskFactory,
    IncludedTaskFactory,
    ProgrammingLanguageFactory,
)
from ..models import Student, Teacher, Topic, IncludedMaterial, Material, IncludedTask, Task, SourceCodeTest

from odin.users.factories import ProfileFactory, BaseUserFactory, SuperUserFactory

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
        course = CourseFactory(name="TestCourseName")
        with self.login(email=self.student.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotIn(course.name, response.content.decode('utf-8'))

    def test_user_courses_are_shown_for_student_in_course(self):
        with self.login(email=self.student.email, password=self.test_password):
            add_student(self.course, self.student)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, self.course.name)

    def test_course_is_not_shown_if_teacher_is_not_in_it(self):
        course = CourseFactory(name="TestCourseName")
        with self.login(email=self.teacher.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertNotContains(response, course.name)

    def test_user_courses_are_shown_for_teacher_in_course(self):
        course = CourseFactory(name="TestCourseName")
        with self.login(email=self.teacher.email, password=self.test_password):
            add_teacher(course, self.teacher)
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, course.name)

    def test_course_is_shown_if_user_is_teacher_and_student_in_different_courses(self):
        course = CourseFactory(name="TestCourseName")
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


class TestPublicCourseDetailView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.url = reverse('public:course_detail', kwargs={'course_slug': self.course.slug_url})

    def test_cannot_add_topic_or_material_on_public_detail_page(self):
        response = self.get(self.url)
        self.assertEqual(200, response.status_code)
        content = response.content.decode('utf-8')
        self.assertNotIn(content,
                         "<button type='button' name='button' class='btn green uppercase' >Add new topic</button>")
        self.assertNotIn(content,
                         "<button type='button' name='button' class='btn green uppercase' >Add new material</button>")


class TestAddTopicToCourseView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.url = reverse('dashboard:education:course-management:manage-course-topics',
                           kwargs={'course_id': self.course.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_create_topic_for_course_on_post(self):
        data = {
            'name': faker.name(),
            'week': self.week.id
        }
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response,
                                 expected_url=reverse('dashboard:education:user-course-detail',
                                                      kwargs={'course_id': self.course.id}))
            self.assertEqual(1, Topic.objects.count())
            self.assertEqual(1, Topic.objects.filter(course=self.course).count())


class TestAddNewIncludedMaterialView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.topic = TopicFactory(course=self.course, week=self.week)
        self.url = reverse('dashboard:education:course-management:add-new-included-material',
                           kwargs={'course_id': self.course.id,
                                   'topic_id': self.topic.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_create_new_material_for_topic_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        material_count = IncludedMaterial.objects.count()
        topic_material_count = self.topic.materials.count()
        data = {
            'identifier': faker.name(),
            'url': faker.url(),
            'content': faker.text(),
            'topic': self.topic.id,
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}
            ))
            self.assertEqual(material_count + 1, IncludedMaterial.objects.count())
            self.assertEqual(topic_material_count + 1, self.topic.materials.count())


class TestAddIncludedMaterialFromExistingView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.topic = TopicFactory(course=self.course, week=self.week)
        self.url = reverse('dashboard:education:course-management:add-included-material-from-existing',
                           kwargs={'course_id': self.course.id,
                                   'topic_id': self.topic.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_add_ordinary_material_to_course(self):
        material_count = IncludedMaterial.objects.count()
        teacher = Teacher.objects.create_from_user(self.user)
        material = MaterialFactory()
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            response = self.post(self.url, data={'material': material.id})
            self.assertEqual(material_count + 1, IncludedMaterial.objects.count())
            included_material = IncludedMaterial.objects.filter(material=material)
            self.assertEqual(1, Topic.objects.filter(materials__in=included_material).count())

    def test_can_add_included_material_from_existing_included_materials(self):
        course = CourseFactory()
        topic = TopicFactory(course=course)
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        included_material = IncludedMaterialFactory(topic=topic)

        included_material_count = IncludedMaterial.objects.count()
        material_count = Material.objects.count()

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data={'material': included_material.material.id})
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}))
            self.assertEqual(included_material_count + 1, IncludedMaterial.objects.count())
            self.assertEqual(material_count, Material.objects.count())


class TestAddNewIncludedTaskView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.topic = TopicFactory(course=self.course, week=self.week)
        self.url = reverse('dashboard:education:course-management:add-new-included-task',
                           kwargs={'course_id': self.course.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_create_new_task_for_topic_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        task_count = IncludedTask.objects.count()
        topic_task_count = self.topic.tasks.count()
        data = {
            'name': faker.name(),
            'description': faker.text(),
            'topic': self.topic.id,
        }

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}
            ))
            self.assertEqual(task_count + 1, IncludedTask.objects.count())
            self.assertEqual(topic_task_count + 1, self.topic.tasks.count())


class TestAddIncludedTaskFromExistingView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.topic = TopicFactory(course=self.course, week=self.week)
        self.url = reverse('dashboard:education:course-management:add-included-task-from-existing',
                           kwargs={'course_id': self.course.id})
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_can_add_ordinary_task_that_has_not_yet_been_included_to_course(self):
        task_count = IncludedTask.objects.count()
        teacher = Teacher.objects.create_from_user(self.user)
        task = TaskFactory()
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)
            response = self.post(self.url, data={'task': task.id, 'topic': self.topic.id})
            self.assertEqual(task_count + 1, IncludedTask.objects.count())
            included_task = IncludedTask.objects.filter(task=task)
            self.assertEqual(1, Topic.objects.filter(tasks__in=included_task).count())

    def test_can_add_included_task_from_existing_already_included_tasks(self):
        course = CourseFactory()
        topic = TopicFactory(course=course)
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        included_task = IncludedTaskFactory(topic=topic)

        included_task_count = IncludedTask.objects.count()
        task_count = Task.objects.count()

        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(self.url, data={'task': included_task.task.id, 'topic': self.topic.id})
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id}))
            self.assertEqual(included_task_count + 1, IncludedTask.objects.count())
            self.assertEqual(task_count, Task.objects.count())


class TestEditIncludedTaskView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.topic = TopicFactory(course=self.course, week=self.week)
        self.included_task = IncludedTaskFactory(topic=self.topic)
        self.url = reverse('dashboard:education:course-management:edit-included-task',
                           kwargs={
                               'course_id': self.course.id,
                               'task_id': self.included_task.id
                           })
        self.test_password = faker.password()
        self.user = BaseUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_included_task_is_edited_successfully_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        new_name = faker.name()
        data = {
            'name': new_name,
            'topic': self.included_task.topic.id,
            'description': self.included_task.task.description
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id})
            )
            self.included_task.refresh_from_db()
            self.assertEquals(new_name, self.included_task.name)


class TestEditTaskView(TestCase):

    def setUp(self):
        self.task = TaskFactory()
        self.url = reverse('dashboard:education:edit-task',
                           kwargs={
                               'task_id': self.task.id
                           })
        self.test_password = faker.password()
        self.user = SuperUserFactory(password=self.test_password)

    def test_get_is_forbidden_if_not_superuser(self):
        response = self.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_superuser(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_task_is_edited_successfully_on_post(self):
        new_name = faker.name()
        data = {
            'name': new_name,
            'description': self.task.description,
            'gradable': self.task.gradable
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-courses',
            ))
            self.task.refresh_from_db()
            self.assertEquals(new_name, self.task.name)


class TestAddSourceCodeTestToTaskView(TestCase):

    def setUp(self):
        self.course = CourseFactory()
        self.week = WeekFactory(course=self.course)
        self.topic = TopicFactory(course=self.course, week=self.week)
        self.included_task = IncludedTaskFactory(topic=self.topic)
        self.test_password = faker.password()
        self.language = ProgrammingLanguageFactory()
        self.user = BaseUserFactory(password=self.test_password)
        self.url = reverse('dashboard:education:course-management:add-source-test',
                           kwargs={
                               'course_id': self.course.id,
                               'task_id': self.included_task.id,
                           })

    def test_get_is_forbidden_if_not_teacher_for_course(self):
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(403, response.status_code)

    def test_get_is_allowed_when_teacher_for_course(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        with self.login(email=self.user.email, password=self.test_password):
            response = self.get(self.url)
            self.assertEqual(200, response.status_code)

    def test_source_test_is_added_to_task_on_post(self):
        teacher = Teacher.objects.create_from_user(self.user)
        add_teacher(self.course, teacher)
        source_test_count = SourceCodeTest.objects.count()
        task_tests = self.included_task.tests.count()
        data = {
            'language': self.language.id,
            'code': faker.text()
        }
        with self.login(email=self.user.email, password=self.test_password):
            response = self.post(url_name=self.url, data=data)
            self.assertRedirects(response, expected_url=reverse(
                'dashboard:education:user-course-detail',
                kwargs={'course_id': self.course.id})
            )
            self.assertEqual(source_test_count + 1, SourceCodeTest.objects.count())
            self.assertEqual(task_tests + 1, self.included_task.tests.count())
