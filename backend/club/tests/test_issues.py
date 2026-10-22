from pathlib import Path
import tempfile
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as ModelValidationError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from club.models import Asset, Issue, IssueBlock, Status
from club.services import transition


class IssueTest(TestCase):
    def setUp(self):
        self.editor = User.objects.create_superuser('issue-editor', password='test-only-password')
        self.asset = Asset.objects.create(owner=self.editor, original_name='night.jpg', original_key='original.jpg', display_key='display.webp', thumbnail_key='thumb.webp', content_type='image/jpeg', size=30, checksum='a'*64, state='ready', width=600, height=400)
        self.issue = Issue.objects.create(owner=self.editor, number=1, title='夜色', cover=self.asset)
        self.block = IssueBlock.objects.create(issue=self.issue, image=self.asset, heading='夜色', position=0)
        self.api = APIClient()

    def publish(self):
        transition(self.editor, self.issue, 'submit')
        transition(self.editor, self.issue, 'publish')

    def test_drafts_and_previews_are_private(self):
        url = f'/api/issues/{self.issue.pk}/?preview=1'
        self.assertEqual(self.api.get('/api/issues/').data['count'], 0)
        self.assertEqual(self.api.get(url).status_code, 404)
        ordinary = User.objects.create_user('ordinary')
        self.api.force_authenticate(ordinary)
        self.assertEqual(self.api.get(url).status_code, 404)
        self.api.force_authenticate(self.editor)
        self.assertEqual(self.api.get(url).status_code, 200)
        self.assertEqual(self.api.get('/api/issues/').data['count'], 0)

    def test_publish_order_readonly_and_withdraw(self):
        IssueBlock.objects.create(issue=self.issue, layout='text', text='说明', position=4)
        self.publish()
        result = self.api.get('/api/issues/').data['results'][0]
        self.assertEqual([b['position'] for b in result['blocks']], [0, 4])
        self.assertNotIn('owner', result)
        self.assertEqual(self.api.post('/api/issues/', {}).status_code, 405)
        transition(self.editor, self.issue, 'archive')
        self.assertEqual(self.api.get('/api/issues/').data['count'], 0)
        self.assertEqual(self.api.get(f'/api/issues/{self.issue.pk}/').status_code, 404)

    def test_private_issue_is_not_public_after_publish(self):
        self.issue.visibility = 'private'
        self.issue.save()
        self.publish()
        self.assertEqual(self.api.get('/api/issues/').data['count'], 0)

    def test_invalid_and_empty_content_cannot_publish(self):
        self.block.image = None
        with self.assertRaises(ModelValidationError):
            self.block.full_clean()
        self.block.delete()
        with self.assertRaises(ValidationError):
            transition(self.editor, self.issue, 'submit')
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, Status.DRAFT)

    def test_images_follow_issue_visibility(self):
        with tempfile.TemporaryDirectory() as tmp, override_settings(STORAGE_ROOT=Path(tmp)):
            Path(tmp, 'display.webp').write_bytes(b'test-image')
            url = f'/api/assets/{self.asset.pk}/display/'
            self.assertEqual(self.api.get(url).status_code, 404)
            self.publish()
            response = self.api.get(url)
            self.assertEqual(response.status_code, 200)
            response.close()
            transition(self.editor, self.issue, 'archive')
            self.assertEqual(self.api.get(url).status_code, 404)

    def test_admin_has_preview_and_content_form(self):
        self.client.force_login(self.editor)
        response = self.client.get(f'/admin/club/issue/{self.issue.pk}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'/field-journal/issues/{self.issue.pk}?preview=1')
        self.assertContains(response, '并列照片')
