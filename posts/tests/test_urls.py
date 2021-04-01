from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.another_user = User.objects.create(username='another_test_user')
        cls.group = Group.objects.create(
            title='Test',
            description='Много букв',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизированный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

        self.templates_urls = {
            '/': 'index.html',
            f'/group/{self.group.slug}/': 'group.html',
            '/new/': 'create_or_update_post.html',
            f'/{self.user.username}/': 'profile.html',
            f'/{self.user.username}/{str(self.post.id)}/': 'post.html',
            f'/{self.user.username}/{str(self.post.id)}/edit/':
                'create_or_update_post.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def test_urls_200(self):
        """Тестируем доступность страниц для пользователя"""
        for key in self.templates_urls.keys():
            with self.subTest():
                response = self.authorized_client.get(key)
                self.assertEqual(response.status_code, 200)

    def test_edit_page_for_not_author(self):
        """Тестируем доступность страницы /<str:username>/<int:post_id>/edit/
        для авторизованного пользователя, не автора поста"""
        authorized_client = Client()
        authorized_client.force_login(self.another_user)
        response = authorized_client.get(
            f'/{self.user.username}/{str(self.post.id)}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_redirect_guest_client(self):
        """Тестируем редирект для страницы /new/"""
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_redirect_guest_client_for_edit_page(self):
        """Тестируем редирект для страницы
        /<str:username>/<int:post_id>/edit/ """
        response = self.guest_client.get(
            f'/{self.user.username}/{str(self.post.id)}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/{self.user.username}/'
             f'{str(self.post.id)}/edit/')
        )
        response = self.guest_client.get(
            f'/{self.user.username}/{str(self.post.id)}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/{self.user.username}/'
             f'{str(self.post.id)}/edit/')
        )

    def test_url_correct_template(self):
        """Тестируем шаблоны страниц"""
        for reverse_name, template in self.templates_urls.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_error_404_page(self):
        """Сервер возвращает код 404, если страница не найдена"""
        response = self.guest_client.get("/doest_exist/")
        self.assertEqual(response.status_code, 404)
