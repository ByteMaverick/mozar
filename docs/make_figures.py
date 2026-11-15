"""Draws the three figures in docs/img/ (PNG and PDF). Run from the repository root: python docs/make_figures.py"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans", "font.size": 7, "pdf.fonttype": 42})
IMG = "docs/img/"
FINE, LINE, MARK = "#666666", "#9a9a9a", "#d62728"   # red marks what was edited; everything else is grey
LABEL = {"manipulated": MARK, "matched": "black", "fresh": "#a0a0a0"}
U = 20  # drawing units per inch


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    return fig, ax, (w * U, h * U)


def finish(fig, ax, size, name):
    ax.set_xlim(0, size[0])
    ax.set_ylim(0, size[1])
    fig.savefig(IMG + name + ".png", dpi=300)
    fig.savefig(IMG + name + ".pdf")
    plt.close(fig)


def T(ax, x, y, s, size=6, color="black", ha="left", va="center", **kw):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, zorder=5, **kw)


def mono(ax, x, y, s, **kw):
    T(ax, x, y, s, size=4.6, color=FINE, family="DejaVu Sans Mono", **kw)


def panel(ax, x, y, w, h, title=None, note=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6", fc="#f5f5f5", ec="#7f7f7f", lw=0.8,
                                ls=(0, (3, 2)), zorder=1))
    if title:
        T(ax, x + w / 2, y + h - 3.6, title, size=7.2, weight="bold", ha="center")
    if note:
        T(ax, x + w / 2, y + h - 6.8, note, size=5.2, color=FINE, ha="center")


def card(ax, x, y, w, h, ec=LINE, fc="white", lw=0.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8", fc=fc, ec=ec, lw=lw, zorder=2))


def row(ax, x, y, w, name, n, rule=None, h=4.4, ec=LINE, fc="white", bold=False):
    """A white card with a name on the left and a count on the right; an optional second line explains it."""
    card(ax, x, y, w, h, ec=ec, fc=fc, lw=0.9 if bold else 0.6)
    top = y + h / 2 if rule is None else y + h - 2.2
    T(ax, x + 1.3, top, name, size=5.7, weight="bold" if bold else "normal")
    T(ax, x + w - 1.3, top, n, size=5.7, ha="right", weight="bold")
    if rule:
        T(ax, x + 1.3, y + 1.6, rule, size=4.5, color=FINE)


def arrow(ax, a, b, color="black", lw=0.8, ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=6.5, lw=lw, color=color, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=3))


def picture(ax, name, x, y, w, boxes=(), tag=None):
    im = mpimg.imread(IMG + "pairs/" + name)
    h = w * im.shape[0] / im.shape[1]
    ax.imshow(im, extent=(x, x + w, y, y + h), aspect="auto", zorder=2)
    ax.add_patch(Rectangle((x, y), w, h, fill=False, ec="black", lw=0.5, zorder=3))
    for bx, by, bw, bh in boxes:  # boxes are fractions of the picture, measured from its top-left corner
        x0, y0 = max(bx, 0.015), max(by, 0.02)
        x1, y1 = min(bx + bw, 0.985), min(by + bh, 0.98)
        ax.add_patch(Rectangle((x + x0 * w, y + h - y1 * h), (x1 - x0) * w, (y1 - y0) * h, fill=False, ec=MARK,
                               lw=0.9, zorder=4))
    if tag:
        ax.text(x + 1, y + 1, tag, fontsize=4.6, ha="left", va="bottom", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))
    return h


HAT = [(0.321, -0.007, 0.359, 0.557)]


# Figure 1: how the dataset and the graph are built ------------------------------------------

def figure1():
    fig, ax, size = canvas(7.2, 4.95)
    xs, w, y, h = [3, 38.4, 73.8, 109.2], 32.4, 50, 44
    for a in xs[:-1]:
        arrow(ax, (a + w + 0.3, 72), (a + w + 2.7, 72))

    x = xs[0]
    panel(ax, x, y, w, h, "Collect posts and images", "15 communities · needs internet")
    for k, (name, n) in enumerate((("Posts", "48,924"), ("Image posts", "29,053"), ("Images on disk", "16,078"))):
        row(ax, x + 3, 79.6 - 10.2 * k, w - 6, name, n)
    for k, (s1, s2) in enumerate((("kept if the post has an image", "and is not flagged adult"),
                                  ("each image downloaded once;", "39% were already deleted"))):
        top = 79.6 - 10.2 * k
        arrow(ax, (x + 6.5, top), (x + 6.5, top - 5.8))
        T(ax, x + 8.3, top - 1.8, s1, size=4.8, color=FINE)
        T(ax, x + 8.3, top - 4.0, s2, size=4.8, color=FINE)
    T(ax, x + w / 2, 55.6, "every post from the archive of Reddit:", size=4.7, color=FINE, ha="center")
    T(ax, x + w / 2, 53.2, "viral, political, celebrity, film, control", size=4.7, color=FINE, ha="center")

    x = xs[1]
    panel(ax, x, y, w, h, "Find look-alike pairs", "CPU only")
    bits = [1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0]
    for k, name in enumerate(("hat_a.jpg", "hat_b.jpg")):
        px = x + 2.5 + k * 14.4
        picture(ax, name, px, 73.6, 13)
        for i, b in enumerate(bits):
            flip = k == 1 and i in (5, 11)
            ax.add_patch(Rectangle((px + i * 13 / 16, 71.2), 13 / 16, 1.3, fc="#4d4d4d" if b != flip else "white",
                                   ec=MARK if flip else "#8a8a8a", lw=0.7 if flip else 0.3, zorder=4 if flip else 3))
    for k, s in enumerate(("each image gets a 64-bit perceptual hash;", "two images are a pair if at most",
                           "10 bits differ. Images that match more", "than 10 others are templates: dropped")):
        T(ax, x + w / 2, 68.2 - 2.5 * k, s, size=4.8, color=FINE, ha="center")
    row(ax, x + 3, 53, w - 6, "Look-alike pairs", "1,260")

    x = xs[2]
    panel(ax, x, y, w, h, "Compare the pixels", "line up · subtract · threshold · CPU only")
    for k, (name, n, rule) in enumerate((("exact repost", "1,009", "under 0.5% of pixels changed"),
                                         ("different picture", "127", "over 40% changed, or not alignable"),
                                         ("caption only", "3", "a band at the top or bottom edge"))):
        row(ax, x + 3, 76.4 - 7.6 * k, w - 6, name, n, rule, h=6.6)
    row(ax, x + 3, 53.6, w - 6, "edit candidate", "121", "part of the picture changed", h=6.6, ec="black",
        fc="#e4e4e4", bold=True)

    x = xs[3]
    panel(ax, x, y, w, h, "Label the edits", "one H100, then a person")
    picture(ax, "hat_b.jpg", x + 2.5, 75.6, 11.2, HAT)
    for k, s in enumerate(("a vision-language", "model is asked twice,", "versions swapped")):
        T(ax, x + 15, 82.4 - 2.5 * k, s, size=4.8, color=FINE)
    T(ax, x + w / 2, 72.8, "it answers: a real edit? which version?", size=4.6, color=FINE, ha="center")
    T(ax, x + w / 2, 70.5, "what trace? AI-made? what kind of picture?", size=4.6, color=FINE, ha="center")
    row(ax, x + 3, 63, w - 6, "labeled", "16", "both answers name the same version", h=5.4,
        ec="black", bold=True)
    row(ax, x + 3, 57.1, w - 6, "undecided", "59", "answers disagree: a person decides", h=5.4)
    row(ax, x + 3, 51.2, w - 6, "not an edit", "46", "both answers say no", h=5.4)
    arrow(ax, (x + w / 2, 49.7), (x + w / 2, 46.5))

    # the graph: RIFT's schema on the left, one real pair on the right
    panel(ax, 3, 4.5, 138.6, 41.5)
    T(ax, 7.5, 42.3, "Build the graph", size=7.2, weight="bold")
    T(ax, 31.5, 42.2, "the posts, users and subreddits of RIFT, with pictures and comments added", size=5.2, color=FINE)
    dash = (0, (3, 2))
    ax.add_patch(Circle((15, 28), 3, fc="#e6e6e6", ec="black", lw=0.8, zorder=4))
    T(ax, 15, 28, "User", size=4.8, ha="center")
    ax.add_patch(Rectangle((34.2, 25.2), 5.6, 5.6, fc="white", ec="black", lw=0.9, zorder=4))
    T(ax, 37, 28, "Post", size=4.8, ha="center")
    card(ax, 53.5, 25.5, 13, 5, ec="black", lw=0.8)
    T(ax, 60, 28, "Subreddit", size=4.8, ha="center")
    for x0 in (33.5, 53):
        ax.add_patch(Rectangle((x0, 10.5), 7, 5, fc="#cfcfcf", ec="black", lw=0.6, ls=dash, zorder=4))
        T(ax, x0 + 3.5, 13, "Image", size=4.8, ha="center")
    arrow(ax, (34.2, 28), (18, 28))
    mono(ax, 26.1, 29.6, "POSTED_BY", ha="center")
    arrow(ax, (39.8, 28), (53.5, 28))
    mono(ax, 46.6, 29.6, "BELONGS_TO", ha="center")
    arrow(ax, (37, 25.2), (37, 15.5), ls=dash)
    mono(ax, 38.2, 20.4, "HAS_IMAGE")
    ax.plot([40.5, 53], [13, 13], color="black", lw=0.9, ls=dash, zorder=2)
    mono(ax, 46.75, 14.6, "VARIANT_OF", ha="center")
    mono(ax, 46.75, 11.4, "SAME_AS", ha="center")
    arrow(ax, (16.5, 30.6), (35, 30.8), ls=dash, rad=-0.45)
    mono(ax, 26.1, 36.2, "COMMENTED_ON", ha="center")
    ax.plot([8, 13], [6.8, 6.8], color="black", lw=0.9)
    T(ax, 14.2, 6.8, "as in RIFT (Joshi, 2025)", size=4.6, color=FINE)
    ax.plot([38, 43], [6.8, 6.8], color="black", lw=0.9, ls=dash)
    T(ax, 44.2, 6.8, "added here", size=4.6, color=FINE)
    ax.plot([69.5, 69.5], [7, 39], color="#c4c4c4", lw=0.5)

    ya, yp, yi = 33.5, 23.5, 7.5
    for cx, kind, who, name in ((80, "matched", "A", "hat_a.jpg"), (110, "manipulated", "B", "hat_b.jpg")):
        ax.add_patch(Circle((cx, ya), 2.1, fc="#e6e6e6", ec="black", lw=0.7, zorder=4))
        ax.add_patch(Rectangle((cx - 1.8, yp - 1.8), 3.6, 3.6, fc="white", ec=LABEL[kind], lw=1.3, zorder=4))
        arrow(ax, (cx, yp + 1.8), (cx, ya - 2.1), lw=0.7)
        hi = picture(ax, name, cx - 5.5, yi, 11, tag="original" if who == "A" else "edited")
        arrow(ax, (cx, yp - 1.8), (cx, yi + hi), lw=0.7)
    T(ax, 80, ya + 4.2, "account A: posted the original", size=4.6, ha="center")
    T(ax, 113.1, ya + 0.9, "account B", size=4.8)
    T(ax, 113.1, ya - 1.7, "posted the edit", size=4.5, color=FINE)
    for k in range(3):
        px = 105.4 + 4.6 * k
        ax.add_patch(Rectangle((px - 0.8, ya + 4.6), 1.6, 1.6, fc="white", ec=LINE, lw=0.5, zorder=4))
        ax.plot([110, px], [ya + 2.1, ya + 4.6], color=LINE, lw=0.4, zorder=2)
    T(ax, 117.5, ya + 5.4, "earlier posts and comments", size=4.5, color=FINE, style="italic")
    card(ax, 85.5, yp - 2.3, 19, 4.6, ec="black", lw=0.7)
    T(ax, 95, yp, "r/shittymoviedetails", size=4.4, ha="center")
    arrow(ax, (81.8, yp), (85.5, yp), lw=0.7)
    arrow(ax, (108.2, yp), (104.5, yp), lw=0.7)
    ax.plot([85.5, 104.5], [yi + hi / 2, yi + hi / 2], color="black", lw=1.5, zorder=2)
    mono(ax, 95, yi + hi / 2 + 1.6, "VARIANT_OF", ha="center")
    T(ax, 95, yi + hi / 2 - 1.8, "one is an edit of the other", size=4.5, color=FINE, ha="center")
    for k, (kind, text) in enumerate((("manipulated", "manipulated"), ("matched", "authentic, matched"),
                                      ("fresh", "authentic, fresh"))):
        ax.add_patch(Rectangle((124, 25.4 - 3.6 * k), 2.2, 2.2, fc="white", ec=LABEL[kind], lw=1.2, zorder=4))
        T(ax, 127.2, 26.5 - 3.6 * k, text, size=4.8)
    T(ax, 124, 12.4, "Which side is the edit is the\nlabel. It is never stored\nin the graph.", size=4.4, color=FINE,
      style="italic", linespacing=1.3)
    T(ax, 141.6, 2.2, "counts: one month of 15 communities, 8 Oct to 8 Nov 2026", size=5, color=FINE, ha="right",
      style="italic")
    finish(fig, ax, size, "fig1_dataset")


# Figure 2: the three predictors and how they are compared -----------------------------------

def figure2():
    fig, ax, size = canvas(7.2, 3.7)
    panel(ax, 3, 5, 41, 66, "One post, two views")
    picture(ax, "hat_b.jpg", 6, 49, 18)
    for k, s in enumerate(("image $x$", "posted by $u$", "at time $t$")):
        T(ax, 26, 59.6 - 3.8 * k, s, size=6.2)
    T(ax, 6, 46.4, "what a forensic detector sees: pixels only", size=4.8, color=FINE)
    T(ax, 6, 41.8, "history $H_t$: what $u$ did before $t$", size=6.2)
    y0, x0, xt, x1 = 30, 6, 33, 41.5
    ax.plot([x0, x1], [y0, y0], color="black", lw=0.7, zorder=3)
    for px in (8, 10.5, 14, 15.5, 20, 22.5, 25, 28.5):
        ax.add_patch(Circle((px, y0 + 2.4), 0.75, fc="#3a3a3a", ec="none", zorder=4))
    for px in (9.5, 17.5, 26.5):
        ax.add_patch(Rectangle((px - 1, y0 + 4.6), 2, 2, fc="white", ec="#3a3a3a", lw=0.9, zorder=4))
    ax.add_patch(Rectangle((29.8, y0 + 4.6), 2, 2, fc="white", ec=FINE, lw=0.8, ls=(0, (2, 1.5)), zorder=4))
    for px in (35.5, 38, 40.5):
        ax.add_patch(Circle((px, y0 + 2.4), 0.75, fc="#c9c9c9", ec="none", zorder=4))
    ax.plot([xt, xt], [y0 - 2.2, y0 + 9], color="black", lw=0.9, ls=(0, (3, 2)), zorder=4)
    T(ax, xt, y0 - 4, "$t$", size=6.5, ha="center")
    T(ax, x0, y0 - 4, "$t$ − 180 days", size=5, color=FINE)
    T(ax, 38, y0 + 6.2, "never\nused", size=5, color=FINE, ha="center", style="italic", linespacing=1.2)
    T(ax, 6, 22, "what the history model sees: events before $t$ only", size=4.8, color=FINE)
    ax.add_patch(Rectangle((6, 15.4), 1.8, 1.8, fc="white", ec="#3a3a3a", lw=0.8, zorder=4))
    T(ax, 9.2, 16.3, "an earlier post", size=5.2)
    ax.add_patch(Circle((6.9, 12.7), 0.75, fc="#3a3a3a", ec="none", zorder=4))
    T(ax, 9.2, 12.7, "an earlier comment", size=5.2)
    ax.add_patch(Rectangle((6, 8.2), 1.8, 1.8, fc="white", ec=FINE, lw=0.8, ls=(0, (2, 1.5)), zorder=4))
    T(ax, 9.2, 9.1, "a post of the same picture: hidden", size=5.2)

    x, w = 48, 55
    panel(ax, x, 52, w, 19, "M0 · image only", "published detectors, used as released, not retrained")
    for k, (name, venue) in enumerate((("FLAME", "ICML 2026"), ("TruFor", "CVPR 2023"))):
        card(ax, x + 2.5 + 15 * k, 54, 13.5, 6.6)
        T(ax, x + 9.25 + 15 * k, 58.4, name, size=6, ha="center")
        T(ax, x + 9.25 + 15 * k, 55.7, venue, size=4.5, color=FINE, ha="center")
    arrow(ax, (x + 31, 57.3), (x + 39.5, 57.3))
    card(ax, x + 39.5, 54.5, 13, 5.6, ec="black")
    T(ax, x + 46, 57.3, r"score $p_{\rm img}$", size=6, ha="center")

    panel(ax, x, 5, w, 19, "M1 · history only", "activity · spread · image share · earlier reposts and variants")
    card(ax, x + 2.5, 7.4, 16, 5.6)
    T(ax, x + 10.5, 10.2, r"features $\phi(u;H_t)$", size=6, ha="center")
    arrow(ax, (x + 18.5, 10.2), (x + 20.5, 10.2))
    card(ax, x + 20.5, 7.4, 17, 5.6)
    T(ax, x + 29, 10.2, "logistic regression", size=5.4, ha="center")
    arrow(ax, (x + 37.5, 10.2), (x + 39.5, 10.2))
    card(ax, x + 39.5, 7.4, 13, 5.6, ec="black")
    T(ax, x + 46, 10.2, r"score $p_{\rm hist}$", size=6, ha="center")

    panel(ax, x, 28.5, w, 19, "M2 · both", "history acts as a prior that shifts the detector's odds")
    T(ax, x + w / 2, 38.4, "$a$, $b$ and $c$ are fitted on the training folds", size=4.8, color=FINE, ha="center")
    card(ax, x + 4, 30.6, w - 8, 5.6, ec="black")
    T(ax, x + w / 2, 33.4, r"${\rm logit}\ p = a \cdot {\rm logit}\ p_{\rm img} + b \cdot {\rm logit}\ p_{\rm hist} + c$",
      size=6, ha="center")
    arrow(ax, (44.3, 61), (47.7, 61))
    arrow(ax, (44.3, 14), (47.7, 14))
    arrow(ax, (x + w / 2, 51.7), (x + w / 2, 47.8))
    arrow(ax, (x + w / 2, 24.3), (x + w / 2, 28.2))
    arrow(ax, (x + w + 0.3, 38), (x + w + 3.7, 38))

    x = 107
    panel(ax, x, 5, 34.6, 66, "Compare", "5-fold cross-validation")
    for f in range(5):
        for g in range(5):
            out = f == g
            ax.add_patch(Rectangle((x + 3.4 + 5.6 * g, 57.4 - 3.1 * f), 5, 2.4, fc="#6a6a6a" if out else "white",
                                   ec="#3a3a3a" if out else "#b5b5b5", lw=0.9 if out else 0.5, zorder=3))
    ax.add_patch(Rectangle((x + 3.4, 40.6), 3, 1.8, fc="#6a6a6a", ec="#3a3a3a", lw=0.9, zorder=3))
    T(ax, x + 7.4, 41.5, "held out", size=5)
    ax.add_patch(Rectangle((x + 17.4, 40.6), 3, 1.8, fc="white", ec="#b5b5b5", lw=0.5, zorder=3))
    T(ax, x + 21.4, 41.5, "training", size=5)
    T(ax, x + 3.4, 38, "an account or a picture is never\non both sides of a split", size=4.8, color=FINE,
      style="italic", va="top", linespacing=1.3)
    T(ax, x + 3.4, 30.4, "score: AUROC, with a bootstrap interval", size=4.6, color=FINE)
    for k, (a, b) in enumerate((("M2 against M0", "does history add anything?"), ("M1 alone", "how far does history get?"),
                                ("M2, history shuffled", "a control for model size"))):
        card(ax, x + 2.6, 21.6 - 7 * k, 29.4, 6)
        T(ax, x + 4, 25.6 - 7 * k, a, size=5.6, weight="bold")
        T(ax, x + 4, 23.1 - 7 * k, b, size=5, color=FINE)
    finish(fig, ax, size, "fig2_models")


# Figure 3: four real pairs ------------------------------------------------------------------

def figure3():
    fig, ax, size = canvas(7.2, 3.3)
    cols = [("year", "Text on a backdrop", ("version A", "version B"), "A year is on the backdrop in one version",
             [(0.81, 0.21, 0.228, 0.189), (0.32, 0.219, 0.272, 0.187)]),
            ("hat", "Object added", ("original", "edited"), "A top hat is placed on the man's head", HAT),
            ("person", "Person inserted", ("original", "edited"), "A figure is placed in the doorway",
             [(0.391, 0.296, 0.219, 0.589)]),
            ("wave", "Picture reworked", ("original", "edited"), "Rabbits are added along the wave", [])]
    w, gap = 33.3, 1.8
    for k, (name, title, tags, what, boxes) in enumerate(cols):
        x = 3 + k * (w + gap)
        panel(ax, x, 3, w, 60, title)
        for r, side in enumerate("ab"):
            picture(ax, f"{name}_{side}.jpg", x + 1.8, 33.2 - 23.4 * r, w - 3.6, boxes, tags[r])
        T(ax, x + w / 2, 6.3, what, size=5.1, ha="center")
    finish(fig, ax, size, "fig3_examples")


if __name__ == "__main__":
    figure1()
    figure2()
    figure3()
