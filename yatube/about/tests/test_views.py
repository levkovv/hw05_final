from django.test import Client, TestCase
from django.urls import reverse


class TestAboutViews(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.templates_pages_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }

    def test_pages_acessible_by_name(self):
        """ URL страниц, генерируемых по имени функции доступны."""
        for reverse_name in self.templates_pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_pages_use_correct_template(self):
        """При обращении к страницам используется ожидаемый шаблон """
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
