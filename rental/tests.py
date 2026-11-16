from django.test import SimpleTestCase
from django.urls import resolve, reverse

from .views import catalog


class CatalogRouteTests(SimpleTestCase):
    def test_catalog_route_and_page(self):
        url = reverse('rental:catalog')
        self.assertEqual(url, '/')
        self.assertIs(resolve(url).func, catalog)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Игры и консоли')
        self.assertContains(response, f'href="{url}"', count=3)

    def test_planned_pages_have_named_links(self):
        response = self.client.get(reverse('rental:catalog'))
        for name in ('subscription', 'login'):
            with self.subTest(name=name):
                url = reverse(f'rental:{name}')
                self.assertContains(response, f'href="{url}"')
                self.assertContains(self.client.get(url), 'находится в разработке')
