from http import HTTPStatus

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from authapp import models as authapp_models
from mainapp import models as mainapp_models


class TestNewsPage(TestCase):
    fixtures = [
        "001_news.json",
        "001_user_admin.json",
    ]

    def setUp(self):
        super().setUp()
        self.client_with_auth = Client()
        self.user_admin = authapp_models.CustomUser.objects.get(username="admin")
        self.client_with_auth.force_login(self.user_admin, backend="django.contrib.auth.backends.ModelBackend")

    def test_page_open_list(self):
        path = reverse("mainapp:news")
        result = self.client.get(path)
        self.assertEqual(result.status_code, HTTPStatus.OK)

    def test_page_open_detail(self):
        news_obj = mainapp_models.News.objects.first()
        path = reverse("mainapp:news_detail", args=[news_obj.pk])
        result = self.client.get(path)
        self.assertEqual(result.status_code, HTTPStatus.OK)

    def test_page_open_crete_deny_access(self):
        path = reverse("mainapp:news_create")
        result = self.client.get(path)
        self.assertEqual(result.status_code, HTTPStatus.FOUND)

    def test_page_open_crete_by_admin(self):
        path = reverse("mainapp:news_create")
        result = self.client_with_auth.get(path)
        self.assertEqual(result.status_code, HTTPStatus.OK)

    def test_create_in_web(self):
        counter_before = mainapp_models.News.objects.count()
        path = reverse("mainapp:news_create")
        self.client_with_auth.post(
            path,
            data={
                "title": "NewTestNews001",
                "preambule": "NewTestNews001",
                "body": "NewTestNews001",
            },
        )
        self.assertGreater(mainapp_models.News.objects.count(), counter_before)

    def test_page_open_update_deny_access(self):
        news_obj = mainapp_models.News.objects.first()
        path = reverse("mainapp:news_update", args=[news_obj.pk])
        result = self.client.get(path)
        self.assertEqual(result.status_code, HTTPStatus.FOUND)

    def test_page_open_update_by_admin(self):
        news_obj = mainapp_models.News.objects.first()
        path = reverse("mainapp:news_update", args=[news_obj.pk])
        result = self.client_with_auth.get(path)
        self.assertEqual(result.status_code, HTTPStatus.OK)

    def test_update_in_web(self):
        new_title = "NewTestTitle001"
        news_obj = mainapp_models.News.objects.first()
        self.assertNotEqual(news_obj.title, new_title)
        path = reverse("mainapp:news_update", args=[news_obj.pk])
        result = self.client_with_auth.post(
            path,
            data={
                "title": new_title,
                "preambule": news_obj.preambule,
                "body": news_obj.body,
            },
        )
        self.assertEqual(result.status_code, HTTPStatus.FOUND)
        news_obj.refresh_from_db()
        self.assertEqual(news_obj.title, new_title)

    def test_delete_deny_access(self):
        news_obj = mainapp_models.News.objects.first()
        path = reverse("mainapp:news_delete", args=[news_obj.pk])
        result = self.client.post(path)
        self.assertEqual(result.status_code, HTTPStatus.FOUND)

    def test_delete_in_web(self):
        news_obj = mainapp_models.News.objects.first()
        path = reverse("mainapp:news_delete", args=[news_obj.pk])
        self.client_with_auth.post(path)
        news_obj.refresh_from_db()
        self.assertTrue(news_obj.deleted)


# class TestCoursesWithMock(TestCase):
# fixtures = (
#     "001_user_admin.json",
#     "002_courses.json",
#     "003_lessons.json",
#     "004_teachers.json",
# )

# def test_page_open_detail(self):
#     course_obj = mainapp_models.Courses.objects.get(pk=1)
#     path = reverse("mainapp:courses_detail", args=[course_obj.pk])
#     with open("Django-Framework/mainapp/fixtures/005_feedback_list_1.bin", "rb") as inpf, mock.patch(
#         "django.core.cache.cache.get"
#     ) as mocked_cache:
#         mocked_cache.return_value = pickle.load(inpf)
#         result = self.client.get(path)
#         self.assertEqual(result.status_code, HTTPStatus.OK)
#         self.assertTrue(mocked_cache.called)


from django.core import mail as django_mail

from mainapp import tasks as mainapp_tasks


class TestTaskMailSend(TestCase):
    fixtures = ("001_user_admin.json",)

    def test_mail_send(self):
        message_text = "test_message_text"
        user_obj = authapp_models.CustomUser.objects.first()
        mainapp_tasks.send_feedback_mail({"user_id": user_obj.id, "message": message_text})
        self.assertEqual(django_mail.outbox[0].body, message_text)


from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestNewsSelenium(StaticLiveServerTestCase):

    fixtures = (
        "001_user_admin.json",
        "001_news.json",
    )

    def setUp(self):
        super().setUp()
        # Инициализируем WebDriver с использованием Service
        service = Service(settings.SELENIUM_DRIVER_PATH_FF)  # Замените на свой путь к chromedriver или geckodriver
        self.selenium = webdriver.Chrome(service=service)  # Здесь создаем объект WebDriver
        self.selenium.implicitly_wait(10)  # Устанавливаем неявное ожидание

        # Логинимся
        self.selenium.get(f"{self.live_server_url}{reverse('authapp:login')}")
        button_enter = WebDriverWait(self.selenium, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[type="submit"]'))
        )
        self.selenium.find_element(value="id_username").send_keys("admin")
        self.selenium.find_element(value="id_password").send_keys("admin")
        button_enter.click()

        # Ожидаем появления футера
        WebDriverWait(self.selenium, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "mt-auto")))

    def test_create_button_clickable(self):
        path_list = f"{self.live_server_url}{reverse('mainapp:news')}"
        path_add = reverse("mainapp:news_create")
        self.selenium.get(path_list)

        button_create = WebDriverWait(self.selenium, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f'[href="{path_add}"]'))
        )
        print("Trying to click button ...")
        button_create.click()  # Тестируем, что кнопка кликабельна
        WebDriverWait(self.selenium, 5).until(EC.visibility_of_element_located((By.ID, "id_title")))
        print("Button clickable!")

    def test_pick_color(self):
        path = f"{self.live_server_url}{reverse('mainapp:main_page')}"
        self.selenium.get(path)
        navbar_el = WebDriverWait(self.selenium, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "navbar")))
        try:
            self.assertEqual(
                navbar_el.value_of_css_property("background-color"),
                "rgb(255, 255, 155)",
            )
        except AssertionError:
            # Сохраняем скриншот, если проверка не прошла
            with open("var/screenshots/001_navbar_el_scrnsht.png", "wb") as outf:
                outf.write(navbar_el.screenshot_as_png)
            raise

    def tearDown(self):
        # Закрываем браузер
        self.selenium.quit()
        super().tearDown()
