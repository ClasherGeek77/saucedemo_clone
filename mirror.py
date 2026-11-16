#!/usr/bin/env python3
"""One-shot asset spider: builds static/ from a live saucedemo.com deployment.

    python3 mirror.py [origin] [--dest static]

Follows index.html -> /assets/* (js/css/manifest/icons) -> lazy-import chunk
names found inside each js -> image/font paths ("/static/...", "/assets/...")
found in css+js, until closure. stdlib only.
"""
import argparse
import json
import os
import re
import urllib.request

ASSET_RE = re.compile(r'(?:src|href)="/((?:assets|static)/[^"]+|favicon\.ico|icon-\d+x\d+\.png|manifest\.json|robots\.txt|404\.html)"')
IN_JS_RE = re.compile(r'''[`"'](/?(?:assets|static)/[A-Za-z0-9._/-]+\.(?:js|css|png|jpe?g|svg|gif|woff2?|json))[`"']|[`"']\./([A-Za-z0-9._-]+\.(?:js|css|woff2?|png|jpg))[`"']''')


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 mirror'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(), r.headers.get('Content-Type', '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('origin', nargs='?', default='https://www.saucedemo.com')
    ap.add_argument('--dest', default='static')
    args = ap.parse_args()
    origin = args.origin.rstrip('/')
    queue = ['/']
    seen = set()
    while queue:
        path = queue.pop(0)
        if path in seen or path.startswith('//'):
            continue
        seen.add(path)
        url = origin + path
        try:
            body, ctype = fetch(url)
        except Exception as e:  # noqa: BLE001 - mirror best-effort
            print('skip', path, e)
            continue
        rel = path.lstrip('/') or 'index.html'
        out = os.path.join(args.dest, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as f:
            f.write(body)
        print('got', rel, len(body))
        text = body.decode('utf-8', 'replace')
        found = set(ASSET_RE.findall(text)) if 'html' in ctype or rel.endswith('.html') else set()
        if 'javascript' in ctype or rel.endswith('.js'):
            for m in IN_JS_RE.finditer(text):
                g = m.group(1) or m.group(2)
                if not g:
                    continue
                if g.startswith('./'):
                    found.add('assets/' + g[2:])  # lazy chunks live beside the entry chunk
                elif g.startswith(('/', 'assets/', 'static/')):
                    found.add(g.lstrip('/'))
        if 'css' in ctype or rel.endswith('.css'):
            found |= {u.lstrip('/') for u in re.findall(r'url\(["\']?(/[^)"\']+)', text)}
        for r in found:
            r = r.split('?')[0]
            p = '/' + r
            if p not in seen and not p.endswith('.html') or p == '/404.html':
                queue.append(p)
    localize_fonts(args.dest)
    print('mirrored %d files (+ fonts)' % len(seen))


def localize_fonts(dest):
    """Replace the Google Fonts link in index.html with local /fonts.css + woff2 files."""
    ua = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
    idx_path = os.path.join(dest, 'index.html')
    with open(idx_path) as f:
        html = f.read()
    m = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com[^"]*)"', html)
    if not m:
        print('no google fonts link found; skipped font localization')
        return
    req = urllib.request.Request(m.group(1), headers=ua)
    css = urllib.request.urlopen(req, timeout=20).read().decode()
    os.makedirs(os.path.join(dest, 'fonts'), exist_ok=True)
    for i, gurl in enumerate(re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', css)):
        name = 'font-%d.woff2' % i
        body, _ = fetch(gurl)
        with open(os.path.join(dest, 'fonts', name), 'wb') as f:
            f.write(body)
        css = css.replace(gurl, '/fonts/' + name)
    with open(os.path.join(dest, 'fonts.css'), 'w') as f:
        f.write(css)
    html = html.replace(m.group(0), '<link rel="stylesheet" href="/fonts.css"')
    with open(idx_path, 'w') as f:
        f.write(html)
    print('fonts localized -> /fonts.css + /fonts/font-*.woff2')


if __name__ == '__main__':
    main()
