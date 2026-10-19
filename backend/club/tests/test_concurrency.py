from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest import skipUnless
from django.contrib.auth.models import User
from django.db import connection, connections, close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from club.models import Event, Profile, Registration, Status
from club.services import register


@skipUnless(
    connection.vendor == 'postgresql',
    'Requires PostgreSQL row locks; covered in CI service integration.',
)
class ConcurrentRegistrationTest(TransactionTestCase):
    def test_last_slot_cannot_be_double_booked(self):
        owner = User.objects.create_user('organizer')
        users = [User.objects.create_user(f'member-{i}') for i in range(2)]
        for user in users:
            Profile.objects.create(user=user, display_name=user.username, is_member=True)
        now = timezone.now()
        event = Event.objects.create(
            owner=owner,
            title='最后一个名额',
            status=Status.PUBLISHED,
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=1),
            registration_deadline=now + timedelta(days=1),
            registration_open=True,
            capacity=1,
        )

        def attempt(user_id):
            close_old_connections()
            try:
                user = User.objects.get(pk=user_id)
                register(user, event.pk, 'test-only')
                return True
            except ValidationError:
                return False
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [user.pk for user in users]))
        self.assertEqual(sum(results), 1)
        self.assertEqual(Registration.objects.filter(event=event, cancelled=False).count(), 1)
