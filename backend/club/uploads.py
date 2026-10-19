import hashlib
import io
import subprocess
import tempfile
import warnings
import uuid
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from . import storage
from .models import Asset
from .tasks import process_image

MAX_SIZE = 25 * 1024 * 1024


@transaction.atomic
def ingest(user, uploaded):
    # Serialize quota reservations for one account across concurrent uploads.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    if uploaded.size > MAX_SIZE:
        raise ValidationError('单个文件不得超过 25 MB。RAW 大文件入口暂未开放。')
    total = Asset.objects.filter(owner=user).aggregate(total=Sum('size'))['total'] or 0
    if total + uploaded.size > 1024 * 1024 * 1024:
        raise ValidationError('个人存储额度已用完，请联系管理员。')
    data = uploaded.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE or not data:
        raise ValidationError('文件为空或超过大小限制。')
    suffix = Path(uploaded.name).suffix.lower()
    images = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}
    if suffix in images:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as image:
                    if image.format != images[suffix]:
                        raise ValidationError('扩展名与实际图片类型不一致。')
                    if image.width * image.height > 40_000_000:
                        raise ValidationError('图片像素过大，请导出为 4000 万像素以内。')
                    image.verify()
        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            raise ValidationError('图片损坏或无法安全读取。')
        content_type = Image.MIME[images[suffix]]
    elif suffix in ['.pdf', '.txt']:
        if suffix == '.pdf' and not data.startswith(b'%PDF-'):
            raise ValidationError('不是有效的 PDF 文件。')
        if suffix == '.txt':
            try:
                data.decode('utf-8')
            except UnicodeDecodeError:
                raise ValidationError('文本文件请使用 UTF-8 编码。')
        if not settings.DEBUG and not settings.DOCUMENT_SCANNER:
            raise ValidationError('资料文件安全扫描尚未配置，请联系管理员。')
        if settings.DOCUMENT_SCANNER:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(data)
                scan_path = Path(tmp.name)
            try:
                result = subprocess.run(
                    [settings.DOCUMENT_SCANNER, '--no-summary', str(scan_path)],
                    timeout=45,
                    capture_output=True,
                    check=False,
                )
                if result.returncode != 0:
                    raise ValidationError('文件安全检查未通过。')
            except (OSError, subprocess.TimeoutExpired):
                raise ValidationError('安全扫描暂不可用，请稍后重试。')
            finally:
                scan_path.unlink(missing_ok=True)
        content_type = 'application/pdf' if suffix == '.pdf' else 'text/plain'
    else:
        raise ValidationError('支持 JPEG、PNG、WebP、PDF 和 UTF-8 文本文件。')
    key = f'originals/{uuid.uuid4().hex}{suffix}'
    storage.put(key, data, content_type)
    asset = Asset.objects.create(
        owner=user,
        original_name=Path(uploaded.name).name[:240],
        original_key=key,
        content_type=content_type,
        size=len(data),
        checksum=hashlib.sha256(data).hexdigest(),
        state=Asset.State.PROCESSING if suffix in images else Asset.State.READY,
    )
    if suffix in images:
        if settings.CELERY_TASK_ALWAYS_EAGER:
            process_image.delay(str(asset.pk))
            asset.refresh_from_db()
        else:
            transaction.on_commit(lambda: process_image.delay(str(asset.pk)))
    return asset
