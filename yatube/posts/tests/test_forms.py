import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment
from posts.forms import CommentForm


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.user = User.objects.create(username="Vasy")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст поста",
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись."""
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00"
            b"\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        img = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        id_old = list(
            Post.objects.filter(author=self.user).values_list("id", flat=True)
        )
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст созданного поста",
            "group": self.group.id,
            "image": img,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        new_post = Post.objects.all().exclude(id__in=id_old)
        result_post = new_post[0]
        self.assertRedirects(
            response, reverse("posts:profile", kwargs={"username": self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(result_post.text, form_data["text"])
        self.assertEqual(result_post.group.id, form_data["group"])
        self.assertEqual(
            result_post.image.name, f'posts/{form_data["image"].name}'
        )

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        post = PostFormTests.post
        form_data = {
            "text": "Текст обновлённого поста",
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        post.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
        )
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, form_data["group"])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="Vasy")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст поста",
        )
        cls.form = CommentForm

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_not_authorized(self):
        url = reverse("posts:add_comment", kwargs={"post_id": self.post.id})
        response = self.client.get(url)
        response_authorized = self.authorized_client.get(url)
        url2 = reverse("users:login")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response_authorized.status_code, 302)
        self.assertRedirects(
            response, f"{url2}?next=/posts/{self.post.id}/comment/"
        )
        self.assertRedirects(
            response_authorized,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
        )

    def test_comment_creat(self):
        comment_cut = Comment.objects.count()
        form_data = {"text": "Тестовый коммит"}
        self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        comment = Comment.objects.last()
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        comments = response.context["comments"]
        self.assertEqual(Comment.objects.count(), comment_cut + 1)
        self.assertEqual(comment.text, form_data["text"])
        self.assertIn(comment, comments)
