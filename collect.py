"""Posts -> images -> look-alike pairs -> pixel comparison -> model labels -> dataset table.

Run one step at a time:  python collect.py posts | images | pairs | diff | judge | index | review
Every step saves its output under data/ and skips work that is already done, so any step can be rerun.
'posts' and 'images' need the internet, 'judge' needs a GPU, the rest only need CPUs.
"""
import csv
import html
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np

from config import (AFTER, BEFORE, DATA, EDIT_MAX, FRESH_PER_MANIPULATED, HASH_MAX_BITS,
                    IMAGE_WORKERS, JUDGE_MODEL, MODELS, REPOST_MAX, SUBREDDITS)
from utils import archive, download, read_jsonl, user_code, write_jsonl

POSTS, IMAGES, PAIRS, LABELS = DATA / "posts", DATA / "images", DATA / "pairs", DATA / "labels"
for d in (POSTS, IMAGES, PAIRS / "outline", LABELS):
    d.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or (list(rows[0]) if rows else [])
    tmp = path.with_suffix(".part")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    tmp.rename(path)


# 1. Posts ---------------------------------------------------------------------------------

def get_posts():
    """Every post in each community for the period, saved in full, one file per community."""
    for sub in SUBREDDITS:
        out = POSTS / f"{sub}_{AFTER}_{BEFORE}.jsonl"
        if out.exists():
            continue
        rows, after = {}, AFTER
        while True:
            batch = archive("/api/posts/search", subreddit=sub, after=after, before=BEFORE,
                            sort="asc", limit=100)
            new = [p for p in batch if p["id"] not in rows]
            rows.update((p["id"], p) for p in new)
            print(f"  {sub}: {len(rows)} posts so far", flush=True)
            if len(batch) < 100 or not new:
                break
            after = int(batch[-1]["created_utc"])
        write_jsonl(out, rows.values())
        print(f"{sub}: {len(rows)} posts")
    image_posts()


def image_url(p):
    """The post's image link, or None. Adult posts and animations are skipped."""
    if p.get("over_18"):
        return None
    url = html.unescape(p.get("url_overridden_by_dest") or p.get("url") or "")
    if p.get("is_gallery") and p.get("gallery_data") and p.get("media_metadata"):
        first = p["gallery_data"]["items"][0]["media_id"]
        meta = p["media_metadata"].get(first) or {}
        if meta.get("e") == "Image":
            ext = (meta.get("m") or "image/jpg").split("/")[-1].replace("jpeg", "jpg")
            return f"https://i.redd.it/{first}.{ext}"
        return None
    if re.search(r"\.(jpe?g|png|webp)$", url.split("?")[0], re.I):
        return url
    if p.get("post_hint") == "image" and p.get("preview"):
        return html.unescape(p["preview"]["images"][0]["source"]["url"])
    return None


def image_posts():
    """One row per image post. The image file is named after its link, so posts sharing a file share a row key."""
    rows = []
    for f in sorted(POSTS.glob("*.jsonl")):
        for p in read_jsonl(f):
            url = image_url(p)
            if not url:
                continue
            ext = re.search(r"\.(jpe?g|png|webp)", url.split("?")[0], re.I)
            img = re.sub(r"[^A-Za-z0-9]", "", url.split("?")[0].split("/")[-1].rsplit(".", 1)[0])[:40]
            rows.append({
                "post_id": p["id"], "subreddit": p["subreddit"], "author": user_code(p.get("author")),
                "created_utc": int(p["created_utc"]), "url": url,
                "img": img + "." + (ext.group(1).lower() if ext else "jpg"),
                "crosspost_parent": (p.get("crosspost_parent") or "").replace("t3_", ""),
                "removed": p.get("removed_by_category") or "",
            })
    write_csv(POSTS / "image_posts.csv", rows)
    print(f"image posts: {len(rows)}, distinct image links: {len({r['url'] for r in rows})}")


# 2. Images --------------------------------------------------------------------------------

def fetch_images():
    """Download each distinct image once. Failed links are listed in images/missing.txt."""
    gone = set((IMAGES / "missing.txt").read_text().split()) if (IMAGES / "missing.txt").exists() else set()
    todo = {}
    for r in read_csv(POSTS / "image_posts.csv"):
        if not (IMAGES / r["img"]).exists() and r["img"] not in gone:
            todo[r["img"]] = r["url"]
    with ThreadPoolExecutor(IMAGE_WORKERS) as ex:
        ok = list(ex.map(lambda kv: download(kv[1], IMAGES / kv[0]), todo.items()))
    missing = [k for k, good in zip(todo, ok) if not good]
    with open(IMAGES / "missing.txt", "a") as f:
        f.writelines(m + "\n" for m in missing)
    print(f"downloaded {sum(ok)} of {len(todo)}; total on disk {len(list(IMAGES.glob('*.*'))) - 1}")


# 3. Look-alike pairs ----------------------------------------------------------------------

def find_pairs():
    """Perceptual hash of every image; pairs whose hashes differ in at most HASH_MAX_BITS of 64 bits."""
    import imagehash
    from PIL import Image

    hashes_csv = PAIRS / "hashes.csv"
    known = {r["img"]: r for r in read_csv(hashes_csv)} if hashes_csv.exists() else {}
    for p in sorted(IMAGES.iterdir()):
        if p.name in known or p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        try:
            im = Image.open(p).convert("RGB")
            flat = float(np.asarray(im.convert("L").resize((64, 64))).std()) < 12  # near-blank images match everything
            known[p.name] = {"img": p.name, "phash": str(imagehash.phash(im)), "w": im.width, "h": im.height,
                             "flat": int(flat)}
        except Exception:
            known[p.name] = {"img": p.name, "phash": "", "w": 0, "h": 0, "flat": 1}
    write_csv(hashes_csv, known.values(), ["img", "phash", "w", "h", "flat"])

    usable = [r for r in known.values() if r["phash"] and r["flat"] in (0, "0")]
    names = [r["img"] for r in usable]
    bits = np.array([int(r["phash"], 16) for r in usable], dtype=np.uint64)
    pairs = []
    for i in range(len(bits) - 1):
        d = np.bitwise_count(bits[i] ^ bits[i + 1:])
        for j in np.nonzero(d <= HASH_MAX_BITS)[0]:
            pairs.append((names[i], names[i + 1 + j], int(d[j])))
    # An image matching many others is usually a meme template or a screenshot style; drop it.
    count = {}
    for a, b, _ in pairs:
        count[a] = count.get(a, 0) + 1
        count[b] = count.get(b, 0) + 1
    # Pair numbers never change between runs, so labels and the hand check keep pointing at the same pictures.
    old = {(r["img_a"], r["img_b"]): r["pair_id"] for r in read_csv(PAIRS / "pairs.csv")} if (PAIRS / "pairs.csv").exists() else {}
    nxt = max((int(v[1:]) for v in old.values()), default=-1) + 1
    rows = []
    for a, b, d in pairs:
        if count[a] <= 10 and count[b] <= 10:
            if (a, b) not in old:
                old[(a, b)], nxt = f"p{nxt:05d}", nxt + 1
            rows.append({"pair_id": old[(a, b)], "img_a": a, "img_b": b, "bits": d})
    write_csv(PAIRS / "pairs.csv", rows, ["pair_id", "img_a", "img_b", "bits"])
    print(f"hashed {len(usable)} usable images; look-alike pairs: {len(rows)} (dropped {len(pairs) - len(rows)} template matches)")


# 4. Pixel comparison ----------------------------------------------------------------------

def _load(path, side=1024):
    import cv2
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    s = side / max(im.shape[:2])
    return cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else im


def compare(path_a, path_b):
    """Line B up on A, subtract, and describe what changed."""
    import cv2
    A, B = _load(path_a), _load(path_b)
    a, b = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)
    ha, wa = a.shape
    H, inliers = None, 0
    orb = cv2.ORB_create(4000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is not None and db is not None and len(ka) > 20 and len(kb) > 20:
        m = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(db, da), key=lambda x: x.distance)[:800]
        if len(m) >= 15:
            src = np.float32([kb[x.queryIdx].pt for x in m])
            dst = np.float32([ka[x.trainIdx].pt for x in m])
            H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
            inliers = int(mask.sum()) if mask is not None else 0
    if H is None or inliers < 15:  # fall back to plain resizing
        H = np.array([[wa / b.shape[1], 0, 0], [0, ha / b.shape[0], 0], [0, 0, 1]], dtype=np.float64)
    warped = cv2.warpPerspective(b, H, (wa, ha))
    valid = cv2.warpPerspective(np.full_like(b, 255), H, (wa, ha)) > 0
    valid = cv2.erode(valid.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    diff = cv2.absdiff(cv2.GaussianBlur(a, (5, 5), 0), cv2.GaussianBlur(warped, (5, 5), 0))
    changed = ((diff > 35) & valid).astype(np.uint8)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    overlap = valid.mean()
    frac = changed.sum() / max(valid.sum(), 1)

    regions = []  # nearby changes are merged so the outline shows a few large boxes, not many small ones
    k = max(15, int(0.06 * max(ha, wa)))
    grouped = cv2.dilate(changed, np.ones((k, k), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(grouped)
    for i, (x, y, w, h, _) in enumerate(stats[1:], start=1):
        if changed[labels == i].sum() >= 0.001 * ha * wa:
            regions.append((int(x), int(y), int(w), int(h)))
    if overlap < 0.5 or (inliers < 15 and frac >= REPOST_MAX):  # could not line them up: different pictures
        kind = "unrelated"
    elif frac < REPOST_MAX:
        kind = "repost"
    elif frac > EDIT_MAX:
        kind = "unrelated"
    else:
        ys, xs = np.nonzero(changed)
        band = xs.max() - xs.min() > 0.6 * wa and ys.max() - ys.min() < 0.3 * ha and (
            ys.min() < 0.08 * ha or ys.max() > 0.92 * ha)
        kind = "caption" if band else "edit"
    return {"changed": round(float(frac), 4), "overlap": round(float(overlap), 3), "inliers": inliers,
            "kind": kind}, (A, B, H, regions)


def _outline(img, boxes_poly, path):
    import cv2
    out = img.copy()
    for poly in boxes_poly:
        cv2.polylines(out, [np.int32(poly)], True, (0, 0, 255), 4)
    cv2.imwrite(str(path), out, [cv2.IMWRITE_JPEG_QUALITY, 92])


def diff_pairs():
    """Classify every look-alike pair: repost, caption, unrelated, or edit (with the change outlined on both)."""
    import cv2
    out_csv = PAIRS / "diff.csv"
    done = {r["pair_id"]: r for r in read_csv(out_csv)} if out_csv.exists() else {}
    for r in read_csv(PAIRS / "pairs.csv"):
        if r["pair_id"] in done:
            continue
        try:
            res, (A, B, H, regions) = compare(IMAGES / r["img_a"], IMAGES / r["img_b"])
        except Exception as e:
            res, regions = {"changed": "", "overlap": "", "inliers": "", "kind": f"error:{type(e).__name__}"}, []
        if res["kind"] == "edit":
            boxes_a = [np.float32([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]) for x, y, w, h in regions]
            Hinv = np.linalg.inv(H)
            boxes_b = [cv2.perspectiveTransform(bx.reshape(-1, 1, 2), Hinv).reshape(-1, 2) for bx in boxes_a]
            _outline(A, boxes_a, PAIRS / "outline" / f"{r['pair_id']}_a.jpg")
            _outline(B, boxes_b, PAIRS / "outline" / f"{r['pair_id']}_b.jpg")
        done[r["pair_id"]] = {**r, **res}
    rows = list(done.values())
    write_csv(out_csv, rows, ["pair_id", "img_a", "img_b", "bits", "changed", "overlap", "inliers", "kind"])
    kinds = {}
    for x in rows:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    print("pair kinds:", kinds)


# 5. Model judgment (GPU) ------------------------------------------------------------------

PROMPT = """You will see three images.
Image 1 and Image 2 are two versions of the same picture.
Image 3 shows Image 1 with the region that differs outlined in red.
The red boxes were drawn by the researchers to show where to look. They are not part
of either picture and are not the edit. Compare what is inside the boxes in Image 1 and Image 2.

Answer in JSON with exactly these keys:
1. "real_edit": Is the difference a change to the picture's content? "yes" or "no".
   Answer "no" for a caption, sticker, watermark, crop, border or color change.
2. "edited_image": Which version was altered: "1", "2", or "cannot_tell"?
   Decide from visible traces: edges that do not blend, lighting or shadows that
   do not match, texture or sharpness that differs from the rest, physically odd
   objects, leftovers of what was there before.
   If neither version shows traces, answer "cannot_tell". Do not guess.
3. "evidence": One sentence naming the trace you relied on.
4. "looks_ai": Does the edit look made by an AI image tool: "yes", "no", or "cannot_tell"?
5. "confidence": "high", "medium" or "low".
6. "picture_type": What kind of picture is this?
   "photo": a photograph of a real scene or real people.
   "meme": a meme template, comic, cartoon, or a picture built around large caption text.
   "screenshot": a capture of a post, chat, app or web page.
   "other": a poster, painting, illustration, or a film or game still.
Reply with the JSON object only."""


def judge_pairs():
    """Ask the vision-language model about each edit candidate twice, with the two versions swapped."""
    import torch
    from PIL import Image
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    local = MODELS / JUDGE_MODEL.split("/")[-1]
    model = Qwen3VLForConditionalGeneration.from_pretrained(local, dtype=torch.bfloat16, device_map="cuda")
    processor = AutoProcessor.from_pretrained(local)
    out = LABELS / "judgments.jsonl"
    done = {(j["pair_id"], j["order"]) for j in read_jsonl(out)} if out.exists() else set()

    def small(path):
        im = Image.open(path).convert("RGB")
        im.thumbnail((1024, 1024))
        return im

    for r in read_csv(PAIRS / "diff.csv"):
        if r["kind"] != "edit":
            continue
        for order, (first, second, outline) in {
            "ab": (r["img_a"], r["img_b"], f"{r['pair_id']}_a.jpg"),
            "ba": (r["img_b"], r["img_a"], f"{r['pair_id']}_b.jpg"),
        }.items():
            if (r["pair_id"], order) in done:
                continue
            content = [{"type": "image", "image": small(IMAGES / first)},
                       {"type": "image", "image": small(IMAGES / second)},
                       {"type": "image", "image": small(PAIRS / "outline" / outline)},
                       {"type": "text", "text": PROMPT}]
            inputs = processor.apply_chat_template([{"role": "user", "content": content}], tokenize=True,
                                                   add_generation_prompt=True, return_dict=True,
                                                   return_tensors="pt").to(model.device)
            with torch.no_grad():
                ids = model.generate(**inputs, max_new_tokens=256, do_sample=False)
            text = processor.batch_decode(ids[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
            m = re.search(r"\{.*\}", text, re.S)
            try:
                ans = json.loads(m.group(0)) if m else {}
            except json.JSONDecodeError:
                ans = {}
            pick = str(ans.get("edited_image", "")).strip()
            edited = first if pick == "1" else second if pick == "2" else ""
            rec = {"pair_id": r["pair_id"], "order": order, "model": JUDGE_MODEL, "answer": ans,
                   "edited_file": edited, "raw": text}
            with open(out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(r["pair_id"], order, ans.get("real_edit"), ans.get("edited_image"), ans.get("confidence"))
    decide()


def decide():
    """A pair is labeled only if both orders say it is a real edit and point to the same file."""
    by_pair = {}
    for j in read_jsonl(LABELS / "judgments.jsonl"):
        by_pair.setdefault(j["pair_id"], {})[j["order"]] = j
    rows = []
    for pid, js in by_pair.items():
        if len(js) < 2:
            continue
        a, b = js["ab"], js["ba"]
        votes = [str(x["answer"].get("real_edit", "")).lower() for x in (a, b)]
        real, not_real = votes == ["yes", "yes"], votes == ["no", "no"]
        agree = a["edited_file"] and a["edited_file"] == b["edited_file"]
        types = [str(x["answer"].get("picture_type", "")).lower() for x in (a, b)]
        rows.append({"pair_id": pid,
                     "decision": "labeled" if real and agree else ("not_an_edit" if not_real else "undecided"),
                     "edited_img": a["edited_file"] if real and agree else "",
                     "looks_ai": a["answer"].get("looks_ai", ""),
                     "confidence": f"{a['answer'].get('confidence', '')}/{b['answer'].get('confidence', '')}",
                     "evidence": a["answer"].get("evidence", ""), "hand_check": "",
                     "picture_type": types[0] if types[0] == types[1] else "unclear"})
    write_csv(LABELS / "decisions.csv", rows,
              ["pair_id", "decision", "edited_img", "looks_ai", "confidence", "evidence", "hand_check", "picture_type"])
    print("decisions:", {d: sum(r["decision"] == d for r in rows) for d in ("labeled", "undecided", "not_an_edit")})


# 6. Dataset table -------------------------------------------------------------------------

def build_index():
    """One row per post: manipulated, authentic_matched (carries the other version), or authentic_fresh."""
    posts = read_csv(POSTS / "image_posts.csv")
    by_img = {}
    for p in posts:
        by_img.setdefault(p["img"], []).append(p)
    pairs = {r["pair_id"]: r for r in read_csv(PAIRS / "diff.csv")}
    decisions = read_csv(LABELS / "decisions.csv") if (LABELS / "decisions.csv").exists() else []
    # Hand check wins over the model. labels/hand_check.csv: pair_id,verdict  (verdict: A, B or no)
    hand = {h["pair_id"]: h["verdict"].strip().upper() for h in read_csv(LABELS / "hand_check.csv")} \
        if (LABELS / "hand_check.csv").exists() else {}
    for d in decisions:
        v = hand.pop(d["pair_id"], None)
        if v:
            d["hand_check"] = v
            d["decision"] = "labeled" if v in ("A", "B") else "not_an_edit"
            d["edited_img"] = pairs[d["pair_id"]]["img_a" if v == "A" else "img_b"] if v in ("A", "B") else ""
    # One row per post. An image can sit in several pairs (one edit, many reposts of the original);
    # a post that is the edited side of any labeled pair is manipulated, whatever else it matched.
    keep = {}
    for d in decisions:
        if d["decision"] != "labeled":
            continue
        pr = pairs[d["pair_id"]]
        orig = pr["img_b"] if d["edited_img"] == pr["img_a"] else pr["img_a"]
        for img, label in ((d["edited_img"], "manipulated"), (orig, "authentic_matched")):
            for p in by_img.get(img, []):
                if p["post_id"] not in keep or (label == "manipulated" and keep[p["post_id"]]["label"] != label):
                    keep[p["post_id"]] = {**p, "label": label, "pair_id": d["pair_id"], "hand_check": d["hand_check"],
                                           "picture_type": d.get("picture_type", "")}
    rows = list(keep.values())
    # Fresh: images with no look-alike at all, from the same communities.
    paired = {x for r in read_csv(PAIRS / "pairs.csv") for x in (r["img_a"], r["img_b"])}
    on_disk = {p.name for p in IMAGES.iterdir()}
    fresh = [p for p in posts if p["img"] in on_disk and p["img"] not in paired]
    n_manip = sum(r["label"] == "manipulated" for r in rows)
    random.Random(0).shuffle(fresh)
    for p in fresh[:max(FRESH_PER_MANIPULATED * n_manip, 30)]:  # never fewer than 30, so a small run still has rows
        rows.append({**p, "label": "authentic_fresh", "pair_id": "", "hand_check": "", "picture_type": ""})
    fields = ["post_id", "subreddit", "author", "created_utc", "img", "label", "pair_id", "hand_check", "picture_type",
              "crosspost_parent", "removed", "url"]
    write_csv(DATA / "index.csv", rows, fields)
    print("index:", {k: sum(r["label"] == k for r in rows) for k in ("manipulated", "authentic_matched", "authentic_fresh")})


# Review page for the hand check -----------------------------------------------------------

def review_page():
    """data/pairs/review.html: every edit candidate side by side with the model's answers."""
    js = {}
    if (LABELS / "judgments.jsonl").exists():
        for j in read_jsonl(LABELS / "judgments.jsonl"):
            js.setdefault(j["pair_id"], {})[j["order"]] = j
    dec = {d["pair_id"]: d for d in read_csv(LABELS / "decisions.csv")} if (LABELS / "decisions.csv").exists() else {}
    cards = []
    for r in read_csv(PAIRS / "diff.csv"):
        if r["kind"] != "edit":
            continue
        d = dec.get(r["pair_id"], {})
        ans = "".join(
            f"<li><b>{o}</b>: {html.escape(json.dumps(js[r['pair_id']][o]['answer']))}</li>"
            for o in ("ab", "ba") if o in js.get(r["pair_id"], {}))
        cards.append(f"""<section><h3>{r['pair_id']} · changed {float(r['changed']):.1%} · decision: {d.get('decision', 'not judged')}
 · edited: {'A' if d.get('edited_img') == r['img_a'] else 'B' if d.get('edited_img') else '-'}</h3>
<div class=row><figure><img src="outline/{r['pair_id']}_a.jpg"><figcaption>A</figcaption></figure>
<figure><img src="outline/{r['pair_id']}_b.jpg"><figcaption>B</figcaption></figure></div><ul>{ans}</ul></section>""")
    page = f"""<!doctype html><meta charset=utf-8><title>Mozar edit candidates</title>
<style>body{{font:14px system-ui;margin:20px}}.row{{display:flex;gap:12px}}figure{{margin:0;flex:1}}
img{{width:100%}}section{{border-bottom:1px solid #ccc;padding:12px 0}}</style>
<h1>Edit candidates ({len(cards)})</h1><p>Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC.
Red boxes mark where the two versions differ.</p>{''.join(cards)}"""
    (PAIRS / "review.html").write_text(page)
    print(f"review page: {len(cards)} candidates -> {PAIRS / 'review.html'}")


if __name__ == "__main__":
    steps = {"posts": get_posts, "images": fetch_images, "pairs": find_pairs, "diff": diff_pairs,
             "judge": judge_pairs, "decide": decide, "index": build_index, "review": review_page}
    for name in sys.argv[1:] or ["posts", "images", "pairs", "diff"]:
        steps[name]()
