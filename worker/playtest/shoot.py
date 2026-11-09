#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""playtest-shoot: serve a web app inside the cage, open it in headless Chromium,
take screenshots and report what went wrong in the browser.

The playtester role calls this, then READS the screenshots (change
add-playtester-role). Nothing leaves the cage: the server listens on 127.0.0.1
and any request to another host is blocked and reported.

  playtest-shoot --serve-dir web --path / --viewport 390x844 --viewport 1280x800
  playtest-shoot --serve-cmd "npm run preview -- --port {port}" --path /play/
  playtest-shoot --serve-dir web --steps-json '[{"click": "#play"}, {"shot": "game"}]'
Steps: a JSON list of {"goto": "/x"}, {"click": "css"}, {"tap": [x, y]},
{"press": "Enter"}, {"wait": ms}, {"shot": "name"}. Shots go to --out (default
/work/playtest) as <viewport>-<name>.jpg; a summary JSON goes to stdout.
"""
import argparse, functools, http.server, json, os, re, shlex, socket
import subprocess, sys, threading, time, urllib.request
from pathlib import Path

MAX_SHOTS = 12


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve_dir(root, port):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=root)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def wait_up(url, seconds):
    end = time.time() + seconds
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception as exc:
            if getattr(exc, "code", None):   # an HTTP error still means it is up
                return True
            time.sleep(0.5)
    return False


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "home"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--serve-dir")
    src.add_argument("--serve-cmd", help="command with {port}; runs until done")
    p.add_argument("--path", action="append", default=[])
    p.add_argument("--viewport", action="append", default=[])
    p.add_argument("--steps", help="file with a JSON list of steps")
    p.add_argument("--steps-json", help="the same list, inline (the role cannot write files)")
    p.add_argument("--out", default="/work/playtest")
    p.add_argument("--startup", type=float, default=60)
    a = p.parse_args()
    paths = a.path or ["/"]
    viewports = a.viewport or ["390x844", "1280x800"]
    steps = (json.loads(a.steps_json) if a.steps_json
             else json.loads(Path(a.steps).read_text()) if a.steps else None)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    proc = srv = None
    if a.serve_dir:
        srv = serve_dir(a.serve_dir, port)
    else:
        proc = subprocess.Popen(shlex.split(a.serve_cmd.format(port=port)),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report = {"base": base, "shots": [], "console_errors": [], "page_errors": [],
              "http_errors": [], "blocked_external": [], "step_errors": []}
    try:
        if not wait_up(base + paths[0], a.startup):
            report["step_errors"].append(f"server did not answer on {base} within {a.startup}s")
            return report
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=os.environ.get("PLAYTEST_CHROMIUM") or None)
            for vp in viewports:
                w, h = (int(x) for x in vp.lower().split("x"))
                ctx = browser.new_context(viewport={"width": w, "height": h},
                                          has_touch=w < 700, is_mobile=w < 700)
                page = ctx.new_page()

                def route(r, req=None):
                    u = r.request.url
                    if u.startswith(base) or u.startswith(("data:", "blob:")):
                        return r.continue_()
                    report["blocked_external"].append(u)
                    return r.abort()

                page.route("**/*", route)
                page.on("console", lambda m, vp=vp: m.type == "error" and
                        report["console_errors"].append(f"{vp}: {m.text}"))
                page.on("pageerror", lambda e, vp=vp: report["page_errors"].append(f"{vp}: {e}"))
                page.on("response", lambda r, vp=vp: r.status >= 400 and
                        report["http_errors"].append(f"{vp}: {r.status} {r.url}"))

                def shot(name):
                    if len(report["shots"]) >= MAX_SHOTS:
                        return
                    f = out / f"{vp}-{slug(name)}.jpg"
                    page.screenshot(path=str(f), type="jpeg", quality=70)
                    report["shots"].append(str(f))

                if steps is None:
                    for path in paths:
                        page.goto(base + path, wait_until="networkidle")
                        page.wait_for_timeout(800)
                        shot(path)
                else:
                    page.goto(base + paths[0], wait_until="networkidle")
                    for i, st in enumerate(steps):
                        try:
                            if "goto" in st:
                                page.goto(base + st["goto"], wait_until="networkidle")
                            elif "click" in st:
                                page.click(st["click"], timeout=5000)
                            elif "tap" in st:
                                page.mouse.click(*st["tap"])
                            elif "press" in st:
                                page.keyboard.press(st["press"])
                            elif "wait" in st:
                                page.wait_for_timeout(int(st["wait"]))
                            elif "shot" in st:
                                shot(st["shot"])
                        except Exception as exc:
                            report["step_errors"].append(f"{vp} step {i} {st}: {exc}")
                    shot("end")
                ctx.close()
            browser.close()
    finally:
        if srv:
            srv.shutdown()
        if proc:
            proc.terminate()
    return report


if __name__ == "__main__":
    r = main()
    print(json.dumps(r, indent=1))
    sys.exit(0)
