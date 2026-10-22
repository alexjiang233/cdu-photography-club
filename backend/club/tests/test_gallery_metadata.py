import io
import tempfile
from datetime import timedelta
from pathlib import Path
from PIL import Image, TiffImagePlugin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from club.models import Asset, Collection, Event, Photo, Profile
from club.photo_metadata import technical_metadata
from club.serializers import PhotoSerializer


class GalleryMetadataTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('gallery-editor', password='test-password-only')
        self.profile = Profile.objects.create(display_name='协会',user=self.user)
        self.asset = Asset.objects.create(owner=self.user,original_name='photo.jpg',original_key='original.jpg',display_key='display.webp',content_type='image/jpeg',size=10,checksum='a'*64,state='ready',photo_metadata={'camera_body':'Camera','taken_at':'2024-06-04 04:43:03','iso':'800','serial':'private'})
        self.collection = Collection.objects.create(title='相册',owner=self.user,author=self.profile,status='published',visibility='public')
        self.photo = Photo.objects.create(collection=self.collection,asset=self.asset,caption='照片',photographer='署名',iso='400')
        self.api = APIClient()

    def test_exif_allowlist_and_values(self):
        output=io.BytesIO()
        exif=Image.Exif()
        exif[271]='SONY'; exif[272]='ILCE-7RM3'; exif[315]='private owner'
        exif[34665]={36867:'2024:06:04 04:43:03',33434:TiffImagePlugin.IFDRational(1,125),33437:TiffImagePlugin.IFDRational(35,10),34855:800,42036:'E 28-200mm',42033:'private serial'}
        Image.new('RGB',(30,20),'blue').save(output,'JPEG',exif=exif)
        with Image.open(io.BytesIO(output.getvalue())) as image:
            result=technical_metadata(image)
        self.assertEqual(result['camera_body'],'SONY ILCE-7RM3')
        self.assertEqual(result['shutter_speed'],'1/125 s')
        self.assertEqual(result['aperture'],'f/3.5')
        self.assertEqual(result['iso'],'800')
        self.assertEqual(result['taken_at'],'2024-06-04 04:43:03')
        self.assertNotIn('private',str(result))

    def test_manual_overrides_and_private_exif_not_serialized(self):
        result=PhotoSerializer(self.photo).data['shooting']
        self.assertEqual(result['iso'],'400')
        self.assertEqual(result['photographer'],'署名')
        self.assertEqual(result['time_source'],'exif')
        self.assertNotIn('serial',result)
        self.photo.taken_at='2024-06-04 12:43'
        self.assertEqual(PhotoSerializer(self.photo).data['shooting']['time_source'],'manual')

    def test_missing_exif_is_not_invented(self):
        self.asset.photo_metadata={}
        self.photo.iso=''
        self.photo.photographer=''
        result=PhotoSerializer(self.photo).data['shooting']
        self.assertNotIn('taken_at',result)
        self.assertNotIn('camera_body',result)
        self.assertEqual(result['photographer'],'')

    def test_placeholder_filter_preserves_old_site(self):
        self.collection.is_placeholder=True
        self.collection.save()
        self.assertEqual(self.api.get('/api/collections/').data['count'],1)
        self.assertEqual(self.api.get('/api/collections/?placeholder=0').data['count'],0)

    def test_event_photos_visibility_and_exclusive_parent(self):
        start=timezone.now()+timedelta(days=1)
        event=Event.objects.create(owner=self.user,title='外拍',starts_at=start,ends_at=start+timedelta(hours=2),registration_deadline=start-timedelta(hours=1),location='现场')
        photo=Photo(event=event,asset=self.asset,caption='活动照片')
        photo.full_clean(); photo.save()
        photo.collection=self.collection
        with self.assertRaises(ValidationError): photo.full_clean()
        self.photo.delete()
        with tempfile.TemporaryDirectory() as tmp, override_settings(STORAGE_ROOT=Path(tmp)):
            Path(tmp,'display.webp').write_bytes(b'photo')
            url=f'/api/assets/{self.asset.pk}/display/'
            self.assertEqual(self.api.get(url).status_code,404)
            event.status='published'; event.save()
            response=self.api.get(url)
            self.assertEqual(response.status_code,200); response.close()
            result=self.api.get(f'/api/events/{event.pk}/').data
            self.assertEqual(len(result['photos']),1)

    def test_admin_event_photos_form(self):
        self.client.force_login(self.user)
        response=self.client.get('/admin/club/event/add/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'拍摄参数')

    def test_photo_edit_api_keeps_manual_credit(self):
        self.api.force_authenticate(self.user)
        self.collection.status='draft'; self.collection.save()
        response=self.api.post(f'/api/collections/{self.collection.pk}/update-photo/', {'photo_id':str(self.photo.pk),'caption':'照片','photographer':'摄影署名','camera_body':'手动机身','iso':'200'},format='json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data['shooting']['photographer'],'摄影署名')
        self.assertEqual(response.data['shooting']['camera_body'],'手动机身')
        self.assertEqual(response.data['shooting']['iso'],'200')
