from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем тестовую запись о группе. """
        super().setUpClass()
        PostURLTest.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='Description of test group'
        )
        PostURLTest.user = User.objects.create(
            username='test_user'
        )
        PostURLTest.user_2 = User.objects.create(
            username='another_user'
        )
        PostURLTest.post = Post.objects.create(
            text='Test text',
            author=PostURLTest.user,
            group=PostURLTest.group
        )

    def setUp(self):
        """Создаем неавторизованного и авторизованного клиентов и
        список шаблонов.
        """
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTest.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(PostURLTest.user_2)
        self.templates_url_names = {
            '/': 'index.html',
            f'/group/{PostURLTest.group.slug}/': 'group.html',
            '/new/': 'new.html',
            f'/{PostURLTest.user.username}/': 'profile.html',
            f'/{PostURLTest.user.username}/{PostURLTest.post.id}/':
                'post.html',
            f'/{PostURLTest.user.username}/{PostURLTest.post.id}/edit/':
                'new.html',
            '/follow/': 'follow.html'
        }

    def test_homepage_avalibale_for_guest(self):
        """Главная страница доступна гостевому пользователю. """
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_homepage_avalibale_for_authorized(self):
        """Главная страница доступна авторизованному пользователю. """
        response = self.authorized_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_avalibale_for_guest(self):
        """Страница группы доступна гостевому пользователю. """
        response = self.guest_client.get(f'/group/{PostURLTest.group.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_group_avalible_for_authorized(self):
        """Страница группы доступна авторизованному пользователю. """
        response = self.authorized_client.get(
            f'/group/{PostURLTest.group.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_new_post_avalible_for_authorized(self):
        """Страница нового поста доступна авторизованному пользователю. """
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_new_post_redirect_for_guest_user(self):
        """ Страница нового поста '/new' перенаправит неавторизованного
        пользователя на страницу авторизации.
        """
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_edit_post_avalible_for_post_author(self):
        """ Страница редактирования поста доступна для автора поста"""
        response = self.authorized_client.get(
            f'/{PostURLTest.user.username}/{PostURLTest.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_edit_post_redirect_for_guest_user(self):
        """ Страница редактирования поста перенаправит
        неавторизованного пользователя на страницу авторизации.
        """
        response = self.guest_client.get(
            f'/{PostURLTest.user.username}/{PostURLTest.post.id}/edit/',
            follow=True)
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/{PostURLTest.user.username}/'
                f'{PostURLTest.post.id}/edit/'))

    def test_comment_post_not_avalible_for_guest(self):
        """Гость будет перенаправлен на авторизацию при комментировании."""
        responce = self.guest_client.get(
            f'/{PostURLTest.user.username}/{PostURLTest.post.id}/comment/',
            follow=True)
        self.assertRedirects(
            responce,
            (f'/auth/login/?next=/{PostURLTest.user.username}/'
                f'{PostURLTest.post.id}/comment/')
        )

    def test_edit_post_redirect_not_author_post(self):
        """При попытке редактировать пост не автором поста
        последует перенаправление обратно на страницу поста.
        """
        response = self.another_authorized_client.get(
            f'/{PostURLTest.user.username}/{PostURLTest.post.id}/edit/',
            follow=True)
        self.assertRedirects(
            response, f'/{PostURLTest.user.username}/{PostURLTest.post.id}/')

    def test_urls_use_correct_templates(self):
        """ URL-адреса использует соответствующий шаблон. """
        cache.clear()
        for adress, template in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_not_exist_page_has_404_status(self):
        """ Возвращается код 404 если страница не существует. """
        response = self.guest_client.get('/page_does_not_exist/')
        self.assertEqual(response.status_code, 404)
