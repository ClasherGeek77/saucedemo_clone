# saucedemo_clone

## what it is

a local, offline copy of the Sauce Labs practice shop https://www.saucedemo.com/ (login page, product list, cart, checkout). it listens on **port 50000**.

the real site is a client-side app: users, products and cart logic all live in its JavaScript bundle. so this repo is a static mirror of that bundle (`static/`, produced by `mirror.py`) plus a small python file that serves it. the pages, routes and element locators are the same as the real site, and fonts and images are local, so it works without internet.

there is no server-side state. everything (the logged-in user, the cart) lives in the browser, so the server never needs a reset.

## when to use it

- as the target for web UI automation: selenium, katalon, playwright and so on, on your own machine, always up, no flakiness from the public site.
- to practice locators, waits, login negative cases, cart and checkout flows.

when not to use it:

- you want to test APIs: use https://github.com/ClasherGeek77/reqresin_clone (REST clone) instead.
- you need the current version of the public site: this is a snapshot, later changes of saucedemo.com are not reflected. rerun `mirror.py` to take a new snapshot (see below).

repos that use it as their target:

| repo | how it uses the clone |
| --- | --- |
| https://github.com/ClasherGeek77/pytest_web_boilerplate | `BASE_URL=http://localhost:50000` in `test.env`; can start the clone itself via `SAUCEDEMO_CLONE_DIR` |
| https://github.com/ClasherGeek77/katalon_web_boilerplate | `Profiles/default.glbl` points at `http://localhost:50000` |

the `local` environment of https://github.com/ClasherGeek77/bruno_collection also defines `sd_url` for this clone, but none of its requests use it.

## what you need

- python 3.8 or newer (standard library only, nothing to pip install). checked on 3.8.2.
- git.
- a browser to look at it.

## quick start

```bash
git clone https://github.com/ClasherGeek77/saucedemo_clone.git
cd saucedemo_clone
python3 server.py
```

you should see:

```
saucedemo clone on http://localhost:50000  (Ctrl-C to stop)
```

open http://localhost:50000 in a browser: you should see the Swag Labs login page. log in with `standard_user` / `secret_sauce` and you land on the product list.

check from the command line:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:50000/
```

you should see `200`.

### start on another port

```bash
python3 server.py --port 8080
```

`--host` is also available (default `localhost`). tell your tests the new URL (`BASE_URL` in pytest, the Katalon profile value).

### run it in the background and stop it

```bash
python3 server.py > /tmp/saucedemo.log 2>&1 &
echo $! > /tmp/saucedemo.pid
# later
kill "$(cat /tmp/saucedemo.pid)"
```

in the foreground, stop with Ctrl-C.

### reset state

nothing is stored on the server. to start from a clean state (empty cart, logged out), clear the site data for `localhost:50000` in the browser, or use a fresh browser profile or a private window. test frameworks that launch a new browser per run already do this.

## accounts

password for all of them: `secret_sauce`.

| username | behavior |
| --- | --- |
| `standard_user` | normal user |
| `problem_user` | broken images and other deliberate defects |
| `performance_glitch_user` | slow login |
| `error_user` | errors on some actions |
| `visual_user` | deliberate visual defects |
| `locked_out_user` | rejected: "Sorry, this user has been locked out." |

the behaviors are those of the public site, taken from its code; the exact defects of each user are not documented here, explore them in the browser. a wrong password or an empty field gives the usual `Epic sadface: ...` message.

## routes

the app uses client-side routing. these paths exist: `/` (login), `/inventory.html`, `/inventory-item.html`, `/cart.html`, `/checkout-step-one.html`, `/checkout-step-two.html`, `/checkout-complete.html`. any path that is not a real file serves `index.html`, as the deployed site does, so a refresh or a direct URL on any route works.

## how to read the code

- `server.py`: static file server with the single-page-app fallback and open CORS.
- `static/`: the mirrored site (`index.html`, `assets/` with the minified JS and images, `fonts/` with local fonts). do not edit the JS by hand.
- `mirror.py`: one-shot spider that rebuilds `static/` from a live deployment: `python3 mirror.py [origin] [--dest static]` (default origin `https://www.saucedemo.com`). it needs internet and overwrites the files in `static/`.

## if it breaks

| symptom | cause | fix |
| --- | --- | --- |
| `OSError: [Errno 48] Address already in use` (Linux: `Errno 98`) | something already listens on 50000, often a previous copy of this server | find it with `lsof -iTCP:50000 -sTCP:LISTEN`, stop it, or start with `--port` |
| browser: "connection refused" or tests time out on the first page | the server is not running | start it with `python3 server.py` |
| you are still logged in or the cart is not empty | state is kept in the browser | clear site data for `localhost:50000` or use a private window |
| a test works on saucedemo.com but not here | the snapshot is older than the live site | rerun `mirror.py` into a scratch folder and compare, or adapt the test to the snapshot |
| `ImportError` or `SyntaxError` on start | python older than 3.8 | use a newer python3 |

## next

- web tests in python (selenium + pytest): https://github.com/ClasherGeek77/pytest_web_boilerplate
- web tests in Katalon: https://github.com/ClasherGeek77/katalon_web_boilerplate
- the REST API twin of this clone: https://github.com/ClasherGeek77/reqresin_clone
