from django.test import Client, TestCase


class TestAboutUrls(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'
        }

    def test_about_urls_exists_at_desire_location(self):
        """Страницы about доступны неавторизованному пользователю."""
        for adress in self.templates_url_names.values():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """ Открывается соответствующий шаблон."""
        for template, adress in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
