from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Copy, Item, Loan, Plan


class CatalogDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Настольные игры')
        cls.items = [Item.objects.create(
            title=f'Game {number:02}', category=cls.category,
            description='Описание игры', daily_price=Decimal('125.50'),
        ) for number in range(25)]
        cls.hidden = Item.objects.create(
            title='Скрытая игра', category=cls.category, description='Скрыто',
            daily_price=Decimal('100.00'), is_published=False,
        )
        cls.user = get_user_model().objects.create_user(username='player')
        cls.other = get_user_model().objects.create_user(username='other')
        cls.free_copy = Copy.objects.create(item=cls.items[0], inventory_number='FREE')
        cls.busy_copy = Copy.objects.create(item=cls.items[0], inventory_number='BUSY')
        cls.other_copy = Copy.objects.create(item=cls.items[1], inventory_number='OTHER')
        closed_time = timezone.now()
        Loan.objects.create(user=cls.user, copy=cls.free_copy, status='closed',
                            daily_days=1, daily_price_snapshot=1, created_at=closed_time, closed_at=closed_time)
        Loan.objects.create(user=cls.user, copy=cls.busy_copy, status='closed',
                            daily_days=1, daily_price_snapshot=1, created_at=closed_time, closed_at=closed_time)
        Loan.objects.create(user=cls.user, copy=cls.busy_copy, status='active',
                            daily_days=1, daily_price_snapshot=1)
        Loan.objects.create(user=cls.other, copy=cls.other_copy, status='active',
                            daily_days=1, daily_price_snapshot=1)
        Plan.objects.create(name='Доступный тариф', limit=2, price=500, is_active=True)
        Plan.objects.create(name='Скрытый тариф', limit=1, price=100, is_active=False)

    def test_catalog_pagination_and_publication(self):
        first = self.client.get(reverse('rental:catalog'))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.context['page_obj']), 20)
        self.assertEqual(first.context['page_obj'].paginator.count, 25)
        self.assertNotContains(first, 'Скрытая игра')
        self.assertContains(first, reverse('rental:item', args=[self.items[0].pk]))
        second = self.client.get(reverse('rental:catalog'), {'page': 2})
        self.assertEqual(len(second.context['page_obj']), 5)

    def test_available_count_excludes_all_open_loans(self):
        response = self.client.get(reverse('rental:item', args=[self.items[0].pk]))
        self.assertEqual(response.context['item'].available_count, 1)
        self.assertContains(response, 'Доступно экземпляров: 1')
        self.assertEqual(self.client.get(reverse('rental:item', args=[self.hidden.pk])).status_code, 404)

    def test_search_uses_database_and_preserves_query_in_pagination(self):
        response = self.client.get(reverse('rental:search'), {'q': 'Game'})
        self.assertEqual(response.context['page_obj'].paginator.count, 25)
        self.assertContains(response, '?q=Game&amp;page=2')
        response = self.client.get(reverse('rental:search'), {'q': '<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_search_supports_cyrillic_case_insensitive(self):
        self.items[0].title = 'Диксит'
        self.items[0].save(update_fields=['title'])
        response = self.client.get(reverse('rental:search'), {'q': 'диксит'})
        self.assertContains(response, 'Диксит')

    def test_plans_and_personal_loans(self):
        plans = self.client.get(reverse('rental:subscription'))
        self.assertContains(plans, 'Доступный тариф')
        self.assertNotContains(plans, 'Скрытый тариф')
        anonymous = self.client.get(reverse('rental:loans'))
        self.assertNotContains(anonymous, 'BUSY')
        self.client.force_login(self.user)
        own = self.client.get(reverse('rental:loans'))
        self.assertContains(own, 'BUSY')
        self.assertNotContains(own, 'OTHER')

    def test_empty_catalog_and_search(self):
        Item.objects.all().update(is_published=False)
        self.assertContains(self.client.get(reverse('rental:catalog')), 'В каталоге пока нет игр.')
        self.assertContains(self.client.get(reverse('rental:search'), {'q': 'Game'}), 'По вашему запросу ничего не найдено.')


class CatalogImportTests(TestCase):
    def test_load_catalog_does_not_overwrite_existing_records(self):
        call_command('load_catalog', stdout=StringIO())
        self.assertEqual(Item.objects.count(), 30)
        self.assertEqual(Copy.objects.count(), 60)
        self.assertEqual(get_user_model().objects.count(), 0)
        with self.assertRaises(CommandError):
            call_command('load_catalog', stdout=StringIO())
        self.assertEqual(Item.objects.count(), 30)
