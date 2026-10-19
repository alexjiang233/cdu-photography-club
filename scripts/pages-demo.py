"""Generate Pages fixtures from an isolated, in-memory demo database only."""
import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DEBUG'] = '1'
import django
from django.conf import settings

settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
settings.STORAGE_ROOT = root / '.pages-build' / 'storage'
settings.S3_BUCKET = ''
django.setup()
from django.core.management import call_command
from django.test import Client

call_command('migrate', verbosity=0)
call_command('seed_demo', verbosity=0)
client = Client()
def get(path):
    response = client.get('/api/' + path)
    assert response.status_code == 200, (path, response.status_code)
    return response.json()

data = {'site': get('site/'), 'members': get('members/')}
data['site']['name'] = '摄影协会'
for resource in ['collections', 'events', 'documents']:
    data[resource] = get(resource + '/')['results']
    assert all(row['is_demo'] for row in data[resource])
media = root / '.pages-build' / 'public' / 'preview-media'
media.mkdir(parents=True, exist_ok=True)
urls = {}
def localize(value):
    if isinstance(value, dict):
        return {k: localize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [localize(v) for v in value]
    if isinstance(value, str) and '/api/assets/' in value:
        if value not in urls:
            from urllib.parse import urlsplit
            import hashlib
            path = urlsplit(value).path
            response = client.get(path)
            assert response.status_code == 200, path
            extension = '.txt' if 'text/plain' in response['Content-Type'] else '.jpg'
            name = hashlib.sha256(path.encode()).hexdigest()[:20] + extension
            content = b''.join(response.streaming_content) if response.streaming else response.content
            (media / name).write_bytes(content)
            urls[value] = '/preview-media/' + name
        return urls[value]
    return value

data = localize(data)
target = root / 'deploy' / 'pages' / 'demo.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('Exported demo-only fixture and media.')
