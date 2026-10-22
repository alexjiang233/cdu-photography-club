from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from rest_framework.exceptions import PermissionDenied

from club.models import Asset, AuditLog, Collection, Comment, Photo, Profile, Status
from club.services import delete_collections


@override_settings(DEBUG=True)
class CollectionDeleteTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('delete-admin', password='test-only-password')
        self.profile = Profile.objects.create(user=self.admin, display_name='作者')
        self.work = Collection.objects.create(
            owner=self.admin, author=self.profile, title='待删除作品', status=Status.PUBLISHED
        )
        self.other = Collection.objects.create(
            owner=self.admin, author=self.profile, title='保留作品'
        )
        self.asset = Asset.objects.create(
            owner=self.admin, original_name='photo.jpg', original_key='originals/photo.jpg',
            content_type='image/jpeg', size=100, checksum='a' * 64,
        )
        Photo.objects.create(collection=self.work, asset=self.asset, caption='照片')
        Comment.objects.create(collection=self.work, text='关联留言')
        self.client.force_login(self.admin)
        self.url = '/admin/club/collection/'

    def test_bulk_action_requires_confirmation_then_deletes_only_selected_series(self):
        payload = {'action': 'delete_selected', '_selected_action': [str(self.work.pk)]}
        response = self.client.get(self.url)
        self.assertContains(response, '删除所选作品系列')
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="post"')
        self.assertTrue(Collection.objects.filter(pk=self.work.pk).exists())
        response = self.client.post(self.url, {**payload, 'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Collection.objects.filter(pk=self.work.pk).exists())
        self.assertTrue(Collection.objects.filter(pk=self.other.pk).exists())
        self.assertFalse(Photo.objects.filter(collection_id=self.work.pk).exists())
        self.assertFalse(Comment.objects.filter(collection_id=self.work.pk).exists())
        self.assertTrue(Asset.objects.filter(pk=self.asset.pk).exists())
        self.assertTrue(Profile.objects.filter(pk=self.profile.pk).exists())
        self.assertTrue(AuditLog.objects.filter(
            action='delete_collection', target_id=str(self.work.pk), detail='待删除作品'
        ).exists())

    def test_single_delete_uses_same_service(self):
        url = f'{self.url}{self.work.pk}/delete/'
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Collection.objects.filter(pk=self.work.pk).exists())
        self.assertEqual(self.client.post(url, {'post': 'yes'}).status_code, 302)
        self.assertFalse(Collection.objects.filter(pk=self.work.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action='delete_collection').exists())

    def test_staff_without_delete_permission_cannot_delete(self):
        staff = User.objects.create_user('editor-only', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='change_collection'))
        self.client.force_login(staff)
        self.assertNotContains(self.client.get(self.url), 'value="delete_selected"')
        self.assertEqual(self.client.post(
            f'{self.url}{self.work.pk}/delete/', {'post': 'yes'}
        ).status_code, 403)
        with self.assertRaises(PermissionDenied):
            delete_collections(staff, Collection.objects.filter(pk=self.work.pk))
        self.assertTrue(Collection.objects.filter(pk=self.work.pk).exists())
