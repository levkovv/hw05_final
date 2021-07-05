import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls.base import reverse

from ..models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PostCreateFormTest.user = User.objects.create(
            username='test_user'
        )
        PostCreateFormTest.user_2 = User.objects.create(
            username='another_user'
        )
        PostCreateFormTest.post = Post.objects.create(
            text='Тестовый текст',
            author=PostCreateFormTest.user
        )
        PostCreateFormTest.group = Group.objects.create(
            title='test group',
            slug='test-group'
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTest.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif')
        self.post_form_data = {
            'text': 'Новая запись',
            'group': PostCreateFormTest.group.id,
            'image': uploaded
        }
        self.comment_form_data = {
            'post': PostCreateFormTest.post,
            'author': PostCreateFormTest.user,
            'text': 'Test comment'
        }

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """ Создается и проверяется новый пост в БД, работает редирект."""
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('new_post'),
            self.post_form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, reverse('index'))
        cache.clear()
        response = self.authorized_client.get(
            reverse('index')).context['page'][0]
        self.assertEqual(response.text, self.post_form_data['text'])
        self.assertEqual(response.author, PostCreateFormTest.user)
        self.assertEqual(response.group, PostCreateFormTest.group)
        self.assertEqual(response.image, 'posts/small.gif')

    def test_edit_post(self):
        """ При редактировании е создается еще одна запись в БД и работает редирект.
        И проверяется что пост изменился
        """
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse(
                'post_edit', kwargs={
                    'username': PostCreateFormTest.user.username,
                    'post_id': PostCreateFormTest.post.id}),
            self.post_form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(
            response,
            reverse('post', kwargs={
                'username': PostCreateFormTest.user.username,
                'post_id': PostCreateFormTest.post.id}))
        cache.clear()
        response = self.authorized_client.get(
            reverse('index')).context['page'][0]
        self.assertEqual(response.text, self.post_form_data['text'])
        self.assertEqual(response.author, PostCreateFormTest.user)
        self.assertEqual(response.group, PostCreateFormTest.group)
        self.assertEqual(response.image, 'posts/small.gif')

    def test_add_comment(self):
        """Создается комментарий, работает редирект."""
        comment_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse(
                'add_comment', kwargs={
                    'username': PostCreateFormTest.user.username,
                    'post_id': PostCreateFormTest.post.id}),
            self.comment_form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(
            response,
            reverse('post', kwargs={
                'username': PostCreateFormTest.user.username,
                'post_id': PostCreateFormTest.post.id}))
        response = self.authorized_client.get(
            reverse('post', kwargs={
                'username': PostCreateFormTest.user.username,
                'post_id': PostCreateFormTest.post.id}))
        self.assertEqual(response.context['comments'][0].text,
                         self.comment_form_data['text'])
        self.assertEqual(response.context['comments'][0].author,
                         self.comment_form_data['author'])
        self.assertEqual(response.context['comments'][0].post,
                         self.comment_form_data['post'])
