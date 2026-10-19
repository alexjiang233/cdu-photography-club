import io
import tempfile
from pathlib import Path
from PIL import Image
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django_otp.oath import totp
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient
from club.models import Asset, Collection, Document, Profile, Status


class AdminAndSecurityTest(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.override = override_settings(STORAGE_ROOT=Path(self.temp.name), DEBUG=True)
        self.override.enable()
        self.user = User.objects.create_superuser(
            'test-admin', 'admin@example.test', 'Test-only-strong-password!'
        )
        self.profile = Profile.objects.create(user=self.user, display_name='管理员', is_member=True)
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def tearDown(self):
        self.override.disable()
        self.temp.cleanup()

    def test_admin_upload_uses_same_validation_pipeline(self):
        self.client.force_login(self.user)
        output = io.BytesIO()
        Image.new('RGB', (40, 30), 'blue').save(output, 'JPEG')
        response = self.client.post(
            '/admin/club/asset/add/',
            {
                'upload': SimpleUploadedFile(
                    'admin.jpg', output.getvalue(), content_type='image/jpeg'
                ),
                '_save': '保存',
            },
        )
        self.assertEqual(response.status_code, 302)
        asset = Asset.objects.get()
        self.assertEqual(asset.state, Asset.State.READY)
        self.assertEqual(asset.owner, self.user)
        self.assertTrue(asset.display_key)

    @override_settings(DEBUG=False)
    def test_staff_api_requires_totp_and_rejects_replay(self):
        client = APIClient()
        payload = {'username': self.user.username, 'password': 'Test-only-strong-password!'}
        self.assertEqual(
            client.post('/api/auth/login/', payload, format='json', secure=True).status_code, 400
        )
        device = TOTPDevice.objects.create(user=self.user, confirmed=True)
        token = str(totp(device.bin_key)).zfill(device.digits)
        response = client.post(
            '/api/auth/login/', {**payload, 'otp': token}, format='json', secure=True
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn('otp_device_id', client.session)
        self.assertEqual(client.get('/api/dashboard/', secure=True).status_code, 200)
        replay = APIClient().post(
            '/api/auth/login/', {**payload, 'otp': token}, format='json', secure=True
        )
        self.assertEqual(replay.status_code, 400)

    @override_settings(DEBUG=False)
    def test_existing_staff_session_without_otp_cannot_use_api(self):
        client = APIClient()
        client.force_login(self.user)
        self.assertEqual(client.get('/api/dashboard/', secure=True).status_code, 403)

    def test_invalid_ids_return_client_errors(self):
        self.assertEqual(self.api.get('/api/collections/not-a-uuid/').status_code, 404)
        self.assertEqual(self.api.get('/api/collections/?author=not-a-uuid').status_code, 400)
        collection = Collection.objects.create(owner=self.user, author=self.profile, title='草稿')
        self.assertEqual(
            self.api.post(
                f'/api/collections/{collection.pk}/photos/',
                {'asset_id': 'invalid', 'caption': 'test'},
                format='json',
            ).status_code,
            400,
        )

    def test_api_cannot_set_own_membership_or_staff_role(self):
        self.user.is_staff = False
        self.user.is_superuser = False
        self.user.save()
        self.profile.is_member = False
        self.profile.save()
        response = self.api.patch(
            '/api/auth/account/',
            {'display_name': '正常署名', 'is_member': True, 'is_staff': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.profile.is_member)

    def test_document_versions_and_public_download(self):
        document = Document.objects.create(
            owner=self.user, title='版本文档', year=2026, category='tutorial'
        )
        for i in range(2):
            response = self.api.post(
                '/api/upload/',
                {'file': SimpleUploadedFile(f'version-{i}.txt', f'version {i}'.encode())},
                format='multipart',
            )
            self.assertEqual(response.status_code, 201, response.data)
            version = self.api.post(
                f'/api/documents/{document.pk}/versions/',
                {'asset_id': response.data['id'], 'note': f'第 {i + 1} 版'},
                format='json',
            )
            self.assertEqual(version.status_code, 201, version.data)
        self.assertEqual(list(document.versions.values_list('version', flat=True)), [2, 1])
        self.assertEqual(
            self.api.post(
                f'/api/documents/{document.pk}/workflow/', {'action': 'submit'}, format='json'
            ).status_code,
            200,
        )
        self.assertEqual(
            self.api.post(
                f'/api/documents/{document.pk}/workflow/', {'action': 'publish'}, format='json'
            ).status_code,
            200,
        )
        self.api.force_authenticate(None)
        data = self.api.get(f'/api/documents/{document.pk}/').data
        self.assertEqual(len(data['versions']), 2)
        response = self.api.get(data['versions'][0]['download_url'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'version 1')

    def test_publish_state_cannot_be_set_on_creation(self):
        response = self.api.post(
            '/api/collections/',
            {'title': '越过审核尝试', 'status': 'published', 'featured': True},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        obj = Collection.objects.get(pk=response.data['id'])
        self.assertEqual(obj.status, Status.DRAFT)
        self.assertFalse(obj.featured)
