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

    def test_main_navigation_links(self):
        response = self.client.get(reverse('rental:catalog'))
        for name in ('subscription', 'login', 'loans', 'item', 'search'):
            with self.subTest(name=name):
                url = reverse(f'rental:{name}')
                self.assertContains(response, url)

    def test_all_pages_render(self):
        for name in ('catalog', 'item', 'subscription', 'login', 'loans', 'search'):
            with self.subTest(name=name):
                response = self.client.get(reverse(f'rental:{name}'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<h1', count=1)

    def test_search_query_is_escaped(self):
        response = self.client.get(reverse('rental:search'), {'q': '<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
