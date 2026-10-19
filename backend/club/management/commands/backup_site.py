import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from club import storage


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


class Command(BaseCommand):
    help = 'Create a verifiable database + private media backup without deleting old backups.'

    def add_arguments(self, parser):
        parser.add_argument('--output', required=True)
        parser.add_argument('--pg-dump-bin', default='pg_dump')

    def handle(self, *args, **options):
        parent = Path(options['output']).resolve()
        if parent.is_relative_to(settings.STORAGE_ROOT.resolve()):
            raise CommandError('备份目录不能位于文件存储目录内部。')
        target = parent / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        target.mkdir(parents=True, exist_ok=False)
        if connection.vendor == 'sqlite':
            db_path = target / 'database.sqlite3'
            with (
                sqlite3.connect(settings.DATABASES['default']['NAME']) as source,
                sqlite3.connect(db_path) as backup,
            ):
                source.backup(backup)
        else:
            config = settings.DATABASES['default']
            db_path = target / 'database.dump'
            env = {**os.environ, 'PGPASSWORD': config['PASSWORD']}
            subprocess.run(
                [
                    options['pg_dump_bin'],
                    '--format=custom',
                    '--no-owner',
                    '--host',
                    config['HOST'],
                    '--port',
                    str(config['PORT']),
                    '--username',
                    config['USER'],
                    '--file',
                    str(db_path),
                    config['NAME'],
                ],
                env=env,
                check=True,
            )
            with db_path.open('rb') as dump:
                if dump.read(5) != b'PGDMP':
                    raise CommandError('数据库备份格式无效；本次备份不完整。')
        media = target / 'media'
        media.mkdir()
        if settings.S3_BUCKET:
            s3 = storage.client()
            for page in s3.get_paginator('list_objects_v2').paginate(Bucket=settings.S3_BUCKET):
                for item in page.get('Contents', []):
                    key = item['Key']
                    path = (media / key).resolve()
                    if not path.is_relative_to(media.resolve()):
                        raise CommandError('对象键不安全。')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    s3.download_file(settings.S3_BUCKET, key, str(path))
        elif settings.STORAGE_ROOT.exists():
            shutil.copytree(settings.STORAGE_ROOT, media, dirs_exist_ok=True)
        manifest = {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'database_engine': connection.vendor,
            'files': {
                str(path.relative_to(target)).replace('\\', '/'): checksum(path)
                for path in target.rglob('*')
                if path.is_file()
            },
        }
        (target / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        self.stdout.write(
            self.style.SUCCESS(f'备份完成：{target}；{len(manifest["files"])} 个文件。')
        )
