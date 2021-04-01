from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name="Название сообщества",
                             help_text="Название сообщества")
    slug = models.SlugField(unique=True, verbose_name="Метка",
                            help_text="Метка")
    description = models.TextField(max_length=200,
                                   verbose_name="Описание сообщества",
                                   help_text="Описание сообщества")

    class Meta:
        verbose_name = "Сообщество"
        verbose_name_plural = "Сообщества"

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст", help_text="Текст")
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts", verbose_name="Автор",
                               help_text="Автор")
    group = models.ForeignKey("Group", on_delete=models.SET_NULL,
                              related_name="posts", blank=True, null=True,
                              verbose_name="Сообщество",
                              help_text="Сообщество")
    image = models.ImageField(verbose_name="Картинка", upload_to="posts/",
                              blank=True, null=True,
                              help_text="Загрузите картинку")

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField(verbose_name="Текст комментария",
                            help_text="Введите комментарий")
    created = models.DateTimeField("Дата публикации комментария",
                                   auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-created"]

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")

    class Meta:
        unique_together = ["user", "author"]
