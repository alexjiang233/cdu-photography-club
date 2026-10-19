"""Check every local asset and navigation target in the static export."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[1] / '.pages-build/frontend/out'
base = '/cdu-photography-club'
failures = []
class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ['src', 'href', 'action'] or not value:
                continue
            url = urlsplit(value)
            if url.scheme or url.netloc or value.startswith('#'):
                continue
            if not url.path.startswith(base + '/') and url.path != base:
                failures.append((str(page.relative_to(root)), value, 'outside project path'))
                continue
            target = root / unquote(url.path[len(base):]).lstrip('/')
            if not target.is_file() and not (target / 'index.html').is_file():
                failures.append((str(page.relative_to(root)), value, 'missing file'))

pages = list(root.rglob('*.html'))
assert pages
for page in pages:
    Links().feed(page.read_text(encoding='utf-8'))
assert (root / '.nojekyll').exists()
assert not failures, failures
print(f'Passed: {len(pages)} HTML pages, all local links, images, forms and bundles resolve.')
