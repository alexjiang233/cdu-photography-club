from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from club.models import Collection, Comment, Event, Profile, Status, Visibility
from django.utils import timezone
from datetime import timedelta


class PublicDiscussionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('photographer')
        cls.profile = Profile.objects.create(user=cls.owner, display_name='原作者', is_member=True)
        cls.work = Collection.objects.create(owner=cls.owner, author=cls.profile, title='公开作品', status=Status.PUBLISHED)
        cls.event = Event.objects.create(owner=cls.owner, title='公开活动', status=Status.PUBLISHED, starts_at=timezone.now(), ends_at=timezone.now()+timedelta(hours=1), registration_deadline=timezone.now())

    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        token = self.client.get('/api/csrf/').data['csrf_token']
        self.client.credentials(HTTP_X_CSRFTOKEN=token)

    def tearDown(self):
        cache.clear()

    def test_guest_can_submit_to_work_and_event_and_waits_for_approval(self):
        for resource, target in [('collections', self.work), ('events', self.event)]:
            url = f'/api/{resource}/{target.pk}/comments/'
            response = self.client.post(url, {'guest_name': '路过的同学', 'text': '很喜欢光线', 'approved': True}, format='json')
            self.assertEqual(response.status_code, 201, response.data)
            comment = Comment.objects.get(pk=response.data['id'])
            self.assertIsNone(comment.author_id)
            self.assertFalse(comment.approved)
            self.assertEqual(response.data['author_name'], '路过的同学')
            self.assertEqual(self.client.get(url).data['count'], 0)
            comment.approved = True
            comment.save()
            self.assertEqual(self.client.get(url).data['count'], 1)

    def test_optional_nickname_and_input_limits(self):
        url = f'/api/collections/{self.work.pk}/comments/'
        for payload in [{'text': '  '}, {'text': 'x'*2001}, {'text': '正常', 'guest_name': 'x'*41}]:
            self.assertEqual(self.client.post(url, payload, format='json').status_code, 400)
        response = self.client.post(url, {'text': '匿名观察'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['author_name'], '访客')

    def test_private_targets_and_upload_are_not_opened(self):
        self.work.visibility = Visibility.MEMBERS
        self.work.save()
        url = f'/api/collections/{self.work.pk}/comments/'
        self.assertEqual(self.client.post(url, {'text': '尝试留言'}, format='json').status_code, 404)
        self.assertEqual(self.client.post('/api/upload/', {}, format='json').status_code, 403)
        self.work.visibility = Visibility.PUBLIC
        self.work.status = Status.DRAFT
        self.work.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_rate_limit_is_shared_between_targets_but_does_not_limit_reading(self):
        url = f'/api/collections/{self.work.pk}/comments/'
        for _ in range(6):
            self.assertEqual(self.client.post(url, {'text': '留言'}, format='json').status_code, 201)
        self.assertEqual(self.client.post(f'/api/events/{self.event.pk}/comments/', {'text': '留言'}, format='json').status_code, 429)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(Comment.objects.count(), 6)

    def test_existing_member_attribution_is_preserved(self):
        comment = Comment.objects.create(author=self.owner, collection=self.work, text='历史留言', approved=True)
        data = self.client.get(f'/api/collections/{self.work.pk}/comments/').data['results']
        self.assertEqual(data[0]['author_name'], '原作者')
        self.assertEqual(str(data[0]['id']), str(comment.pk))
