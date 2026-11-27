"""End-to-end smoke test for Verilabel AI.

Start the server first (python manage.py runserver). If you use a Celery worker,
start it too (CELERY_EAGER=False). Then run, from the project folder:

    python scripts/e2e_test.py
    python scripts/e2e_test.py --image C:\\path\\to\\label.jpg
    python scripts/e2e_test.py --base http://127.0.0.1:8000

It signs up a new test customer, uploads a photo, waits for the result and checks
the answers against contracts/API_CONTRACT.md. It needs only the packages that
Django already installed (Pillow is used to make a test photo).
"""
import argparse
import io
import json
import random
import sys
import time
import urllib.error
import urllib.request
import uuid

results = []


def record(name, ok, detail=''):
    results.append((name, ok))
    print(('PASS  ' if ok else 'FAIL  ') + name + (f'  ({detail})' if detail else ''))


def skip(name, detail=''):
    print('SKIP  ' + name + (f'  ({detail})' if detail else ''))


def call(base, method, path, token=None, body=None, files=None):
    """Returns (status, headers, raw_bytes). Never raises for HTTP errors."""
    headers = {}
    data = None
    if token:
        headers['Authorization'] = 'Token ' + token
    if files:
        boundary = uuid.uuid4().hex
        parts = []
        for field, filename, content_type, content in files:
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; '
                f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode() + content + b'\r\n')
        data = b''.join(parts) + f'--{boundary}--\r\n'.encode()
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
    elif body is not None:
        data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()


def as_json(raw):
    try:
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return None


def make_test_photo():
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (800, 1000), 'white')
    draw = ImageDraw.Draw(image)
    draw.text((60, 60), 'VERILABEL TEST PHOTO', fill='black')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8000')
    parser.add_argument('--image', help='path of a real label photo (JPG or PNG)')
    parser.add_argument('--wait', type=int, default=120, help='seconds to wait for the result')
    args = parser.parse_args()
    base = args.base.rstrip('/')

    if args.image:
        with open(args.image, 'rb') as file:
            photo = file.read()
        photo_name = args.image.replace('\\', '/').split('/')[-1]
    else:
        photo, photo_name = make_test_photo(), 'e2e_test.jpg'
    content_type = 'image/png' if photo_name.lower().endswith('.png') else 'image/jpeg'

    user_id = 'e2e' + str(random.randint(100000, 999999))
    password = 'test12345'

    status, _, raw = call(base, 'POST', '/api/auth/signup/',
                          body={'name': 'E2E Tester', 'user_id': user_id, 'password': password})
    data = as_json(raw) or {}
    record('sign up a customer', status == 201 and data.get('role') == 'customer', f'status {status}')

    status, _, raw = call(base, 'POST', '/api/auth/signin/', body={'user_id': user_id, 'password': password})
    data = as_json(raw) or {}
    token = data.get('token')
    record('sign in returns a token', status == 200 and bool(token), f'status {status}')
    if not token:
        print('Cannot go on without a token.')
        sys.exit(1)

    status, _, raw = call(base, 'POST', '/api/auth/signin/', body={'user_id': user_id, 'password': 'wrong-password'})
    record('wrong password gives 401 and an error message',
           status == 401 and 'error' in (as_json(raw) or {}), f'status {status}')

    status, _, raw = call(base, 'GET', '/api/scans/')
    record('list without a token gives 401', status == 401, f'status {status}')

    status, _, raw = call(base, 'POST', '/api/scans/', token,
                          files=[('image', 'notes.txt', 'text/plain', b'not an image')])
    record('a .txt upload is rejected with 400', status == 400 and 'error' in (as_json(raw) or {}), f'status {status}')

    status, _, raw = call(base, 'POST', '/api/scans/', token, files=[('image', photo_name, content_type, photo)])
    data = as_json(raw) or {}
    scan_id = data.get('scan_id')
    record('upload a photo gives 201 and a scan_id', status == 201 and bool(scan_id), f'status {status}')
    if not scan_id:
        print('Cannot go on without a scan.')
        sys.exit(1)

    scan = {}
    deadline = time.time() + args.wait
    while time.time() < deadline:
        status, _, raw = call(base, 'GET', f'/api/scans/{scan_id}/', token)
        scan = as_json(raw) or {}
        if scan.get('status') in ('done', 'failed', 'low_quality'):
            break
        time.sleep(1)
    final = scan.get('status')
    record('the scan finishes (done or low_quality)', final in ('done', 'low_quality'), f'status "{final}"')

    result = scan.get('compliance_result') or {}
    if final == 'done':
        rules = result.get('rules') or []
        record('the result has rules, a score and a verdict',
               len(rules) > 0 and isinstance(result.get('score'), int) and result.get('verdict') in
               ('COMPLIANT', 'PARTIAL', 'NON_COMPLIANT'),
               f'score {result.get("score")}, verdict {result.get("verdict")}')
        failed = [f"{r['rule_id']} {r['name']}: {r['reason']}" for r in rules if r.get('status') == 'FAIL']
        print('      product:', scan.get('product_name') or '(none)')
        print('      failed rules:', failed if failed else 'none')
    elif final == 'low_quality':
        record('a low-quality scan has a warning and no score',
               bool(result.get('image_quality_warning')) and result.get('score') is None)
    else:
        print('      error:', scan.get('error_message', ''))

    record('the scan record has a pending review block',
           (scan.get('review') or {}).get('status') == 'pending')

    status, _, raw = call(base, 'GET', '/api/scans/', token)
    items = as_json(raw) or []
    mine = [s for s in items if s.get('scan_id') == scan_id] if isinstance(items, list) else []
    record('history list has the scan with product_name and score fields',
           len(mine) == 1 and 'product_name' in mine[0] and 'score' in mine[0])

    image_url = scan.get('image_url')
    if image_url:
        status, _, raw = call(base, 'GET', image_url)
        record('the photo is reachable at image_url', status == 200 and len(raw) > 100, f'status {status}')

    # Member 3's endpoints: SKIP while they do not exist yet (404).
    status, headers, raw = call(base, 'GET', f'/api/scans/{scan_id}/report/', token)
    if status == 404 and (as_json(raw) or {}).get('error') != 'The report is not ready yet.':
        skip('PDF report', 'not built yet')
    else:
        record('PDF report downloads with Content-Type application/pdf',
               status == 200 and 'application/pdf' in (headers.get('Content-Type') or '') and raw[:4] == b'%PDF',
               f'status {status}')
    status, _, raw = call(base, 'GET', f'/api/scans/{scan_id}/alternatives/', token)
    if status == 404:
        skip('alternatives', 'not built yet')
    else:
        items = as_json(raw)
        good = status == 200 and isinstance(items, list) and all(
            {'name', 'category', 'why'} <= set(i) for i in items)
        record('alternatives is a list of {name, category, why}', good, f'status {status}')

    failed_count = sum(1 for _, ok in results if not ok)
    print()
    print(f'{len(results) - failed_count} passed, {failed_count} failed.')
    sys.exit(1 if failed_count else 0)


main()