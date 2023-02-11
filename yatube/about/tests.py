from http import HTTPStatus

from django.test import TestCase, Client


class StaticPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов about и tech."""
        url_location = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for adress, expected_value in url_location.items():
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.guest_client.get(adress).status_code,
                    expected_value
                )

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов для адресов about и tech."""
        url_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for adress, expected_value in url_template.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(
                    self.guest_client.get(adress),
                    expected_value
                )
