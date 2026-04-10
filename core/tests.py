from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import School, SystemActivityLog


class SystemActivityLogTests(TestCase):
    def setUp(self):
        self.password = 'StrongPass123!'
        self.user = User.objects.create_user(
            username='auditor',
            password=self.password,
            first_name='Audit',
            last_name='User',
        )
        self.staff_user = User.objects.create_user(
            username='adminuser',
            password=self.password,
            is_staff=True,
        )

    def test_login_and_logout_are_logged(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': self.user.username, 'password': self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SystemActivityLog.objects.filter(
            username=self.user.username,
            action='User logged in',
            event_type=SystemActivityLog.EVENT_AUTH,
        ).exists())

        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SystemActivityLog.objects.filter(
            username=self.user.username,
            action='User logged out',
            event_type=SystemActivityLog.EVENT_AUTH,
        ).exists())

    def test_failed_login_is_logged(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': self.user.username, 'password': 'wrong-password'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SystemActivityLog.objects.filter(
            username=self.user.username,
            action='Failed login attempt',
            event_type=SystemActivityLog.EVENT_SECURITY,
        ).exists())

    def test_school_create_records_action_log(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('core:school_create'), {
            'name': 'Audit School',
            'fee_amount': '25000',
        })
        self.assertEqual(response.status_code, 302)
        school = School.objects.get(name='Audit School')
        log = SystemActivityLog.objects.filter(
            username=self.user.username,
            action='Created school',
        ).latest('created_at')
        self.assertIn(school.name, log.description)

    def test_staff_can_view_system_logs_page(self):
        SystemActivityLog.objects.create(
            user=self.user,
            username=self.user.username,
            action='Manual entry',
            event_type=SystemActivityLog.EVENT_ACTION,
            description='Created for page visibility test.',
        )
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('core:system_activity_logs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'System Activity Logs')
        self.assertContains(response, 'Manual entry')
