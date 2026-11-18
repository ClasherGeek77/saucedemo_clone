#!/usr/bin/env python3
"""Local clone of https://www.saucedemo.com/ (the Sauce Labs demo app).

The real app is fully client-side — users, passwords (`secret_sauce`), products
and cart logic live inside the JS bundle — so a byte-faithful static mirror is a
complete functional clone. `mirror.py` in this directory produced `static/` from
the live deployment; selectors, routes and behavior are identical.

    python3 server.py                # http://localhost:50000
    python3 server.py --port 8080

Login accounts (same as saucedemo.com): standard_user, problem_user,
performance_glitch_user, error_user, visual_user (locked_out_user is rejected),
password: secret_sauce.

Notes:
- Fonts are served locally from static/, no external requests.
- Unknown paths serve index.html (SPA router), matching the deployed app.
"""
import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, 'static')


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB, **kwargs)

    def send_head(self):
        # SPA fallback: any request that isn't a real file serves the app shell
        path = self.translate_path(self.path)
        if not os.path.exists(path):
            self.path = '/index.html'
        return super().send_head()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, fmt, *args):
        print('%s %s' % (self.address_string(), fmt % args))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--host', default='localhost')
    ap.add_argument('--port', type=int, default=50000)
    args = ap.parse_args()
    httpd = ThreadingHTTPServer((args.host, args.port), SpaHandler)
    print('saucedemo clone on http://%s:%d  (Ctrl-C to stop)' % (args.host, args.port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
