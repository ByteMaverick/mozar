"""Shared helpers: polite archive client, image downloader, file helpers."""
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from config import ARCHIVE, ARCHIVE_GAP

UA = "academic-research/0.1 (course project, one request per 1.5 s)"
_last = [0.0]


def archive(path, **params):
    """GET an archive endpoint, at most one request per ARCHIVE_GAP seconds. Returns the 'data' list."""
    url = ARCHIVE + path + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        wait = ARCHIVE_GAP - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r).get("data") or []
        except urllib.error.HTTPError as e:
            if e.code in (422, 429, 500, 502, 503, 504):
                print(f"  archive HTTP {e.code}, retrying ({attempt + 1}/6)", flush=True)
                time.sleep(15 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:  # ValueError: cut-off JSON
            print(f"  archive {type(e).__name__}, retrying ({attempt + 1}/6)", flush=True)
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"archive request kept failing: {url}")


def download(url, dest):
    """Download one file. Returns True on success. Never raises."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            if r.geturl().endswith("removed.png") or len(body) < 2000:
                return False  # Reddit serves a placeholder for deleted images
        tmp = Path(str(dest) + ".part")
        tmp.write_bytes(body)
        tmp.rename(dest)
        return True
    except Exception:
        return False


def user_code(name):
    """Stable code for an account. Real names stay only in the raw post files on the HPC."""
    if name in (None, "[deleted]", "AutoModerator"):
        return name
    return "u_" + hashlib.sha1(("mozar|" + name).encode()).hexdigest()[:12]


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    tmp = Path(str(path) + ".part")
    with open(tmp, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    tmp.rename(path)
