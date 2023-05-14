from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class PostUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая группа",
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_list_not_authorized(self):
        lists = [
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.post.author}/",
            f"/posts/{self.post.id}/",
        ]
        for field in lists:
            with self.subTest(field=field):
                response = self.client.get(field)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_authorized(self):
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_author(self):
        response = self.authorized_client.get(f"/posts/{self.post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_eror(self):
        response = self.client.get("/aboutxxx/author/")
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.post.author}/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            "/create/": "posts/creat_post.html",
            f"/posts/{self.post.id}/edit/": "posts/creat_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
