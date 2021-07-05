from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PostModelTest.user = User.objects.create(
            username='test_user'
        )
        PostModelTest.post = Post.objects.create(
            text=3 * 'Строка состоит из 30 символов ',
            author=PostModelTest.user
        )
        PostModelTest.post_2 = Post.objects.create(
            text='Короткий',
            author=PostModelTest.user
        )

    def test_object_name_is_title_15_symbols(self):
        """ __str__ - это 15 знаков поля text. """
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_object_name_short_text(self):
        """ Проверка __str__ при коротком поле text. """
        post = PostModelTest.post_2
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_verbose_name(self):
        """ verbose_name совпадает с ожидаемым. """
        post = PostModelTest.post
        verbose_field = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Сообщество'
        }
        for field, expected_values in verbose_field.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_values)

    def test_help_text(self):
        """ help_text совпадает с ожидаемым. """
        post = PostModelTest.post
        verbose_field = {
            'text': 'Введите текст поста',
            'group': 'Выберите сообщество'
        }
        for field, expected_value in verbose_field.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        GroupModelTest.group = Group.objects.create(
            title=3 * 'Название тестовой группы',
            slug='test-group',
            description='Описание тестовой группы'
        )
        GroupModelTest.group_2 = Group.objects.create(
            title='Название',
            slug='test-group-2',
            description='Описание тестовой группы'
        )

    def test_object_name_is_group_name_long_title(self):
        """ __str__ - это название группы, длинная строка. """
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_object_name_is_group_name_short_title(self):
        """ __str__ - это название группы, короткая строка. """
        group = GroupModelTest.group_2
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
