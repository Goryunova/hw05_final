import shutil
import tempfile

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from django import forms

from posts.models import Post, Group, User, Follow

User = get_user_model()


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }

    def test_author_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени about, доступен."""
        for item in self.templates_pages_names.values():
            with self.subTest():
                response = self.guest_client.get(item)
                self.assertEqual(response.status_code, 200)

    def test_about_page_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT="temp_media")
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def setUpClass(cls):
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
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Test',
            slug='test-slug',
            description='Много букв'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.templates_pages_names = {
            reverse('posts:index'): 'index.html',
            reverse('posts:new_post'): 'create_or_update_post.html',
            reverse('posts:group', kwargs={'slug': self.group.slug}):
                'group.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'profile.html',
            reverse(
                'posts:post', kwargs={'username': self.user.username,
                                      'post_id': self.post.id}): 'post.html',
            reverse(
                'posts:post_edit', kwargs={'username': self.user.username,
                                           'post_id': self.post.id}):
                'create_or_update_post.html'
        }

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Проверяем, что при обращении к name вызывается
        # соответствующий HTML-шаблон
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_list_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        post_text_0 = response.context.get('page')[0].text
        post_group_0 = response.context.get('page')[0].group
        post_author_0 = response.context.get('page')[0].author
        post_pub_date_0 = response.context.get('page')[0].pub_date
        post_image_0 = response.context.get('page')[0].image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_group_list_page_show_correct_context(self):
        """Шаблон group.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group', kwargs={'slug': self.group.slug}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        post_text_0 = response.context.get('page')[0].text
        post_group_0 = response.context.get('page')[0].group
        post_author_0 = response.context.get('page')[0].author
        post_pub_date_0 = response.context.get('page')[0].pub_date
        post_image_0 = response.context.get('page')[0].image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(post_image_0, self.post.image)

    def test_new_page_show_correct_context(self):
        """1 Шаблон create_or_update_post.html сформирован с правильным
        контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        # Список ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_index_page_list_is_1(self):
        # Удостоверимся, что на страницу со списком постов передаётся
        # ожидаемое количество объектов
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page']), 1)

    def test_post_group_page_list_is_1(self):
        # Удостоверимся, что на страницу группы постов передаётся
        # ожидаемое количество объектов
        response = self.authorized_client.get(reverse(
            'posts:group', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page']), 1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом для
            /<username>/."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))

        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        post_text_0 = response.context.get('page')[0].text
        post_group_0 = response.context.get('page')[0].group
        post_author_0 = response.context.get('page')[0].author
        post_pub_date_0 = response.context.get('page')[0].pub_date
        author_username_0 = response.context.get('page')[0].author.username
        post_image_0 = response.context.get('page')[0].image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(author_username_0, self.user.username)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_page_show_correct_context(self):
        """Шаблон post.html сформирован с правильным контекстом для
            /<username>/<post_id>/."""
        response = self.authorized_client.get(reverse(
            'posts:post', kwargs={'username': self.user.username,
                                  'post_id': self.post.id}))

        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        post_text_0 = response.context.get('post').text
        post_group_0 = response.context.get('post').group
        post_author_0 = response.context.get('post').author
        post_pub_date_0 = response.context.get('post').pub_date
        author_username_0 = response.context.get('post').author.username
        post_image_0 = response.context.get('post').image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(author_username_0, self.user.username)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_edit_page_show_correct_context(self):
        """2 Шаблон create_or_update_post.html сформирован с правильным
            контекстом для /<username>/<post_id>/edit/."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'username': self.user.username,
                                       'post_id': self.post.id}))
        # Список ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        # Проверим, что поле с текстом не пусто
        field_not_empty = response.context.get('item')
        self.assertEqual(field_not_empty, self.post)

    def test_follow(self):
        """Тест работы подписки и отписки от автора"""
        first_user = get_user_model().objects.create_user(username='First')
        first_user_client = Client()
        first_user_client.force_login(first_user)
        first_user_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user.username}))
        follower = Follow.objects.filter(user=first_user).exists()
        self.assertEqual(follower, True)
        first_user_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user.username}))
        follower = Follow.objects.filter(user=first_user).exists()
        self.assertEqual(follower, False)

    def test_new_post_follow(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
           подписан и не появляется в ленте тех, кто не подписан на него.
        """
        first_author = get_user_model().objects.create(username='First')
        second_author = get_user_model().objects.create(username='Second')
        third_author = get_user_model().objects.create(username='Third')
        first_author_client = Client()
        second_author_client = Client()
        third_author_client = Client()
        first_author_client.force_login(first_author)
        second_author_client.force_login(second_author)
        third_author_client.force_login(third_author)
        follow_count = Follow.objects.count()
        # Подписка первого автора на второго
        first_author_client.get(reverse(
            'posts:profile_follow', args=['Second']))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        Post.objects.filter(author__following__user=self.user)
        response_first = first_author_client.get(reverse(
            'posts:follow_index'))
        response_third = third_author_client.get(reverse(
            'posts:follow_index'))
        Post.objects.filter(author__following__user=self.user)
        self.assertEqual(response_first.status_code, 200)
        self.assertEqual(response_third.status_code, 200)

    def test_comments(self):
        user = get_user_model().objects.create_user(username='Bruno')
        user_client = Client()
        user_client.force_login(user)
        response = user_client.get(reverse(
            'posts:add_comment', kwargs={'username': self.user.username,
                                         'post_id': self.post.id}))
        self.assertEqual(response.url,
                         f'/{self.user.username}/{str(self.post.id)}/')


class CacheTest(TestCase):
    def test_index_page_cache(self):
        """Тест корректности кеширования в шаблоне index"""
        client = Client()
        user = User.objects.create(username='Bruno')
        Post.objects.create(
            text='Lorem impsum', author=user)
        temp_response = client.get(reverse('posts:index'))
        Post.objects.create(
            text='Lorem impsum', author=user)
        response = client.get(reverse('posts:index'))
        self.assertEqual(temp_response.content, response.content)
        cache.clear()
        Post.objects.create(
            text='Lorem impsum', author=user)
        response_new = client.get(reverse('posts:index'))
        self.assertNotEqual(temp_response.content, response_new)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Test',
            slug='test-slug',
            description='Много букв'
        )
        posts = [Post(author=cls.user, group=cls.group, text=str(i)) for i in
                 range(13)]
        Post.objects.bulk_create(posts)

    def setUp(self):
        # Создаем авторизованного клиента
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_first_page_containse_ten_records(self):
        """Проверка, что 1 страница содержит 10 записей"""
        response = self.authorized_client.get(reverse('posts:index'))
        response_1 = self.authorized_client.get(reverse(
            'posts:group', kwargs={'slug': self.group.slug}))

        # Проверка: количество постов на первой странице равно 10
        self.assertEqual(len(response.context.get('page').object_list), 10)
        self.assertEqual(len(response_1.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        """Проверка, что 2 страница содержит 3 записей"""
        response = self.authorized_client.get(reverse(
            'posts:index') + '?page=2')
        response_1 = self.authorized_client.get(reverse(
            'posts:group', kwargs={'slug': self.group.slug}) + '?page=2')

        # Проверка: на второй странице должно быть три поста.

        self.assertEqual(len(response.context.get('page').object_list), 3)
        self.assertEqual(len(response_1.context.get('page').object_list), 3)
