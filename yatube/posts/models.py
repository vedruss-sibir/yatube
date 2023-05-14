from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, blank=True, unique=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Tекст поста")
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        verbose_name="Название группы",
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    image = models.ImageField("Картинка", upload_to="posts/", blank=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text


class Comment(models.Model):
    post = models.ForeignKey(
        Post, related_name="comments", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name="comments", on_delete=models.CASCADE
    )
    text = models.TextField(verbose_name="Tекст комментария")
    created = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
    )
