"""Dataset table -> poster histories -> graph tables -> features.

Run one step at a time:  python graph.py histories | graph | features
Nothing after a post's own posting time is ever used for that post.
"""
import csv
import math
import sys
from collections import Counter

from collect import IMAGES, PAIRS, POSTS, image_url, read_csv, write_csv
from config import DATA, HISTORY_DAYS
from utils import archive, read_jsonl, user_code, write_jsonl

HIST, GRAPH = DATA / "histories", DATA / "graph"
HIST.mkdir(exist_ok=True)
GRAPH.mkdir(exist_ok=True)
DAY = 86400
MAX_PAGES = 10  # 100 records a page: at most 1,000 posts and 1,000 comments per author


def _page(path, **params):
    rows, after, pages = {}, params.pop("after"), 0
    while pages < MAX_PAGES:
        batch = archive(path, after=after, sort="asc", limit=100, **params)
        pages += 1
        new = [x for x in batch if x["id"] not in rows]
        rows.update((x["id"], x) for x in new)
        if len(batch) < 100 or not new:
            return list(rows.values()), False
        after = int(batch[-1]["created_utc"])
    return list(rows.values()), True


def histories():
    """Each indexed author's posts and comments from HISTORY_DAYS before their first indexed post."""
    index = read_csv(DATA / "index.csv")
    names = {}
    for f in POSTS.glob("*.jsonl"):
        for p in read_jsonl(f):
            names[user_code(p.get("author"))] = p.get("author")
    span = {}
    for r in index:
        t = int(r["created_utc"])
        lo, hi = span.get(r["author"], (t, t))
        span[r["author"]] = (min(lo, t), max(hi, t))
    for code, (lo, hi) in span.items():
        out = HIST / f"{code}.jsonl"
        name = names.get(code)
        if out.exists() or not name or name == "[deleted]":
            continue
        posts, cut_p = _page("/api/posts/search", author=name, after=lo - HISTORY_DAYS * DAY, before=hi)
        comments, cut_c = _page("/api/comments/search", author=name, after=lo - HISTORY_DAYS * DAY, before=hi)
        keep = []
        for p in posts:
            keep.append({"kind": "post", "id": p["id"], "subreddit": p.get("subreddit"),
                         "created_utc": int(p["created_utc"]), "image_url": image_url(p) or "",
                         "crosspost_parent": (p.get("crosspost_parent") or "").replace("t3_", ""),
                         "truncated": cut_p})
        for c in comments:
            keep.append({"kind": "comment", "id": c["id"], "subreddit": c.get("subreddit"),
                         "created_utc": int(c["created_utc"]), "link_id": (c.get("link_id") or "").replace("t3_", ""),
                         "truncated": cut_c})
        write_jsonl(out, keep)  # usernames are not stored here; the file is named by the account's code
        print(f"{code}: {len(posts)} posts, {len(comments)} comments{' (capped)' if cut_p or cut_c else ''}")


def graph():
    """Two plain tables, nodes.csv and links.csv, that also load into Neo4j as they are."""
    pool = read_csv(POSTS / "image_posts.csv")
    nodes, links = {}, []
    for p in pool:
        nodes[p["author"]] = {"id": p["author"], "type": "User", "subreddit": "", "time": ""}
        nodes[p["post_id"]] = {"id": p["post_id"], "type": "Post", "subreddit": p["subreddit"], "time": p["created_utc"]}
        links.append({"src": p["author"], "dst": p["post_id"], "type": "POSTED", "time": p["created_utc"]})
        if (IMAGES / p["img"]).exists():
            nodes[p["img"]] = {"id": p["img"], "type": "Image", "subreddit": "", "time": ""}
            links.append({"src": p["post_id"], "dst": p["img"], "type": "HAS_IMAGE", "time": p["created_utc"]})
        if p["crosspost_parent"]:
            links.append({"src": p["post_id"], "dst": p["crosspost_parent"], "type": "CROSSPOSTED", "time": p["created_utc"]})
    for f in HIST.glob("*.jsonl"):
        code = f.stem
        nodes.setdefault(code, {"id": code, "type": "User", "subreddit": "", "time": ""})
        for h in read_jsonl(f):
            if h["kind"] == "post":
                nodes.setdefault(h["id"], {"id": h["id"], "type": "Post", "subreddit": h["subreddit"], "time": h["created_utc"]})
                links.append({"src": code, "dst": h["id"], "type": "POSTED", "time": h["created_utc"]})
            elif h["link_id"]:
                nodes.setdefault(h["link_id"], {"id": h["link_id"], "type": "Post", "subreddit": h["subreddit"], "time": ""})
                links.append({"src": code, "dst": h["link_id"], "type": "COMMENTED_ON", "time": h["created_utc"]})
    for r in read_csv(PAIRS / "diff.csv"):
        kind = {"repost": "SAME_AS", "edit": "VARIANT_OF"}.get(r["kind"])
        if kind:  # undirected; which side is the edit is the label and is never stored in the graph
            links.append({"src": r["img_a"], "dst": r["img_b"], "type": kind, "time": ""})
    links = list({(l["src"], l["dst"], l["type"], l["time"]): l for l in links}.values())
    write_csv(GRAPH / "nodes.csv", nodes.values(), ["id", "type", "subreddit", "time"])
    write_csv(GRAPH / "links.csv", links, ["src", "dst", "type", "time"])
    print("nodes:", dict(Counter(n["type"] for n in nodes.values())), "links:", dict(Counter(l["type"] for l in links)))


def _entropy(counts):
    n = sum(counts.values())
    return -sum(c / n * math.log(c / n) for c in counts.values()) if n else 0.0


def features():
    """Poster-history numbers for each indexed post, as of its posting time, with the pair hidden."""
    index = read_csv(DATA / "index.csv")
    pairs = {r["pair_id"]: r for r in read_csv(PAIRS / "diff.csv")}
    pool = read_csv(POSTS / "image_posts.csv")
    same = {}  # image -> images that are the same picture or an altered variant (from the pixel comparison)
    for r in pairs.values():
        if r["kind"] in ("repost", "edit"):
            same.setdefault(r["img_a"], set()).add((r["img_b"], r["kind"]))
            same.setdefault(r["img_b"], set()).add((r["img_a"], r["kind"]))
    first_seen = {}  # image -> earliest posting time of that exact file in the pool
    for p in pool:
        t = int(p["created_utc"])
        first_seen[p["img"]] = min(first_seen.get(p["img"], t), t)
    pool_by_author = {}
    for p in pool:
        pool_by_author.setdefault(p["author"], []).append(p)

    rows = []
    for r in index:
        t, code = int(r["created_utc"]), r["author"]
        hidden = set()
        if r["pair_id"]:
            hidden = {pairs[r["pair_id"]]["img_a"], pairs[r["pair_id"]]["img_b"]}
        hist_file = HIST / f"{code}.jsonl"
        hist = read_jsonl(hist_file) if hist_file.exists() else []
        hist = [h for h in hist if t - HISTORY_DAYS * DAY <= h["created_utc"] < t and h["id"] != r["post_id"]]
        posts = [h for h in hist if h["kind"] == "post"]
        comments = [h for h in hist if h["kind"] == "comment"]
        subs = Counter(h["subreddit"] for h in hist)
        earliest = min((h["created_utc"] for h in hist), default=t)
        # Earlier image posts by this author inside our pool, minus anything carrying the pair's images.
        mine = [p for p in pool_by_author.get(code, [])
                if int(p["created_utc"]) < t and p["img"] not in hidden and p["post_id"] != r["post_id"]]

        def seen_before(p, kinds):
            tp = int(p["created_utc"])
            if first_seen.get(p["img"], tp) < tp and "repost" in kinds:
                return True
            return any(k in kinds and o not in hidden and first_seen.get(o, tp) < tp for o, k in same.get(p["img"], ()))

        rows.append({
            "post_id": r["post_id"], "label": r["label"], "pair_id": r["pair_id"], "author": code, "img": r["img"],
            "subreddit": r["subreddit"], "created_utc": t, "has_history": int(hist_file.exists()),
            "n_posts": len(posts), "n_comments": len(comments), "n_subreddits": len(subs),
            "subreddit_entropy": round(_entropy(subs), 4),
            "share_image_posts": round(sum(bool(h.get("image_url")) for h in posts) / len(posts), 4) if posts else 0,
            "days_observed": round((t - earliest) / DAY, 2),
            "posts_per_day": round(len(posts) / max((t - earliest) / DAY, 1), 4),
            "n_prior_pool_posts": len(mine),
            "prior_repost_share": round(sum(seen_before(p, {"repost"}) for p in mine) / len(mine), 4) if mine else 0,
            "prior_variant_share": round(sum(seen_before(p, {"edit"}) for p in mine) / len(mine), 4) if mine else 0,
            "history_capped": int(any(h.get("truncated") for h in hist)),
        })
    write_csv(DATA / "features.csv", rows)
    print(f"features: {len(rows)} rows")


if __name__ == "__main__":
    steps = {"histories": histories, "graph": graph, "features": features}
    for name in sys.argv[1:] or list(steps):
        steps[name]()
