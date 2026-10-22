import io
import tempfile
from datetime import timedelta
from pathlib import Path
from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from club.models import (
    Asset,
    Collection,
    Document,
    DocumentVersion,
    Event,
    Photo,
    Profile,
    Registration,
    Status,
    Visibility,
)
from club.services import register
from club import storage


class WorkflowsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('author', password='Test-password-234!')
        cls.other = User.objects.create_user('another', password='Test-password-234!')
        cls.editor = User.objects.create_user(
            'editor', password='Test-password-234!', is_staff=True
        )
        cls.profile = Profile.objects.create(
            user=cls.owner, display_name='作者', is_member=True, bio='私有简介', cohort='不公开届别'
        )
        Profile.objects.create(user=cls.other, display_name='另一位成员', is_member=True)
        cls.editor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label='club',
                codename__in=['change_collection', 'change_document', 'change_event'],
            )
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.override = override_settings(
            STORAGE_ROOT=Path(self.temp.name), CELERY_TASK_ALWAYS_EAGER=True, DEBUG=True
        )
        self.override.enable()
        self.client = APIClient()

    def tearDown(self):
        self.override.disable()
        self.temp.cleanup()

    def image(self, name='photo.jpg'):
        output = io.BytesIO()
        image = Image.new('RGB', (60, 40), 'green')
        exif = Image.Exif()
        exif[270] = 'private metadata'
        image.save(output, format='JPEG', exif=exif)
        return SimpleUploadedFile(name, output.getvalue(), content_type='image/jpeg')

    def upload(self, user=None):
        self.client.force_authenticate(user or self.owner)
        result = self.client.post('/api/upload/', {'file': self.image()}, format='multipart')
        self.assertEqual(result.status_code, 201, result.data)
        return Asset.objects.get(pk=result.data['id'])

    def collection(self, status=Status.DRAFT, visibility=Visibility.PUBLIC, asset=None):
        obj = Collection.objects.create(
            owner=self.owner,
            author=self.profile,
            title='待展示作品',
            status=status,
            visibility=visibility,
            review_note='内部审核信息',
        )
        if asset:
            Photo.objects.create(collection=obj, asset=asset, caption='照片说明')
        return obj

    def event(self, capacity=1):
        now = timezone.now()
        return Event.objects.create(
            owner=self.editor,
            title='正式活动',
            status=Status.PUBLISHED,
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            registration_deadline=now + timedelta(days=1),
            registration_open=True,
            capacity=capacity,
            location='活动地点',
        )

    def test_end_to_end_upload_submit_review_publish_and_withdraw(self):
        asset = self.upload()
        result = self.client.post(
            '/api/collections/', {'title': '新作品', 'description': '创作说明'}, format='json'
        )
        self.assertEqual(result.status_code, 201, result.data)
        pk = result.data['id']
        self.assertEqual(
            self.client.post(
                f'/api/collections/{pk}/photos/',
                {'asset_id': str(asset.pk), 'caption': '说明'},
                format='json',
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                f'/api/collections/{pk}/workflow/', {'action': 'submit'}, format='json'
            ).status_code,
            200,
        )
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/collections/{pk}/').status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.post(
                f'/api/collections/{pk}/workflow/', {'action': 'publish'}, format='json'
            ).status_code,
            403,
        )
        self.client.force_authenticate(self.editor)
        self.assertEqual(
            self.client.post(
                f'/api/collections/{pk}/workflow/', {'action': 'publish'}, format='json'
            ).status_code,
            200,
        )
        self.client.force_authenticate(None)
        detail = self.client.get(f'/api/collections/{pk}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['review_note'], '')
        image_response = self.client.get(f'/api/assets/{asset.pk}/display/')
        self.assertEqual(image_response.status_code, 200)
        self.assertTrue(b''.join(image_response.streaming_content))
        self.assertEqual(self.client.get(f'/api/assets/{asset.pk}/download/').status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.post(
                f'/api/collections/{pk}/workflow/', {'action': 'revise'}, format='json'
            ).status_code,
            200,
        )
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/assets/{asset.pk}/display/').status_code, 404)

    def test_derived_image_preserves_metadata(self):
        asset = self.upload()
        with Image.open(io.BytesIO(storage.get(asset.display_key))) as image:
            self.assertEqual(image.getexif().get(270), 'private metadata')
        self.assertEqual(asset.state, Asset.State.READY)

    def test_fake_extension_rejected(self):
        self.client.force_authenticate(self.owner)
        result = self.client.post(
            '/api/upload/',
            {'file': SimpleUploadedFile('evil.jpg', b'<script>alert(1)</script>')},
            format='multipart',
        )
        self.assertEqual(result.status_code, 400)

    def test_unlisted_file_type_rejected(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.post(
                '/api/upload/',
                {'file': SimpleUploadedFile('test.svg', b'<svg/>')},
                format='multipart',
            ).status_code,
            400,
        )

    def test_anonymous_cannot_upload(self):
        self.assertEqual(
            self.client.post(
                '/api/upload/', {'file': self.image()}, format='multipart'
            ).status_code,
            403,
        )

    def test_non_member_cannot_upload_or_create(self):
        self.profile.is_member = False
        self.profile.save()
        self.client.force_authenticate(User.objects.get(pk=self.owner.pk))
        self.assertEqual(
            self.client.post(
                '/api/collections/', {'title': '无成员权限'}, format='json'
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                '/api/upload/', {'file': self.image()}, format='multipart'
            ).status_code,
            403,
        )
        self.profile.is_member = True

    def test_cannot_attach_another_members_asset(self):
        asset = self.upload()
        self.client.force_authenticate(self.other)
        obj = Collection.objects.create(
            owner=self.other, author=self.other.profile, title='其他作品'
        )
        self.assertEqual(
            self.client.post(
                f'/api/collections/{obj.pk}/photos/',
                {'asset_id': str(asset.pk), 'caption': '非法引用'},
                format='json',
            ).status_code,
            404,
        )

    def test_cannot_modify_another_members_work(self):
        obj = self.collection(status=Status.PUBLISHED)
        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.patch(
                f'/api/collections/{obj.pk}/', {'title': '篡改'}, format='json'
            ).status_code,
            400,
        )
        obj.status = Status.DRAFT
        obj.save()
        self.assertEqual(
            self.client.patch(
                f'/api/collections/{obj.pk}/', {'title': '篡改'}, format='json'
            ).status_code,
            404,
        )

    def test_published_work_is_locked(self):
        obj = self.collection(status=Status.PUBLISHED)
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.patch(
                f'/api/collections/{obj.pk}/', {'title': '未撤回修改'}, format='json'
            ).status_code,
            400,
        )

    def test_empty_collection_cannot_submit(self):
        obj = self.collection()
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.post(
                f'/api/collections/{obj.pk}/workflow/', {'action': 'submit'}, format='json'
            ).status_code,
            400,
        )

    def test_member_document_not_exposed_to_public_search_or_download(self):
        self.client.force_authenticate(self.owner)
        result = self.client.post(
            '/api/upload/',
            {'file': SimpleUploadedFile('guide.txt', '内部资料'.encode())},
            format='multipart',
        )
        asset = Asset.objects.get(pk=result.data['id'])
        doc = Document.objects.create(
            owner=self.owner,
            title='内部交接记录',
            year=2026,
            category='handover',
            status=Status.PUBLISHED,
            visibility=Visibility.MEMBERS,
        )
        DocumentVersion.objects.create(document=doc, asset=asset, version=1)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/documents/?q=内部').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/documents/{doc.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/assets/{asset.pk}/download/').status_code, 404)
        self.client.force_authenticate(self.other)
        response = self.client.get(f'/api/assets/{asset.pk}/download/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertTrue(b''.join(response.streaming_content))

    def test_registration_capacity_duplicate_cancel_and_rejoin(self):
        event = self.event()
        self.client.force_authenticate(self.owner)
        url = f'/api/events/{event.pk}/register/'
        self.assertEqual(
            self.client.post(url, {'contact': 'test contact'}, format='json').status_code, 201
        )
        self.assertEqual(
            self.client.post(url, {'contact': 'test contact'}, format='json').status_code, 400
        )
        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.post(url, {'contact': 'other contact'}, format='json').status_code, 400
        )
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.post(
                f'/api/events/{event.pk}/cancel-registration/', {}, format='json'
            ).status_code,
            200,
        )
        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.post(url, {'contact': 'other contact'}, format='json').status_code, 201
        )
        self.assertEqual(Registration.objects.filter(event=event, cancelled=False).count(), 1)

    def test_closed_event_and_demo_event_refuse_registration(self):
        event = self.event()
        self.client.force_authenticate(self.owner)
        event.registration_open = False
        event.save()
        self.assertEqual(
            self.client.post(
                f'/api/events/{event.pk}/register/', {'contact': 'contact'}, format='json'
            ).status_code,
            400,
        )
        event.registration_open = True
        event.is_demo = True
        event.save()
        self.assertEqual(
            self.client.post(
                f'/api/events/{event.pk}/register/', {'contact': 'contact'}, format='json'
            ).status_code,
            400,
        )

    def test_participant_contacts_are_private(self):
        event = self.event()
        register(self.owner, event.pk, 'private contact')
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/events/{event.pk}/registrations/').status_code, 403)
        self.assertNotIn('private contact', str(self.client.get(f'/api/events/{event.pk}/').data))
        self.client.force_authenticate(self.editor)
        response = self.client.get(f'/api/events/{event.pk}/registrations/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['contact'], 'private contact')

    def test_comment_waits_for_moderation(self):
        obj = self.collection(status=Status.PUBLISHED)
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.post(
                f'/api/collections/{obj.pk}/comments/', {'text': '讨论内容'}, format='json'
            ).status_code,
            201,
        )
        self.assertEqual(self.client.get(f'/api/collections/{obj.pk}/comments/').data['count'], 1)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/collections/{obj.pk}/comments/').data['count'], 0)

    def test_member_login_is_disabled_and_csrf_is_required(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(
            client.post(
                '/api/auth/login/',
                {'username': 'author', 'password': 'Test-password-234!'},
                format='json',
            ).status_code,
            403,
        )
        response = client.get('/api/auth/session/')
        token = response.data['csrf_token']
        response = client.post(
            '/api/auth/login/',
            {'username': 'author', 'password': 'Test-password-234!'},
            format='json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertNotIn('_auth_user_id', client.session)

    def test_private_author_profile_is_not_exposed(self):
        obj = self.collection(status=Status.PUBLISHED)
        response = self.client.get(f'/api/collections/{obj.pk}/')
        self.assertEqual(response.data['author']['bio'], '')
        self.assertEqual(response.data['author']['cohort'], '')
        self.assertEqual(self.client.get(f'/api/members/{self.profile.pk}/').status_code, 404)

    @override_settings(DEBUG=False, DOCUMENT_SCANNER='')
    def test_production_document_upload_requires_scanner(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            '/api/upload/',
            {'file': SimpleUploadedFile('file.pdf', b'%PDF-1.7\n...')},
            format='multipart',
            secure=True,
        )
        self.assertEqual(response.status_code, 400)

    def test_object_keys_never_exposed(self):
        asset = self.upload()
        obj = self.collection(status=Status.PUBLISHED, asset=asset)
        self.client.force_authenticate(None)
        data = self.client.get(f'/api/collections/{obj.pk}/').data
        self.assertNotIn('originals/', str(data))
        self.assertNotIn(asset.checksum, str(data))

    def test_uploaded_image_recovery_is_owner_only(self):
        asset = self.upload()
        result = self.client.get('/api/upload/')
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(str(result.data['results'][0]['id']), str(asset.pk))
        obj = self.collection(asset=asset)
        self.assertEqual(self.client.get(f'/api/upload/?collection={obj.pk}').data['count'], 0)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/upload/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/upload/?collection={obj.pk}').status_code, 404)
