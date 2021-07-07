import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test.client import Client
from django.test.testcases import TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PostViewsTest.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='Описание тестовой группы'
        )
        PostViewsTest.group_2 = Group.objects.create(
            title='Вторая тестовая группа',
            slug='another-group',
            description='Описание второй тестовой группы'
        )
        PostViewsTest.user = User.objects.create(username='test_user')
        PostViewsTest.user_2 = User.objects.create(username='user_2')
        PostViewsTest.user_3 = User.objects.create(username='user_3')
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
        PostViewsTest.count_posts = 13
        for _ in range(0, PostViewsTest.count_posts):
            PostViewsTest.post = Post.objects.create(
                text='test text',
                author=PostViewsTest.user,
                group=PostViewsTest.group,
                image=uploaded
            )
        Follow.objects.create(
            user=PostViewsTest.user_2,
            author=PostViewsTest.user
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(PostViewsTest.user_2)
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(PostViewsTest.user_3)
        self.templates_pages_name = {
            reverse('index'):
                'index.html',
            reverse('group_posts',
                    kwargs={'slug': f'{PostViewsTest.group.slug}'}):
                'group.html',
            reverse('new_post'):
                'new.html',
            reverse('profile',
                    kwargs={'username': f'{PostViewsTest.user.username}'}):
                'profile.html',
            reverse('post',
                    kwargs={'username': f'{PostViewsTest.user.username}',
                            'post_id': f'{PostViewsTest.post.id}'}):
                'post.html',
            reverse('post_edit',
                    kwargs={'username': f'{PostViewsTest.user.username}',
                            'post_id': f'{PostViewsTest.post.id}'}):
                'new.html',
            reverse('follow_index'): 'follow.html'
        }
        self.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

    def make_expected_and_response_context(self, response):
        """ Создается словарь ожидаемых и фактических элементов контекста."""
        expected_and_response_context = {
            PostViewsTest.post.text: response.text,
            PostViewsTest.post.author: response.author,
            PostViewsTest.post.group: response.group,
            PostViewsTest.post.image: response.image
        }
        return expected_and_response_context

    def test_pages_uses_correct_template(self):
        """При обращении к функции через name вызывается
        соответствующий HTML-шаблон.
        """
        cache.clear()
        for reverse_name, template in self.templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_shows_correct_context(self):
        """На страницу index передается правильный контекст.  """
        cache.clear()
        first_post = self.authorized_client.get(
            reverse('index')).context['page'][0]
        expected_and_response_context = (
            self.make_expected_and_response_context(first_post))
        for expected, value in expected_and_response_context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_group_page_shows_correct_context(self):
        """ На страницу group передается правильный контекст. """
        first_post = (self.authorized_client.
                      get(reverse(
                          'group_posts',
                          kwargs={'slug': f'{PostViewsTest.group.slug}'})).
                      context['page'][0])
        expected_and_response_context = (
            self.make_expected_and_response_context(first_post))
        for expected, value in expected_and_response_context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_profile_page_shows_correct_context(self):
        """ На страницу profile передается правильный контекст."""
        first_post = (self.authorized_client.
                      get(reverse(
                          'profile',
                          kwargs={'username':
                                  f'{PostViewsTest.user.username}'})).
                      context['page'][0])
        expected_and_response_context = (
            self.make_expected_and_response_context(first_post))
        for expected, value in expected_and_response_context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_page_shows_correct_context(self):
        """ На страницу post передается правильный контекст."""
        first_post = (self.authorized_client.
                      get(reverse(
                          'profile',
                          kwargs={'username':
                                  f'{PostViewsTest.user.username}'})).
                      context['post'])
        expected_and_response_context = (
            self.make_expected_and_response_context(first_post))
        for expected, value in expected_and_response_context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_new_post_use_correct_context_fields_type(self):
        """Проверка типа полей контекста для нового поста. """
        response = self.authorized_client.get(reverse('new_post'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_use_correct_context_fields_type(self):
        """Проверка типа полей контекста для редактирования поста. """
        response = self.authorized_client.get(
            reverse(
                'post_edit',
                kwargs={'username': f'{PostViewsTest.user.username}',
                        'post_id': f'{PostViewsTest.post.id}'}))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_another_group_is_empty(self):
        """В пустую группу не попало ни одного поста. """
        response = self.authorized_client.get(
            reverse('group_posts',
                    kwargs={'slug': f'{PostViewsTest.group_2.slug}'}))
        self.assertEqual(len(response.context['page'].object_list), 0)

    def test_paginator_first_page_has_ten_records(self):
        """На первой странице паджинатора 10 записей. """
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context['page'].object_list), 10)

    def test_paginator_second_page_has_three_records(self):
        """На второй странице паджинатора 3 записи. """
        response = self.authorized_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context['page'].object_list), 3)

    def test_paginator_in_group_not_empty(self):
        """ При создании постов они попадают в нужную группу. """
        response = self.authorized_client.get(
            reverse('group_posts',
                    kwargs={'slug': f'{PostViewsTest.group.slug}'}))
        self.assertEqual(len(response.context['page'].object_list), 10)

    def test_cache_index_page(self):
        """Кэшируется главная страница.
        Создали новый пост, он не отразился на главной странице,
        после отчистки кэша он отобразился на главной"""
        cache.clear()
        first_post = (self.authorized_client_2.get(reverse('index')).
                      context['page'][0])
        not_cached_post = {
            'text': 'cache text',
            'author': PostViewsTest.user_2,
            'group': PostViewsTest.group_2
        }
        Post.objects.create(
            text=not_cached_post['text'],
            author=not_cached_post['author'],
            group=not_cached_post['group']
        )
        self.assertNotEqual(first_post.id, PostViewsTest.count_posts + 1)
        cache.clear()
        first_post = (self.authorized_client.get(reverse('index')).
                      context['page'][0])
        self.assertEqual(first_post.id, PostViewsTest.count_posts + 1)
        self.assertEqual(first_post.text, not_cached_post['text'])
        self.assertEqual(first_post.author, not_cached_post['author'])
        self.assertEqual(first_post.group, not_cached_post['group'])

    def test_follower_see_posts(self):
        """Подписчик видит посты автора, на коротого подписался."""
        first_post = (self.authorized_client_2.get(reverse('follow_index')).
                      context['page'][0])
        expected_and_response_context = (
            self.make_expected_and_response_context(first_post))
        for expected, value in expected_and_response_context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_following_is_working(self):
        """Работает подписка на автора."""
        count_follow_note = Follow.objects.count()
        response = self.authorized_client_3.get(
            reverse('profile_follow',
                    kwargs={'username': PostViewsTest.user.username}))
        self.assertEqual(Follow.objects.count(), count_follow_note + 1)
        response = (self.authorized_client_3.get(reverse('follow_index')).
                    context['page'])
        posts_count = len(response)
        self.assertEqual(posts_count, 10)

    def test_unfollowing_is_working(self):
        """Работает отписка от автора."""
        count_follow_note = Follow.objects.count()
        response = self.authorized_client_2.get(
            reverse('profile_unfollow',
                    kwargs={'username': PostViewsTest.user.username}))
        self.assertEqual(Follow.objects.count(), count_follow_note - 1)
        response = (self.authorized_client_2.get(reverse('follow_index')).
                    context['page'])
        posts_count = len(response)
        self.assertEqual(posts_count, 0)

    def test_not_follower_not_see_posts(self):
        """Не подписчик не видит посты автора, на корторого не подписался."""
        response = (self.authorized_client_3.get(reverse('follow_index')).
                    context['page'])
        posts_count = len(response)
        self.assertEqual(posts_count, 0)
