from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group

import tempfile
import shutil

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем временную папку для медиа файлов
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        # Создаем запись в базе данных
        cls.user = User.objects.create(username="test_user")
        cls.group = Group.objects.create(
            title="Test",
            description="Много букв",
            slug="test-slug"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст",
            group=cls.group,
            image="small.gif"
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Рекурсивно удаляем временную после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        # Подготавливаем данные для передачи в форму
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст",
            "author": self.user,
            "group": self.group.id,
            "image": uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(reverse("posts:new_post"),
                                               data=form_data, follow=True,)

        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse("posts:index"))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.latest("-pub_date")
        self.assertEqual(last_post.text, form_data["text"])
        self.assertEqual(last_post.author, form_data["author"])
        self.assertEqual(last_post.image, form_data["image"])
        # Проверяем, что создалась запись с нашим слагом
        self.assertTrue(
            Post.objects.filter(group=self.group.id).exists())

    def test_post_edit_save_to_database(self):
        """Проверка редактирования поста в форме /<username>/<post_id>/edit/ -
        изменяется соответствующая запись
        """
        form_data = {
            "text": "Измененный тестовый текст",
            "author": self.user,
            "group": self.group.id,
        }
        test_post = Post.objects.create(
            text="Тестовый текст записи",
            author=self.user,
        )
        self.authorized_client.post(
            reverse("posts:post_edit", args=[self.post.author, self.post.id]),
            data=form_data,
            follow=True
        )
        posts_count = Post.objects.count()
        # Проверяем, что тестовая запись изменилась
        test_post.refresh_from_db()
        self.assertNotEqual(self.post.text, test_post.text,
                            'Запись /<username>/<post_id>/edit/ не изменилась')
        # Проверяем, что колиество записей не изменилось
        self.assertEqual(Post.objects.count(), posts_count,
                         'Кол-во записей увеличивается при редактировании!')
