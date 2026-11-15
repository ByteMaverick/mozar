# What is weak or unfinished

Read this before trusting any number. Each item says what the problem is, why it matters, and what is planned.

## Data

1. **Very few labeled edits.** One month of 15 subreddits gave 12 manipulated posts; about 1 image in 1,000
   becomes a labeled edit before the hand check. A pair is only findable when both the original and the edit
   were posted inside our data. Target: at least 100 manipulated posts (a validation study needs 100 events,
   ideally 200, per Collins et al. 2016), which the January to October run should reach after the hand check.
   Below that, every result is a pilot.
2. **Most edits are memes.** The labeling model tags only about 1 in 8 likely edits as a photograph; most are
   memes, posters and film stills. A model trained on these may learn "who posts memes", not "who passes off a
   fake". Report photo edits as their own slice; the picture-type tag in `labels/decisions.csv` exists for this.
3. **Few edits look AI-made.** By eye, 2 or 3 of the first 20 viewed. Say "manipulated", not "AI-manipulated",
   unless that changes.
4. **The labeling model often cannot tell which version is the edit.** In the first month it said "edit" in both
   orders but named a different file each time for 41 of 121 candidates. Posting order does not settle it either
   (in one pair the watermarked copy came first). These pairs need the hand check, which is not done yet.
5. **39% of images were already deleted** when we reached them. If deleted images differ systematically (removed
   fakes, for instance), the sample is biased. Experiment E7 in the proposal tests this.
6. **Matching uses a perceptual hash only.** It misses crops, screenshots of a picture and heavy re-encodes. The
   proposal adds DINOv2 embeddings; not done yet.
7. **The template rule drops viral pictures.** An image matching more than 10 others is dropped as a meme
   template. In the January to October run this removed about 311,000 pairs, and it also removes real pictures
   reposted more than 10 times, which is exactly where edits appear. Needs a look: raise the limit or drop only
   the centre of a cluster.
8. **Fifteen hand-picked subreddits.** Fine for the class run; the paper needs a written selection rule.
9. **The adult flag also covers graphic content**, so those posts are skipped too (about 1 to 2% of posts in the
   big communities).

## Models and evaluation

10. **The detectors have not been run.** M0 and M2 are empty. Reddit stores JPEGs at quality 75, and published
    results show both detectors losing much of their accuracy under that recompression (TGIF; FLAME's own
    robustness table). Measure this first; it is also part of the motivation.
11. **Edited posts are all re-posts.** The social features may learn "this account reposts", not "this account
    edits". The matched originals and the 1,000+ exact-repost pairs are the control; keep comparing against them.
12. **Small sample, many choices.** With a few hundred positives, an AUROC gain of about 0.03 to 0.07 is the
    smallest detectable. Fix the main comparison in advance (logistic regression and score-level fusion); treat
    everything else as exploratory and say so.
13. **Histories are capped** at 1,000 posts and 1,000 comments per account, and deleted accounts have none.
    `history_capped` and `has_history` record this; report how many rows are affected.
14. **The graph neural network is not built yet.** With this little data it is unlikely to beat trees on
    hand-made features (GADBench found the same on real anomalies), so it comes after the simple models.

## Engineering

15. **The archive is slow** (about 55,000 to 70,000 posts an hour, with frequent retries), so collections take
    most of a day. Never run two collections at once.
16. **The live data is in Mohammed's home folder** until the current run ends; the shared folder holds a copy.
17. **`TODO.md`** in the repo lists open engineering items (for example, the archive page size).
