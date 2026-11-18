from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Copy, Item, Loan


class ItemAvailabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Игры')
        cls.item = Item.objects.create(
            title='Игра',
            category=category,
            description='Описание',
            daily_price=100,
        )
        cls.hidden = Item.objects.create(
            title='Скрытая',
            category=category,
            description='Описание',
            daily_price=100,
            is_published=False,
        )
        cls.user = get_user_model().objects.create_user(username='player')
        cls.free_copy = Copy.objects.create(item=cls.item, inventory_number='FREE')
        cls.closed_copy = Copy.objects.create(item=cls.item, inventory_number='CLOSED')
        cls.busy_copy = Copy.objects.create(item=cls.item, inventory_number='BUSY')
        Copy.objects.create(
            item=cls.item, inventory_number='BROKEN', is_serviceable=False
        )
        now = timezone.now()
        for copy in (cls.closed_copy, cls.busy_copy):
            Loan.objects.create(
                user=cls.user,
                copy=copy,
                status=Loan.Status.CLOSED,
                daily_days=1,
                daily_price_snapshot=100,
                created_at=now,
                closed_at=now,
            )
        Loan.objects.create(
            user=cls.user,
            copy=cls.busy_copy,
            status=Loan.Status.ACTIVE,
            daily_days=1,
            daily_price_snapshot=100,
        )

    def test_current_availability_and_no_cache(self):
        url = reverse('rental:item_availability', args=[self.item.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'available_count': 2})
        self.assertIn('no-store', response['Cache-Control'])
        Loan.objects.create(
            user=self.user,
            copy=self.free_copy,
            status=Loan.Status.RESERVED,
            daily_days=1,
            daily_price_snapshot=100,
        )
        self.assertEqual(self.client.get(url).json(), {'available_count': 1})

    def test_hidden_and_missing_items_are_not_available(self):
        for pk in (self.hidden.pk, 999999):
            with self.subTest(pk=pk):
                response = self.client.get(
                    reverse('rental:item_availability', args=[pk])
                )
                self.assertEqual(response.status_code, 404)

    def test_only_get_is_allowed(self):
        response = self.client.post(
            reverse('rental:item_availability', args=[self.item.pk])
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Allow'], 'GET')
