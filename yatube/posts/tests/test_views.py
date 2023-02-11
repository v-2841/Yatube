import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.get(username='test_author'),
            group=Group.objects.get(slug='test-group'),
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_about_view_uses_correct_template(self):
        """Проверка view-функций на правильное отображение шаблонов."""
        view_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for value, expected_value in view_template.items():
            with self.subTest(value=value):
                self.assertTemplateUsed(
                    self.authorized_client.get(value),
                    expected_value
                )

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        form_fields = {
            first_post.text: self.post.text,
            first_post.group.title: self.group.title,
            first_post.author.username: self.user.username,
            first_post.image: self.post.image
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_post = response.context['page_obj'][0]
        form_fields = {
            first_post.text: self.post.text,
            first_post.group.title: self.group.title,
            first_post.author.username: self.user.username,
            first_post.image: self.post.image
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_post = response.context['page_obj'][0]
        form_fields = {
            first_post.text: self.post.text,
            first_post.group.title: self.group.title,
            first_post.author.username: self.user.username,
            first_post.image: self.post.image
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_data = {
            response.context.get('post').text: self.post.text,
            response.context.get('post').group: self.group.title,
            response.context.get('post').author: self.user.username,
            response.context.get('post').image: self.post.image
        }
        for value, expected in post_data.items():
            with self.subTest(value=value):
                self.assertEqual(post_data[value], expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        post = Post.objects.create(
            text='Тестовый текст +',
            author=self.user,
            group=self.group
        )
        responses = {
            self.client.get(reverse('posts:index')),
            self.client.get(
                reverse('posts:group_list', kwargs={'slug': post.group.slug})),
            self.client.get(
                reverse(
                    'posts:profile', kwargs={'username': post.author.username}
                ))
        }
        for value in responses:
            with self.subTest(value=value):
                self.assertIn(post, value.context['page_obj'])

    def test_post_added_correctly_to_group(self):
        """Пост при создании не добавляется в другую группу"""
        test_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-2'
        )
        posts_count_before = test_group.posts.all().count()
        Post.objects.create(
            text='Тестовый пост +',
            author=self.user,
            group=self.group,
        )
        posts_count_after = test_group.posts.all().count()
        self.assertEqual(posts_count_before, posts_count_after)

    def test_comment_add_to_post(self):
        """Добавленный комментарий появляется на странице поста"""
        comment = Comment.objects.create(
            post=self.post,
            text='Тестовый комментарий',
            author=self.user,
        )
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context.get('comments')[0], comment)

    def test_cache(self):
        """Кэш index работает корректно"""
        new_post = Post.objects.create(
            text='Тестовый кэш',
            author=User.objects.get(username='test_author'),
        )
        response = self.authorized_client.get(reverse('posts:index'))
        cache_post = response.context['page_obj'][0]
        self.assertEqual(new_post, cache_post)
        new_post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(new_post.text, response.content.decode('utf-8'))
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_post = response.context['page_obj'][0]
        self.assertNotEqual(new_post, cache_post)

    def test_new_post(self):
        """Новый пост появляется в follow тех, кто на него подписан"""
        test_author = User.objects.create_user(username='Following')
        Follow.objects.create(user=self.user, author=test_author)
        post = Post.objects.create(author=test_author, text='Тест подписки')
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(post, response.context['page_obj'][0])
        self.test_client = Client()
        self.test_client.force_login(test_author)
        response = self.test_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
        )
        for i in range(settings.POSTS_VIEW_NUM + 1):
            Post.objects.create(
                text=f'Тест {i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_for_guest(self):
        """Тест Paginator для первой страницы гостя"""
        view_response = {
            self.client.get(reverse('posts:index')),
            self.client.get(
                reverse('posts:profile', kwargs={'username': 'test_author'})
            ),
            self.client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-group'})
            ),
        }
        for response in view_response:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_VIEW_NUM
                )

    def test_first_page_for_auth(self):
        """Тест Paginator для первой страницы пользователя"""
        view_response = {
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': 'test_author'})
            ),
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-group'})
            ),
        }
        for response in view_response:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_VIEW_NUM
                )

    def test_second_page_for_guest(self):
        """Тест Paginator для второй страницы гостя"""
        view_response = {
            self.client.get(reverse('posts:index') + '?page=2'),
            self.client.get(
                reverse('posts:profile', kwargs={'username': 'test_author'})
                + '?page=2'
            ),
            self.client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-group'})
                + '?page=2'
            ),
        }
        for response in view_response:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    1
                )

    def test_second_page_for_auth(self):
        """Тест Paginator для второй страницы пользователя"""
        view_response = {
            self.authorized_client.get(reverse('posts:index') + '?page=2'),
            self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': 'test_author'})
                + '?page=2'
            ),
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-group'})
                + '?page=2'
            ),
        }
        for response in view_response:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    1
                )
