"""Draws the three figures in docs/img/ (PNG and PDF). Run from the repository root: python docs/make_figures.py"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans", "font.size": 7, "pdf.fonttype": 42})
IMG = "docs/img/"
PANEL = {"grey": ("#f2f2f2", "#8f8f8f"), "blue": ("#dfeaf7", "#5b8fd0"), "purple": ("#e9e0f3", "#9a7cc7"),
         "yellow": ("#fdf4d3", "#d9ae2f"), "green": ("#e1f0db", "#6aa84f"), "red": ("#f9dfdd", "#d5655f")}
FINE, LINE, MARK = "#666666", "#9a9a9a", "#d62728"
LABEL = {"manipulated": "#c0392b", "matched": "#3f8f3a", "fresh": "#3b6ea5"}
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


def panel(ax, x, y, w, h, color, n=None, title=None, note=None):
    fill, edge = PANEL[color]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6", fc=fill, ec=edge, lw=0.8,
                                ls=(0, (3, 2)), zorder=1))
    if n:
        ax.add_patch(Circle((x + 0.8, y + h - 0.8), 2.1, fc="black", ec="white", lw=0.6, zorder=6))
        ax.text(x + 0.8, y + h - 0.95, str(n), color="white", fontsize=6.5, weight="bold", ha="center", va="center",
                zorder=7)
    if title:
        T(ax, x + w / 2, y + h - 3.6, title, size=7.2, weight="bold", ha="center")
    if note:
        T(ax, x + w / 2, y + h - 6.7, note, size=5.2, color=FINE, ha="center")


def card(ax, x, y, w, h, ec=LINE, fc="white", lw=0.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8", fc=fc, ec=ec, lw=lw, zorder=2))


def row(ax, x, y, w, name, n, h=4.4, ec=LINE, fc="white", bold=False, size=5.8):
    card(ax, x, y, w, h, ec=ec, fc=fc, lw=0.9 if bold else 0.6)
    T(ax, x + 1.3, y + h / 2, name, size=size, weight="bold" if bold else "normal")
    T(ax, x + w - 1.3, y + h / 2, n, size=size, ha="right", weight="bold")


def arrow(ax, a, b, color="black", lw=0.8, ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=6.5, lw=lw, color=color, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=3))


def picture(ax, name, x, y, w, boxes=()):
    im = mpimg.imread(IMG + "pairs/" + name)
    h = w * im.shape[0] / im.shape[1]
    ax.imshow(im, extent=(x, x + w, y, y + h), aspect="auto", zorder=2)
    ax.add_patch(Rectangle((x, y), w, h, fill=False, ec="black", lw=0.5, zorder=3))
    for bx, by, bw, bh in boxes:  # boxes are fractions of the picture, measured from its top-left corner
        x0, y0 = max(bx, 0.015), max(by, 0.02)
        x1, y1 = min(bx + bw, 0.985), min(by + bh, 0.98)
        ax.add_patch(Rectangle((x + x0 * w, y + h - y1 * h), (x1 - x0) * w, (y1 - y0) * h, fill=False, ec=MARK,
                               lw=0.9, zorder=4))
    return h


HAT = [(0.321, -0.007, 0.359, 0.557)]


# Figure 1: how the dataset and the graph are built ------------------------------------------

def figure1():
    fig, ax, size = canvas(7.2, 4.3)
    xs, w, y, h = [3, 38.4, 73.8, 109.2], 32.4, 47, 36
    for a in xs[:-1]:
        arrow(ax, (a + w + 0.3, 65), (a + w + 2.7, 65))

    x = xs[0]
    panel(ax, x, y, w, h, "grey", 1, "Collect", "15 communities · needs internet")
    for k, (name, n) in enumerate((("Posts", "48,924"), ("Image posts", "29,053"), ("Images on disk", "16,078"))):
        row(ax, x + 3, 67 - 8.6 * k, w - 6, name, n)
    for k, s in enumerate(("has an image, not flagged adult", "39% were already deleted")):
        arrow(ax, (x + 6.5, 67 - 8.6 * k), (x + 6.5, 67 - 8.6 * k - 4.2))
        T(ax, x + 8.3, 67 - 8.6 * k - 2.1, s, size=5, color=FINE)

    x = xs[1]
    panel(ax, x, y, w, h, "purple", 2, "Find look-alikes", "CPU only")
    bits = [1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0]
    for k, name in enumerate(("hat_a.jpg", "hat_b.jpg")):
        px = x + 2.5 + k * 14.4
        picture(ax, name, px, 63.2, 13)
        for i, b in enumerate(bits):
            flip = k == 1 and i in (5, 11)
            ax.add_patch(Rectangle((px + i * 13 / 16, 60.8), 13 / 16, 1.3, fc="#4d4d4d" if b != flip else "white",
                                   ec=MARK if flip else "#8a8a8a", lw=0.7 if flip else 0.3, zorder=4 if flip else 3))
    T(ax, x + w / 2, 58.2, "64-bit perceptual hash of every image", size=5, color=FINE, ha="center")
    T(ax, x + w / 2, 55.6, "a pair if at most 10 bits differ", size=5, color=FINE, ha="center")
    row(ax, x + 3, 49.4, w - 6, "Look-alike pairs", "1,260")

    x = xs[2]
    panel(ax, x, y, w, h, "yellow", 3, "Compare the pixels", "line up · subtract · threshold · CPU only")
    for k, (name, n) in enumerate((("exact repost", "1,009"), ("different picture", "127"), ("caption only", "3"))):
        row(ax, x + 3, 66.6 - 5.6 * k, w - 6, name, n)
    row(ax, x + 3, 49.4, w - 6, "edit candidate", "121", ec="#d9822b", fc="#ffe9b0", bold=True)

    x = xs[3]
    panel(ax, x, y, w, h, "green", 4, "Label the edits", "one H100, then a person")
    picture(ax, "hat_b.jpg", x + 2.5, 64.4, 11.2, HAT)
    for k, s in enumerate(("a vision-language", "model is asked twice,", "with the two versions", "swapped")):
        T(ax, x + 15, 71.4 - 2.3 * k, s, size=5, color=FINE)
    row(ax, x + 3, 58.4, w - 6, "labeled", "16", h=4.2, ec=PANEL["green"][1], bold=True)
    row(ax, x + 3, 53.4, w - 6, "undecided → hand check", "59", h=4.2, size=5.4)
    row(ax, x + 3, 48.4, w - 6, "not an edit", "46", h=4.2)
    arrow(ax, (x + w / 2, 46.7), (x + w / 2, 43.5))

    # the graph
    panel(ax, 3, 4.5, 138.6, 38.5, "blue", 5)
    T(ax, 7.5, 39.3, "Build the graph", size=7.2, weight="bold")
    T(ax, 31.5, 39.2, "accounts, posts and pictures, with each poster's earlier activity (180 days back)", size=5.2,
      color=FINE)
    ya, yp, yi = 29.5, 20.5, 6.3
    acc = {"A": 20, "B": 52, "C": 82}
    posts = {"p1": (20, "matched"), "p2": (47, "manipulated"), "p3": (57, "manipulated"), "p4": (82, "fresh")}
    for name, cx in acc.items():
        ax.add_patch(Circle((cx, ya), 2.1, fc="#fcefdc", ec="black", lw=0.7, zorder=4))
        T(ax, cx - 3.2, ya, "account " + name, size=5.4, ha="right")
    for (name, cx), n in zip(acc.items(), (1, 4, 2)):
        for k in range(n):
            px = cx - 2.3 * (n - 1) + 4.6 * k
            ax.add_patch(Rectangle((px - 0.8, ya + 4.6), 1.6, 1.6, fc="white", ec=LINE, lw=0.5, zorder=4))
            ax.plot([cx, px], [ya + 2.1, ya + 4.6], color=LINE, lw=0.4, zorder=2)
    T(ax, 23.5, ya + 5.4, "earlier posts and comments", size=5, color=FINE, style="italic")
    for cx, kind in posts.values():
        ax.add_patch(Rectangle((cx - 1.8, yp - 1.8), 3.6, 3.6, fc="white", ec=LABEL[kind], lw=1.3, zorder=4))
    for a, ps in (("A", ["p1"]), ("B", ["p2", "p3"]), ("C", ["p4"])):
        for p in ps:
            arrow(ax, (acc[a], ya - 2.1), (posts[p][0], yp + 1.8), lw=0.7)
    hi = picture(ax, "hat_a.jpg", 14.5, yi, 11)
    picture(ax, "hat_b.jpg", 46.5, yi, 11)
    card(ax, 77.5, yi + 0.8, 9, hi - 1.6, fc="#f4f4f4")
    T(ax, 82, yi + hi / 2, "a new\npicture", size=4.8, color=FINE, ha="center", linespacing=1.2)
    for a, b in (((20, yp - 1.8), (20, yi + hi)), ((47, yp - 1.8), (50, yi + hi)), ((57, yp - 1.8), (54, yi + hi)),
                 ((82, yp - 1.8), (82, yi + hi - 0.8))):
        arrow(ax, a, b, lw=0.7)
    ax.plot([25.5, 46.5], [yi + hi / 2, yi + hi / 2], color="black", lw=1.5, zorder=2)
    mono(ax, 36, yi + hi / 2 + 1.6, "VARIANT_OF", ha="center")
    arrow(ax, (acc["C"] - 2, ya - 0.8), (21.9, yp + 0.9), color=FINE, lw=0.6, ls=(0, (3, 2)), rad=-0.07)
    mono(ax, 68, 24.2, "COMMENTED_ON", ha="center")
    mono(ax, 21, 25, "POSTED")
    mono(ax, 21, 16.4, "HAS_IMAGE")
    T(ax, 13.6, yi + hi / 2, "original", size=5.4, ha="right")
    T(ax, 58.4, yi + hi / 2, "edited", size=5.4)
    card(ax, 100, 7, 38.6, 28)
    ax.add_patch(Circle((103.4, 31.6), 1.2, fc="#fcefdc", ec="black", lw=0.6, zorder=4))
    T(ax, 105.6, 31.6, "account", size=5.2)
    ax.add_patch(Rectangle((115, 30.5), 2.2, 2.2, fc="white", ec="black", lw=0.8, zorder=4))
    T(ax, 118.4, 31.6, "post", size=5.2)
    ax.add_patch(Rectangle((125.2, 30.6), 3, 2, fc="#cfcfcf", ec="black", lw=0.5, zorder=4))
    T(ax, 129.4, 31.6, "picture", size=5.2)
    for k, (kind, s) in enumerate((("manipulated", "manipulated · carries the edit"),
                                   ("matched", "authentic, matched · the original"),
                                   ("fresh", "authentic, fresh · no look-alike"))):
        ax.add_patch(Rectangle((102.3, 25.4 - 3.7 * k), 2.2, 2.2, fc="white", ec=LABEL[kind], lw=1.2, zorder=4))
        T(ax, 105.6, 26.5 - 3.7 * k, s, size=5.2)
    T(ax, 102.3, 14.8, "exact reposts are joined by SAME_AS links", size=4.9, color=FINE)
    T(ax, 102.3, 10.6, "Which side of a pair is the edit is the label.\nIt is never stored in the graph.", size=4.9,
      color=FINE, style="italic", linespacing=1.3)
    T(ax, 141.6, 2.2, "counts: one month of 15 communities, 8 Oct to 8 Nov 2026", size=5, color=FINE, ha="right",
      style="italic")
    finish(fig, ax, size, "fig1_dataset")


# Figure 2: the three predictors and how they are compared -----------------------------------

def figure2():
    fig, ax, size = canvas(7.2, 3.5)
    panel(ax, 3, 5, 41, 62, "grey", 1, "One post, two views")
    picture(ax, "hat_b.jpg", 6, 45.5, 18)
    for k, s in enumerate(("image $x$", "posted by $u$", "at time $t$")):
        T(ax, 26, 55.6 - 3.8 * k, s, size=6.2)
    T(ax, 6, 39.6, "history $H_t$: what $u$ did before $t$", size=6.2)
    y0, x0, xt, x1 = 27, 6, 33, 41.5
    ax.plot([x0, x1], [y0, y0], color="black", lw=0.7, zorder=3)
    for px in (8, 10.5, 14, 15.5, 20, 22.5, 25, 28.5):
        ax.add_patch(Circle((px, y0 + 2.4), 0.75, fc="#3b6ea5", ec="none", zorder=4))
    for px in (9.5, 17.5, 26.5):
        ax.add_patch(Rectangle((px - 1, y0 + 4.6), 2, 2, fc="white", ec="#3b6ea5", lw=0.9, zorder=4))
    ax.add_patch(Rectangle((29.8, y0 + 4.6), 2, 2, fc="white", ec=FINE, lw=0.8, ls=(0, (2, 1.5)), zorder=4))
    for px in (35.5, 38, 40.5):
        ax.add_patch(Circle((px, y0 + 2.4), 0.75, fc="#c9c9c9", ec="none", zorder=4))
    ax.plot([xt, xt], [y0 - 2.2, y0 + 9], color=MARK, lw=0.9, ls=(0, (3, 2)), zorder=4)
    T(ax, xt, y0 - 4, "$t$", size=6.5, color=MARK, ha="center")
    T(ax, x0, y0 - 4, "$t$ − 180 days", size=5, color=FINE)
    T(ax, 38, y0 + 6.2, "never\nused", size=5, color=FINE, ha="center", style="italic", linespacing=1.2)
    ax.add_patch(Rectangle((6, 16.2), 1.8, 1.8, fc="white", ec="#3b6ea5", lw=0.8, zorder=4))
    T(ax, 9.2, 17.1, "post", size=5.2)
    ax.add_patch(Circle((6.9, 13.3), 0.75, fc="#3b6ea5", ec="none", zorder=4))
    T(ax, 9.2, 13.3, "comment", size=5.2)
    ax.add_patch(Rectangle((6, 8.6), 1.8, 1.8, fc="white", ec=FINE, lw=0.8, ls=(0, (2, 1.5)), zorder=4))
    T(ax, 9.2, 9.5, "post of the same picture: hidden", size=5.2)

    x, w = 48, 55
    panel(ax, x, 49, w, 18, "blue", 2, "M0 · image only", "two published detectors, used as released")
    card(ax, x + 2.5, 51.4, 13.5, 5.6)
    T(ax, x + 9.25, 54.2, "FLAME", size=6, ha="center")
    card(ax, x + 17.5, 51.4, 13.5, 5.6)
    T(ax, x + 24.25, 54.2, "TruFor", size=6, ha="center")
    arrow(ax, (x + 31, 54.2), (x + 39.5, 54.2))
    card(ax, x + 39.5, 51.4, 13, 5.6, ec=PANEL["blue"][1])
    T(ax, x + 46, 54.2, r"score $p_{\rm img}$", size=6, ha="center")

    panel(ax, x, 5, w, 18, "yellow", 3, "M1 · history only", "activity · spread · image share · earlier reposts and variants")
    card(ax, x + 2.5, 7.4, 16, 5.6)
    T(ax, x + 10.5, 10.2, r"features $\phi(u;H_t)$", size=6, ha="center")
    arrow(ax, (x + 18.5, 10.2), (x + 20.5, 10.2))
    card(ax, x + 20.5, 7.4, 17, 5.6)
    T(ax, x + 29, 10.2, "logistic regression", size=5.4, ha="center")
    arrow(ax, (x + 37.5, 10.2), (x + 39.5, 10.2))
    card(ax, x + 39.5, 7.4, 13, 5.6, ec=PANEL["yellow"][1])
    T(ax, x + 46, 10.2, r"score $p_{\rm hist}$", size=6, ha="center")

    panel(ax, x, 27, w, 18, "green", 4, "M2 · both", "history shifts the detector's odds")
    card(ax, x + 4, 29.4, w - 8, 5.6, ec=PANEL["green"][1])
    T(ax, x + w / 2, 32.2, r"${\rm logit}\ p = a \cdot {\rm logit}\ p_{\rm img} + b \cdot {\rm logit}\ p_{\rm hist} + c$",
      size=6, ha="center")
    arrow(ax, (44.3, 58), (47.7, 58))
    arrow(ax, (44.3, 14), (47.7, 14))
    arrow(ax, (x + w / 2, 48.7), (x + w / 2, 45.3))
    arrow(ax, (x + w / 2, 23.3), (x + w / 2, 26.7))
    arrow(ax, (x + w + 0.3, 36), (x + w + 3.7, 36))

    x = 107
    panel(ax, x, 5, 34.6, 62, "red", 5, "Compare", "5-fold cross-validation")
    for f in range(5):
        for g in range(5):
            out = f == g
            ax.add_patch(Rectangle((x + 3.4 + 5.6 * g, 54 - 3.1 * f), 5, 2.4, fc="#f1b3ae" if out else "white",
                                   ec=PANEL["red"][1] if out else "#b5b5b5", lw=0.9 if out else 0.5, zorder=3))
    ax.add_patch(Rectangle((x + 3.4, 37.4), 3, 1.8, fc="#f1b3ae", ec=PANEL["red"][1], lw=0.9, zorder=3))
    T(ax, x + 7.4, 38.3, "held out", size=5)
    ax.add_patch(Rectangle((x + 17.4, 37.4), 3, 1.8, fc="white", ec="#b5b5b5", lw=0.5, zorder=3))
    T(ax, x + 21.4, 38.3, "training", size=5)
    T(ax, x + 3.4, 34.6, "an account or a picture is never\non both sides of a split", size=5, color=FINE,
      style="italic", va="top", linespacing=1.3)
    for k, (a, b) in enumerate((("M2 against M0", "does history add anything?"), ("M1 alone", "how far does history get?"),
                                ("M2, history shuffled", "a control for model size"))):
        card(ax, x + 2.6, 20.6 - 7 * k, 29.4, 6)
        T(ax, x + 4, 24.6 - 7 * k, a, size=5.6, weight="bold")
        T(ax, x + 4, 22.1 - 7 * k, b, size=5, color=FINE)
    finish(fig, ax, size, "fig2_models")


# Figure 3: four real pairs ------------------------------------------------------------------

def figure3():
    fig, ax, size = canvas(7.2, 3.4)
    cols = [("year", "blue", "Text on a backdrop", "a year is in one version only", "0.8% of pixels",
             [(0.81, 0.21, 0.228, 0.189), (0.32, 0.219, 0.272, 0.187)]),
            ("hat", "purple", "Object added", "a top hat", "2.6% of pixels", HAT),
            ("person", "yellow", "Person inserted", "a figure placed in the doorway", "1.8% of pixels",
             [(0.391, 0.296, 0.219, 0.589)]),
            ("wave", "green", "Picture reworked", "rabbits added along the wave", "25.5% of pixels", [])]
    w, gap = 33.3, 1.8
    for k, (name, color, title, what, share, boxes) in enumerate(cols):
        x = 3 + k * (w + gap)
        panel(ax, x, 3, w, 62, color, k + 1, title)
        for r, side in enumerate("ab"):
            picture(ax, f"{name}_{side}.jpg", x + 1.8, 35.4 - 23.4 * r, w - 3.6, boxes)
        T(ax, x + w / 2, 8.8, what, size=5.4, ha="center")
        T(ax, x + w / 2, 5.8, share, size=5.2, color=FINE, ha="center")
    finish(fig, ax, size, "fig3_examples")


if __name__ == "__main__":
    figure1()
    figure2()
    figure3()
