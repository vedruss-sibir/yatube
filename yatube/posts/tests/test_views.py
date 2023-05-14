import tempfile
import shutil

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post, Follow


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        img_creat = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.user = User.objects.create_user(username="Vasy")
        cls.user2 = User.objects.create_user(username="Fedy")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст",
            group=cls.group,
            image=img_creat,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): "posts/profile.html",
            reverse("posts:post_create"): "posts/creat_post.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.id}
            ): "posts/creat_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:index"))
        post = response.context["page_obj"][0]
        post_text = post.text
        post_author = post.author
        post_id = post.id
        post_img = post.image
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_id, self.post.id)
        self.assertEqual(post_img, self.post.image)

    def test_posts_edit_correct_contex(self):
        responce = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        forms_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in forms_fields.items():
            with self.subTest(value=value):
                form_field = responce.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_list_correct_contex(self):
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        post = response.context["page_obj"][0]
        post_group = post.group
        slug = post.group.slug
        post_img = post.image
        self.assertEqual(post_group, self.post.group)
        self.assertEqual(slug, self.group.slug)
        self.assertEqual(post_img, self.post.image)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.post.author})
        )
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        post_author = first_object.author
        post_img = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_img, self.post.image)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с картинкой."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        first_object = response.context["post"]
        post_img = first_object.image
        self.assertEqual(post_img, self.post.image)

    def test_cache_index_page_correct_context(self):
        """Кэш index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:index"))
        content = response.content
        post_id = PostPagesTests.post.id
        instance = Post.objects.get(pk=post_id)
        instance.delete()
        new_response = self.authorized_client.get(reverse("posts:index"))
        new_content = new_response.content
        self.assertEqual(content, new_content)
        cache.clear()
        new_new_response = self.authorized_client.get(reverse("posts:index"))
        new_new_content = new_new_response.content
        self.assertNotEqual(content, new_new_content)

    def test_follow_creat(self):
        follow_cut = Follow.objects.filter(
            user=self.user2, author=self.user
        ).count()
        self.authorized_client2.get(
            reverse("posts:profile_follow", kwargs={"username": self.user})
        )
        self.assertEqual(Follow.objects.count(), follow_cut + 1)

    def test_follow_delete(self):
        Follow.objects.create(user=self.user2, author=self.user)
        follow_cut = Follow.objects.filter(
            user=self.user2, author=self.user
        ).count()
        self.authorized_client2.get(
            reverse("posts:profile_unfollow", kwargs={"username": self.user})
        )
        self.assertEqual(Follow.objects.count(), follow_cut - 1)

    def test_follow_creat_our_user(self):
        response = self.authorized_client.get(
            reverse("posts:profile_follow", kwargs={"username": self.user})
        )
        response2 = self.authorized_client2.get(
            reverse("posts:profile_follow", kwargs={"username": self.user2})
        )
        self.assertNotEqual(response, response2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Vasy")
        cls.group = Group.objects.create(
            title="Тестовая группа 2",
            slug="test-slug-2",
            description="Тестовое описание 2",
        )
        cls.BATCH_SIZE = 13
        cls.obj_list = [
            Post(author=cls.user, text=f"Текст {i}", group=cls.group)
            for i in range(cls.BATCH_SIZE)
        ]
        Post.objects.bulk_create(cls.obj_list)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        reverse_names = (
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.user}),
        )
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context["page_obj"]), settings.NUMBER_POSTS
                )
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + "?page=2")
                self.assertEqual(
                    len(response.context["page_obj"]),
                    (self.BATCH_SIZE - settings.NUMBER_POSTS),
                )


class AdditionalGroupPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="TestUser")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание группы",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый текст поста", group=cls.group
        )

    def test_pages_contains_test_group_post(self):
        """При создании поста с группой он появляется на всех страницах."""
        adresses = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.post.group.slug}),
            reverse("posts:profile", kwargs={"username": self.user.username}),
        ]
        for adress in adresses:
            response = self.client.get(adress)
            first_object = response.context["page_obj"][0]
            post_text = first_object.text
            post_group = first_object.group.title
            self.assertEqual(post_text, self.post.text)
            self.assertEqual(post_group, self.post.group.title)
