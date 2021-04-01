from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Ж' * 100,
            description='Много букв'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        group = PostModelTest.group
        post_field_verboses = {
            'text': 'Текст',
            'group': 'Сообщество',
        }
        group_field_verboses = {
            'title': 'Название сообщества',
            'description': 'Описание сообщества',
            'slug': 'Метка'
        }
        for value, expected in post_field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)
        for value, expected in group_field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст',
            'group': 'Сообщество'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_object_name_feild(self):
        """В поле __str__  объекта post записано значение поля post.text.
           В поле __str__  объекта group записано значение поля group.title.
        """
        group = PostModelTest.group
        post = PostModelTest.post
        expected_object_name = group.title
        expected_object_name_for_post = post.text[:15]
        self.assertEqual(expected_object_name, str(group))
        self.assertEqual(expected_object_name_for_post, str(post))
