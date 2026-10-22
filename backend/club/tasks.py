import io
import warnings
from celery import Task, shared_task
from PIL import Image, ImageOps
from .models import Asset
from . import storage
from .photo_metadata import technical_metadata

Image.MAX_IMAGE_PIXELS = 40_000_000


class ImageTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        Asset.objects.filter(pk=args[0]).update(
            state=Asset.State.REJECTED, error='图片处理暂不可用，请联系管理员重试。'
        )


@shared_task(base=ImageTask, autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def process_image(asset_id):
    asset = Asset.objects.get(pk=asset_id)
    data = storage.get(asset.original_key)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                asset.photo_metadata = technical_metadata(source)
                exif = source.getexif()
                # The raster below is orientation-normalized, so preserve the remaining
                # camera metadata while recording the normalized orientation.
                if 274 in exif:
                    exif[274] = 1
                exif_bytes = exif.tobytes() if exif else source.info.get('exif', b'')
                image = ImageOps.exif_transpose(source).convert('RGB')
                asset.width, asset.height = image.size
                for name, size in [('display', 2200), ('thumbnail', 700)]:
                    resized = image.copy()
                    resized.thumbnail((size, size))
                    output = io.BytesIO()
                    resized.save(output, format='WEBP', quality=86, exif=exif_bytes)
                    key = f'derived/{asset.pk}/{name}.webp'
                    storage.put(key, output.getvalue(), 'image/webp')
                    setattr(asset, f'{name}_key', key)
                asset.state = Asset.State.READY
                asset.error = ''
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        ValueError,
        SyntaxError,
        OSError,
    ):
        asset.state = Asset.State.REJECTED
        asset.error = '图片无法安全解码，请重新导出后上传。'
    asset.save()
    return asset.state
