"""Manage this repository's Pages site using Git's existing credential helper.

Credentials remain in process memory and are never printed or saved.
"""
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['status', 'enable', 'build'])
args = parser.parse_args()
repository = 'alexjiang233/cdu-photography-club'
env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'Never'}
result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, env=env)
if result.returncode:
    raise SystemExit('Git credential helper unavailable.')
credential = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
token = credential.get('password')
if not token:
    raise SystemExit('Git credential helper returned no credential.')

def request(method, suffix, payload=None):
    req = urllib.request.Request('https://api.github.com/repos/' + repository + suffix,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'Photography-Association-Pages', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read() or '{}')
    except urllib.error.HTTPError as error:
        body = json.loads(error.read() or '{}')
        return error.code, {'message': body.get('message', 'GitHub request failed')}

if args.action == 'enable':
    status, data = request('GET', '/pages')
    method = 'PUT' if status == 200 else 'POST'
    if status not in [200, 404]:
        print(json.dumps({'http': status, **data})); raise SystemExit(1)
    status, data = request(method, '/pages', {'build_type': 'legacy', 'source': {'branch': 'gh-pages', 'path': '/'}})
elif args.action == 'build':
    status, data = request('POST', '/pages/builds', {})
else:
    status, data = request('GET', '/pages')
    if status == 200:
        build_status, build = request('GET', '/pages/builds/latest')
        data = {key: data.get(key) for key in ['html_url', 'status', 'build_type', 'source', 'https_enforced']}
        data['latest_build'] = {key: build.get(key) for key in ['status', 'commit', 'error', 'updated_at']} if build_status == 200 else build
print(json.dumps({'http': status, **data}, ensure_ascii=False))
if status >= 400: raise SystemExit(1)
