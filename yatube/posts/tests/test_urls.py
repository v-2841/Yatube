from http import HTTPStatus

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='test_author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_url_exists_at_desired_location(self):
        """URL-адреса доступны по соответствующим адресам."""
        url_status = [
            ('/', self.client, HTTPStatus.OK),
            (f'/group/{self.group.slug}/', self.client, HTTPStatus.OK),
            (f'/profile/{self.user.username}/', self.client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/', self.client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/edit/', self.client, HTTPStatus.FOUND),
            (f'/posts/{self.post.id}/delete/', self.client, HTTPStatus.FOUND),
            ('/create/', self.client, HTTPStatus.FOUND),
            ('/abracadabra/', self.client, HTTPStatus.NOT_FOUND),
            (f'/posts/{self.post.id}/edit/',
                self.authorized_client, HTTPStatus.FOUND),
            (f'/posts/{self.post.id}/delete/',
                self.authorized_client, HTTPStatus.FOUND),
            ('/create/', self.authorized_client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/edit/',
                self.author_client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/delete/',
                self.author_client, HTTPStatus.OK),
        ]
        for adress, client_name, status in url_status:
            with self.subTest(adress=adress):
                self.assertEqual(
                    client_name.get(adress).status_code, status
                )

    def test_url_redirect_for_not_author(self):
        """Перенаправлние не авторов поста от его редактирования."""
        url_redirects = [
            (f'/posts/{self.post.id}/edit/', self.client,
                f'/auth/login/?next=/posts/{self.post.id}/edit/'),
            (f'/posts/{self.post.id}/delete/', self.client,
                f'/auth/login/?next=/posts/{self.post.id}/delete/'),
            (f'/posts/{self.post.id}/edit/', self.authorized_client,
                f'/posts/{self.post.id}/'),
            (f'/posts/{self.post.id}/delete/', self.authorized_client,
                f'/posts/{self.post.id}/'),
            (f'/posts/{self.post.id}/comment/', self.client,
                f'/auth/login/?next=/posts/{self.post.id}/comment/'),
            (f'/posts/{self.post.id}/comment/', self.authorized_client,
                f'/posts/{self.post.id}/'),
        ]
        for adress, client_name, redirect_url in url_redirects:
            with self.subTest(adress=adress):
                self.assertRedirects(
                    client_name.get(adress, follow=True),
                    redirect_url
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_url_name_for_guest = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            f'/posts/{self.post.id}/delete/': 'posts/delete_post.html',
            '/create/': 'posts/create_post.html',
        }
        for adress, expected_value in template_url_name_for_guest.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(
                    self.author_client.get(adress),
                    expected_value
                )

    def test_comment_add_only_auth(self):
        """Добавить комментарий может только авторизованный пользователь"""
        url_redirects = [
            (f'/posts/{self.post.id}/comment/', self.client,
                f'/auth/login/?next=/posts/{self.post.id}/comment/'),
            (f'/posts/{self.post.id}/comment/', self.authorized_client,
                f'/posts/{self.post.id}/'),
        ]
        for adress, client_name, redirect_url in url_redirects:
            with self.subTest(adress=adress):
                self.assertRedirects(
                    client_name.get(adress, follow=True),
                    redirect_url
                )

    def test_following_only_auth(self):
        """Подписаться на автора может только авторизованный пользователь"""
        url_redirects = [
            (f'/profile/{self.author.username}/follow/', self.client,
                f'/auth/login/?next=/profile/{self.author.username}/follow/'),
            (f'/profile/{self.author.username}/follow/',
                self.authorized_client, f'/profile/{self.author.username}/'),
            (f'/profile/{self.author.username}/unfollow/', self.client,
                f'/auth/login/?next=/profile/'
                f'{self.author.username}/unfollow/'),
            (f'/profile/{self.author.username}/unfollow/',
                self.authorized_client, f'/profile/{self.author.username}/'),
        ]
        for adress, client_name, redirect_url in url_redirects:
            with self.subTest(adress=adress):
                self.assertRedirects(
                    client_name.get(adress, follow=True),
                    redirect_url
                )
