# Fusion: injecting the social signal into the image detectors

This is the open research problem of the project and Lazar's main task. The question: given a frozen forensic
detector that reads pixels and a model that reads the poster's history, how do we combine them so the
combination is better than the detector, and so a reviewer believes the gain is real?

## What we do now

**The detectors (M0).** FLAME (ICML 2026) and TruFor (CVPR 2023), used as released and never retrained. Each
gives an image-level score (and a localization map, which we do not use yet). The score is recalibrated on
Reddit images with a one-variable logistic regression (Platt scaling), inside the same grouped folds.

**The history model (M1).** Logistic regression on the poster-history features (see `modeling.md`).

**Late fusion (M2, confirmatory).**

```
logit p = a * logit(p_M0) + b * logit(p_M1) + c
```

Three numbers, fitted on the training folds. Read it through Bayes' rule: posterior odds = prior odds times the
likelihood ratio, which becomes a sum on the log scale. The history plays the prior ("how likely is this
account to post an edit?"), the detector plays the evidence ("what do the pixels say?"). If the two are
independent given the label, `a = b = 1` is optimal (Saerens et al. 2002 is the reference for shifting a
classifier's output by a prior). **The estimate of `b`, with its interval, is the project's main number:**
near zero means history adds nothing.

**Stacking (M2, exploratory).** XGBoost over the raw detector score and the history features together
(Wolpert 1992). It can learn interactions, at the cost of many more parameters. Always reported next to the
same model with the history columns shuffled, so extra capacity is not mistaken for information.

Both are in section 7 of `modeling.ipynb`. They need `results/m0_scores.csv`, which does not exist yet.

## Why this is not enough

1. **One number per image.** Late fusion keeps only the detector's final score and throws away the
   localization map, its confidence, and the features behind it.
2. **The independence assumption may fail.** Accounts that post memes post heavily recompressed, text-heavy
   images, and detectors react to compression. Then the detector score and the history are correlated even for
   authentic posts, and late fusion counts the same evidence twice.
3. **The detector cannot adapt to the context.** A frozen detector applies the same pixel test to every post.
   The only place an interaction can enter is stacking.
4. **Calibration is fragile.** The detectors were trained on clean photos edited by AI tools; our images are
   Reddit JPEGs at quality 75, often memes or film stills, often edited by hand. Their raw scores are badly
   calibrated here, and recalibrating spends some of the scarce positives.
5. **Missing history.** New and deleted accounts have no history; the fusion must fall back to M0 for them, and
   the paper must say how often that happens.
6. **Few positives.** Anything with more than a handful of learned parameters overfits at a few hundred
   manipulated posts. This rules out end-to-end training for now.

## Options, from cheapest to most ambitious

| # | Approach | How | Data needed | Risk |
|---|---|---|---|---|
| A | Late fusion (now) | three-parameter logistic regression on the two logits | tens of positives | assumes independence |
| B | Richer image summary | stacking over several detector outputs: score, predicted edited area, peak and mean of the localization map, TruFor's reliability map statistics, plus the history features | ~100 positives | more parameters; report against shuffled history |
| C | Difficulty-gated fusion | let the history weight depend on how hard the image is: `logit p = a*l_img + (b0 + b1*d)*l_hist + c`, where `d` is edit area, bytes per pixel or resolution. Tests whether history helps most where pixels fail (experiment E5, RQ3) | ~100 positives | the cleanest scientific question; recommended first extension |
| D | Feature-level fusion | take the detector's internal features (pooled penultimate layer), reduce them (for example PCA to 16 dimensions), concatenate with the history features, train a small model | several hundred positives | overfitting; must stay frozen |
| E | Conditioning the detector | the social embedding modulates the detector's feature maps (FiLM layers or cross-attention), so the pixel test itself changes with context | thousands of positives, fine-tuning | not feasible at our size; a paper-later idea. Synthetic edits can pretrain the image side only, never the social side |
| F | Graph-level fusion | put the detector embedding on the Image node and let a GNN (GraphSAGE, or TGN for time) pass messages to and from posts and accounts | several hundred positives | must remove each post's own pair links; see `modeling.md` |
| G | Triage | use history to decide which posts get the expensive detector, or to set a per-post threshold (experiment E6) | any | not a better classifier, but a realistic deployment story |

Recommended order: **A** (the confirmatory result), then **C** (the most interesting question), then **B**.
**D** and **F** once the dataset has several hundred positives. **E** is for the paper's future work.

## How to show the injection is reliable

A fusion result is only believable with these next to it:
- `b` (or the gain of M2 over M0) with a bootstrap interval, under grouped folds.
- The same model with history shuffled within community and month, which must fall back to M0.
- Results against matched originals and against fresh posts separately. A gain that exists only against fresh
  posts may just be "this account reposts".
- The photo-only slice (picture type `photo`), since memes dominate.
- Results by compression level, since that is where pixels fail.
- How many posts had no history, and what the model did with them.
- A calibration plot for M0 before and after recalibration.

## Lazar's first concrete steps

1. **Get the detectors running.** Download the FLAME and TruFor code and weights on the login node (compute
   nodes have no internet), then run them in a GPU job. Check the FLAME repository for released weights; if
   FLAME cannot be run, use TruFor plus CAT-Net as the second detector and tell Mohammed.
2. **Reproduce published numbers (experiment E0).** Score the TGIF test split, including its JPEG and WEBP
   variants, and compare with the papers. This proves the setup is right before any Reddit image is scored.
3. **Score our images.** Every image in `index.csv`. Write `results/m0_scores.csv` with columns `img, score`, plus
   one file per detector with the extra outputs that options B and C need (edited area, map peak and mean).
4. **Run sections 4 and 7 of the notebook** to get M0 and the late-fusion M2.
5. **Implement option C**, then B, as new cells in section 7, each with its shuffled-history control.
6. **Measure the compression effect**: rescore a sample after re-saving at JPEG quality 75 and at quality 95.
   If the detectors drop sharply, that is a central motivation for the paper.

The papers behind all of this are in `papers.md`. `docs/proposal.md` sections 6.4, 7.2 and 9 hold the full plan
and the reviewer objections it anticipates. `docs/synthetic_data_proposal.md` explains why synthetic edits can
test the detectors but cannot stand in for real posters.
