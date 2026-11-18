from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class AccountFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='existing', email='existing@example.com', password='TestPass#8362'
        )

    def test_register_creates_user_signs_in_and_redirects(self):
        response = self.client.post(
            reverse('rental:register'),
            {
                'username': 'new_player',
                'email': 'new@example.com',
                'password1': 'Adventure#4739',
                'password2': 'Adventure#4739',
            },
        )
        self.assertRedirects(
            response, reverse('rental:catalog'), fetch_redirect_response=False
        )
        user = get_user_model().objects.get(username='new_player')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('Adventure#4739'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertContains(
            self.client.get(reverse('rental:catalog')), 'Аккаунт создан'
        )

    def test_register_rejects_invalid_values_and_preserves_non_password_fields(self):
        response = self.client.post(
            reverse('rental:register'),
            {
                'username': 'new_player',
                'email': 'invalid-email',
                'password1': 'TooShort1!',
                'password2': 'Different2!',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertIn('password2', response.context['form'].errors)
        self.assertContains(response, 'value="new_player"')
        self.assertContains(response, 'value="invalid-email"')
        self.assertNotContains(response, 'value="TooShort1!"')
        self.assertNotContains(response, 'value="Different2!"')
        self.assertFalse(
            get_user_model().objects.filter(username='new_player').exists()
        )

    def test_register_rejects_existing_email_case_insensitively(self):
        response = self.client.post(
            reverse('rental:register'),
            {
                'username': 'new_player',
                'email': 'EXISTING@example.com',
                'password1': 'Adventure#4739',
                'password2': 'Adventure#4739',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertFalse(
            get_user_model().objects.filter(username='new_player').exists()
        )

    def test_empty_post_shows_required_field_errors(self):
        for name, fields in (
            ('login', ('username', 'password')),
            ('register', ('username', 'email', 'password1', 'password2')),
        ):
            with self.subTest(form=name):
                response = self.client.post(reverse(f'rental:{name}'), {})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].is_bound)
                for field in fields:
                    self.assertIn(field, response.context['form'].errors)

    def test_incorrect_login_displays_error_and_keeps_username(self):
        response = self.client.post(
            reverse('rental:login'),
            {
                'username': 'existing',
                'password': 'WrongPass#8362',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertContains(response, 'value="existing"')
        self.assertNotContains(response, 'value="WrongPass#8362"')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_then_logout_requires_post(self):
        response = self.client.post(
            reverse('rental:login'),
            {
                'username': 'existing',
                'password': 'TestPass#8362',
            },
        )
        self.assertRedirects(
            response, reverse('rental:catalog'), fetch_redirect_response=False
        )
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertContains(
            self.client.get(reverse('rental:catalog')), 'Вы вошли в аккаунт.'
        )
        self.assertEqual(self.client.get(reverse('rental:logout')).status_code, 405)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        response = self.client.post(reverse('rental:logout'))
        self.assertRedirects(
            response, reverse('rental:catalog'), fetch_redirect_response=False
        )
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(
            self.client.get(reverse('rental:catalog')), 'Вы вышли из аккаунта.'
        )

    def test_csrf_protection_on_account_forms(self):
        client = Client(enforce_csrf_checks=True)
        for name in ('login', 'register', 'logout'):
            with self.subTest(form=name):
                self.assertEqual(
                    client.post(reverse(f'rental:{name}'), {}).status_code, 403
                )
        client.get(reverse('rental:login'))
        token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('rental:login'),
            {
                'username': 'existing',
                'password': 'TestPass#8362',
                'csrfmiddlewaretoken': token,
            },
        )
        self.assertRedirects(response, reverse('rental:catalog'))
        self.assertEqual(int(client.session['_auth_user_id']), self.user.pk)
