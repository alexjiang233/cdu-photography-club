"""Verify a backup manifest and SQLite integrity without changing source data."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()
root = args.directory.resolve()
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
for name, expected in manifest['files'].items():
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise SystemExit('Unsafe path in manifest')
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise SystemExit(f'Checksum mismatch: {name}')
if manifest['database_engine'] == 'sqlite':
    with sqlite3.connect(f'file:{(root / "database.sqlite3").as_posix()}?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise SystemExit('SQLite integrity check failed')
        print(
            'Database tables:',
            db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0],
        )
print(f'Verified {len(manifest["files"])} files. Restore instructions: docs/OPERATIONS.md')
