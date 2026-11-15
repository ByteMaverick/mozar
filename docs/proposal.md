# Beyond the Pixels: How Much Does Social Context Add to Image Manipulation Detection at Posting Time?

Paper proposal. Team Mozar: Mohammed Ansari, Lazar Cankovic.
Draft 2, 2026-11-14. Target: a workshop paper (4 to 8 pages).
Draft 2 was revised after an independent hostile review of Draft 1. Section 16 lists what changed and why.

> **Decisions from the team discussion on 2026-11-14 (evening). Where sections 6.1 and 12 say otherwise, these win.** The details are in the dated notes under "Step zero" in section 12; the method sections have not yet been rewritten to match.
> 1. **Source:** the archive's monthly files for all subreddits, not paging the API. The API covers only the newest weeks and small tests.
> 2. **Window:** labeled posts from 1 January to 31 October 2026; post records from July 2025 for the 180-day histories; the image pool is extended backward only if too few pairs are found.
> 3. **Communities:** 100 to 200, chosen by ranking all subreddits from the metadata and applying written exclusion rules, with a score that favors communities that exchange content. This replaces the hand-picked list of seven.
> 4. **Adult content:** sexual content is never downloaded; graphic non-sexual content is kept under the rule in section 12.
> 5. **Labels:** a vision-language model labels every edit pair first; the team hand-checks a random sample of at least 200 pairs before the paper and reports the agreement.
> 6. **Order of work:** newest two months first as a working batch, then the remaining months in the background while the history, graph and model code is written.
> 7. **Code:** one pipeline file plus one utilities file; no workflow framework.
> 8. **Compute:** the university cluster is available, so DINOv2 is used from the first pass and the detectors can run on every image.

Companion documents:
- `design.md`: project design and decisions log
- `docs/superpowers/specs/2026-11-06-dataset-construction-design.md`: how the corpus is built, stage by stage (see its revision block)
- `reports/Manipulation datasets for social graph coupling.md`: the dataset and prior-work survey
- `research_notes/`: raw notes, the feasibility probe, venue list, verified bibliography

Sections 13 and 14 hold results from background checks. Section 15 lists the assumptions this draft makes where the team has not decided yet.

---

## 0. The paper in one paragraph

Image-manipulation detectors look only at pixels, and on real platform images they are weak: the best published localizer averages 0.46 pixel-F1 on editing tools it has not seen, and detectors fall toward chance on small edits and recompressed uploads. A post, though, arrives with history. The account has posted before, and the picture itself has often been on the platform already. We ask how much that history is worth at the moment a post goes up. No existing dataset can answer this, so we build one. We find pairs of images on Reddit where one is a localized content edit of the other, two people confirm which of the two is the edit, and we take every post in general-interest communities that carries either image. Posts carrying the edit are the manipulated class. They are compared with two kinds of authentic post: posts carrying the unedited original, and ordinary posts whose image had never appeared before. With users and pictures held out, we compare three predictors: the strongest image-only detector (M0), the poster's history alone (M1), and both together (M2). We report the gain of M2 over M0 and how many manipulated posts a platform would catch by sending only the history-ranked top fraction of posts to the detector.

### Abstract draft (numbers to be filled)

> Detectors of manipulated images are trained and evaluated on pixels alone, yet the images that matter are posted by accounts with histories. We ask how much that history is worth at the moment of posting. Because no dataset pairs verified manipulation labels with real social context, we construct one from **N** pairs of Reddit images in which one image is a localized content edit of the other, with the edited image identified by two annotators. Posts carrying the edit are compared with posts carrying the unedited original and with ordinary posts of never-before-seen images, so that neither "being a repost" nor community identity can explain a result. Holding out users and pictures, we compare state-of-the-art forensic detectors (FLAME, TruFor), post-time history alone, and their fusion. **[Result: history alone reaches within-community AUROC X against both kinds of authentic post; adding it to the strongest image-only baseline raises AUROC from A to B. Or: history adds less than D AUROC.]** We also show that the manipulation label of a widely used benchmark is recoverable from metadata alone. We release post identifiers, labels, edit masks, features and code.

---

## 1. Title

**Primary (works for any outcome):**
*Beyond the Pixels: How Much Does Social Context Add to Image Manipulation Detection at Posting Time?*

Alternates, chosen once results are in:
- If H1 holds: *Who Posted It Matters: Post-Time Social Context as a Prior for Detecting Manipulated Images*
- If H2 is the strongest finding: *Context Before Pixels: Triage of Manipulated Images from Posting History Alone*
- If the result is null: *What Social Context Does Not Tell You: A Leakage-Controlled Study of Image Manipulation Detection on Reddit*

Use "AI-Manipulated" in the title only if the audit shows that most positives are generative edits (assumption A1, section 15). Otherwise say "Manipulated" and report the AI-edit slice.

---

## 2. Problem statement

**Setting.** A post is `p = (x, u, c, t)`: image `x`, poster `u`, community `c`, time `t`. Its label `y` is 1 if `x` is a localized content edit of another image, else 0. The label is a property of the image, not of when it was posted. The platform's history `H_t` is everything that happened strictly before `t`.

**The deployment moment.** The prediction is made when the post goes up. Nothing about the post's own reactions exists yet, so nothing about them may be used. Allowed inputs:
- the image itself, through a detector: `s = f(x)`
- context computed from history: `z = φ(u, x; H_t)`: the poster's past and, reported separately, whether this exact picture has been on the platform before

**Three predictors.**

| Model | Sees | Question it answers |
|---|---|---|
| M0 | `s` only | How good is the best pixel detector on real platform images? |
| M1 | `z` only | Can history alone flag a post before anyone looks at the pixels? |
| M2 | `s` and `z` | Does history add anything the pixels do not already say? |

**Hypotheses (confirmatory).**

- **H1 (complementarity).** M2 beats the strongest image-only baseline, against both kinds of authentic post.
- **H2 (early signal).** M1 beats chance and two trivial explanations (time and community alone; whether the exact image was seen before), against both kinds of authentic post.

**Questions (exploratory).**

- **RQ3 (difficulty).** Does history carry more weight on images that are intrinsically hard: small edits, heavily recompressed files, low resolution?
- **RQ4 (which history).** Poster behavior, the poster's position in the sharing network, or the picture's own past on the platform? And how far into the graph does the signal reach: the poster's own history, their position, or their neighbors?
- **RQ5 (triage).** At a realistic share of manipulated posts, how much inspection effort does ranking by history save?

**Why we expect H1 and H2 to hold.** Manipulated and synthetic media are shared very unevenly. On X during the 2024 US election, about 10% of image-sharing accounts posted 80% of the AI-generated images [SynthPol]. A detector applies one threshold to everyone. If base rates differ a lot across posters, a poster-dependent prior improves any detector that is not already near-perfect, and current detectors are far from it on platform images. The experiment tests this rather than assuming it.

**A caution we state up front.** If history only shifts the prior, its gain will automatically look largest where the detector's own score is uninformative. That pattern is expected arithmetic, not evidence that history "resolves hard images." RQ3 therefore defines difficulty by properties of the image, never by the detector's score.

**What the paper claims either way.** If H1 and H2 hold: poster history is a cheap complementary signal, with a measured size. If they do not: after controlling for repost status, labeling route and identity, history adds less than a stated margin on Reddit images. Both are results, because the question has not been asked with a modern detector and these controls.

---

## 3. Gaps in the literature

**G1. Forensic benchmarks have no social context.** TGIF, CocoGlide, MagicBrush, AutoSplice, SID-Set and the classic IMDL suite are built from COCO, OpenImages or lab photos. Their images were never posted, so there is nothing to attach. "In-the-wild" forensic sets (Deepfake-Eval-2024, So-Fake) collect images from platforms but drop the poster and the graph.

**G2. Social-context datasets do not label pixels.** FakeNewsNet, MuMiN, Twitter15/16, PHEME and FakeSV label claim or post veracity. Where images are used, they are embedded semantically (CLIP, ResNet), never forensically.

**G3. The one dataset that has both leaks its label.** Fakeddit's "Manipulated Content" class is entirely r/photoshopbattles comments, and r/photoshopbattles submissions are in the "True" class. Subreddit plus thread position reproduces the label exactly. Any graph model that sees community or author identity can score near-perfectly without learning anything about manipulation.

**G4. Nobody has asked whether context adds to a modern detector.** The only prior fusion of forensics with user features is MediaEval Verifying Multimedia Use (2015 to 2016). It asked the inverse question (do forensics help a social-feature misuse classifier), used 2015-era JPEG forensics that scored F1 0.49 on tampering, and the organizers dropped forensics as "not amenable" to Twitter media [Phan16, Boididou18]. Meta's 2026 AIGC system uses post text and OCR as context, not users or graphs, and reports no image-only versus image-plus-context ablation [MetaAIGC]. The closest work on Reddit runs an AI-image classifier over repost cascades, but it predicts virality and uses AI status as an input; it never asks whether history helps detect the image [Chauhan25].

**G5. Evaluation of social-context models is routinely leaky.** Random splits inflate rumor-detection macro-F1 by 35 to 44 points over chronological splits on Twitter15/16 [Mu23]. On Fakeddit, accuracy is 0.93 for test posts whose users were seen in training and 0.72 to 0.76 for unseen users [ColdUsers]. The released RIFT training scripts give the model a label-encoded subreddit ID under a random split, on Fakeddit's two-way label, which Fakeddit assigned by subreddit. Read as written (not yet run by us), the author ID comes out constant and the user-post edges are dropped by two naming mismatches, so the graph never reaches the model. Confirm by running the code on a sample, or with the author, before stating this in the paper.

**G6. Detectors have real headroom on platform images.** FLAME, the strongest published localizer, averages pixel-F1 0.46 and image-level accuracy 0.64 on unseen editors; on Nano Banana edits it gets 0.30 and TruFor 0.09 [FLAME]. TruFor falls from 0.83 to 0.32 pixel-F1 under JPEG Q80 on TGIF [TGIF], and to detection F1 12.6 zero-shot on GPT-4o-inpainted Reddit photos [SoFake]. Edits under 5% of the image area sit near chance [Pandolfini25]. A complementary signal has room to matter.

---

## 4. Contributions

1. **A task formulation and protocol: post-time, context-augmented manipulation detection.** Features are restricted to what a platform knows at the instant of posting. The protocol holds out users and pictures, compares against two kinds of authentic post, and includes baselines for every trivial explanation we could think of (repost status, time and community, identity, shuffled context). This is the part other groups can reuse regardless of our numbers.
2. **A corpus of verified edit pairs with their real posts.** Pairs of Reddit images where one is a localized content edit of the other, with the edited image identified by two annotators, the edit mask, and every general-community post that carried either image. To our knowledge it is the first corpus where a pixel-level manipulation label and real posting context coexist without the label being a function of the community or of a forensic detector under test. The mining and audit pipeline is released with its measured agreement against the human labels, so the corpus can be extended without hand-labeling every pair.
3. **The first controlled measurement of what poster history adds to a modern detector.** Image-only versus history-only versus fused, by kind of authentic post, by image difficulty, and by kind of history.
4. **An operational estimate for platforms.** At stated shares of manipulated posts, how many are caught when only the history-ranked top fraction is inspected.
5. **A negative control on existing data.** A short audit showing that Fakeddit's manipulation label is recoverable from metadata alone, consistent with identity leakage inflating graph-based results on it.

Released artifacts: post and comment IDs, image hashes, pair membership, labels, edit masks, audit outcomes, features, splits, and code. Images and usernames are not redistributed.

---

## 5. Related work

Each strand ends with the sentence the paper will use to position itself.

**5.1 Image manipulation detection and localization.** Classical localizers learn compression and noise inconsistencies: CAT-Net [CATNet], MVSS-Net, PSCC-Net, TruFor [TruFor], IML-ViT [IMLViT], Mesorch [Mesorch], SAFIRE [SAFIRE], standardized by IMDL-BenCo [BenCo]. The AI-edit generation adds multimodal-LLM detectors, FakeShield [FakeShield] and SIDA [SIDA], and FLAME [FLAME], a SAM 2 adapter over an energy-anomaly map. Whole-image synthetic detectors include UnivFD [UnivFD], NPR [NPR], AIDE [AIDE] and Community Forensics [CommFor]. Generalization is the open problem: unseen editors, small masks, recompression by social platforms [Wu22], and dataset shortcuts [TGIF, Pandolfini25, DFEval24, FakeOrJPEG, BFree]. *All of this work treats the image as the only evidence. We keep the detector fixed and ask what the posting context adds.*

**5.2 Datasets.** Forensic sets with masks and pairs: TGIF [TGIF], CocoGlide [TruFor], MagicBrush [MagicBrush], AutoSplice [AutoSplice], SID-Set [SIDA], GenImage [GenImage]. Sets with social context: Fakeddit [Fakeddit], PS-Battles [PSBattles], MediaEval VMU [VMU15, VMU16], MuMiN [MuMiN], FakeNewsNet [FakeNewsNet], FakeSV [FakeSV], CONVEX [CONVEX], AMMeBa [AMMeBa]. *No released dataset pairs an independently verified pixel-level label with per-post social context. We construct one.*

**5.3 Social context for misinformation detection.** Credibility from account and message features [Castillo11]; user profiles alone are predictive of who shares fake news [Shu19]. Propagation structure: false news spreads differently [Vosoughi18], exploited by Bi-GCN [BiGCN], GCAN [GCAN], FANG [FANG], UPFD [UPFD], dEFEND [dEFEND] and geometric deep learning [Monti19]. Multimodal content: EANN [EANN], MVAE [MVAE], SpotFake [SpotFake]. Text, image and graph together: KMGCN [KMGCN], MFAN [MFAN], MuMiN baselines, and RIFT [RIFT] on Reddit. *These predict veracity, treat images semantically, and mostly use signals that appear after posting. We predict a pixel-level property, use a forensic detector, and restrict features to post time.*

**5.4 Forensics combined with context.** MediaEval VMU systems fused JPEG forensics with tweet and user features for a misuse label and found forensics unhelpful [Phan16, Boididou18]. Out-of-context detection checks image-caption consistency against web evidence [NewsCLIPpings, Abdelnabi22]. Meta's AIGC detector adds post text and OCR to the image [MetaAIGC]. *None fuses a modern manipulation detector with user or repost-history signals, and none reports an image-only versus image-plus-context ablation for a pixel-level label.*

**5.5 Who shares synthetic and manipulated media.** A small share of accounts posts most AI images on X [SynthPol]; deepfake prevalence and partisanship in the 2025 Canadian election [CanElection]; engagement farming with AI images on Facebook [DiResta24]; AI-generated misinformation flagged by Community Notes [CNotesAI]. On Reddit: image resubmission across communities is common and well studied [Lakkaraju13]; AI-generated posts in art communities have been tracked through self-disclosure [Matatov24]; and repost cascades of AI-flagged images have been used to predict virality [Chauhan25]. *These studies describe who shares synthetic media and how it travels. They take the image's status as given and study spread. We ask the reverse: does what is known before posting help decide the image's status, under leakage controls.*

**5.6 Provenance and lineage.** Image phylogeny [Dias12] and provenance analysis [Moreira18] reconstruct which image was derived from which. Perceptual hashing tracks meme variants across communities [Zannettou18]. C2PA content credentials [C2PA] are stripped by most platforms. *We use near-duplicate retrieval and pixel comparison to find edit pairs, and human judgment to decide their direction.*

**5.7 Evaluation pitfalls.** Chronological splits [Mu23], including on Fakeddit itself [StepanovaRoss23], cold users [ColdUsers], unimodal bias [VERITE], shortcut learning [Geirhos20], and distant supervision in Fakeddit [Fakeddit]. *Our protocol adopts these controls and adds baselines for repost status and labeling route.*

---

## 6. Method

### 6.1 Corpus: verified edit pairs and their posts

**"Wild" communities** are large general image subreddits where nobody declares edits (starting list: r/pics, r/interestingasfuck, r/Damnthatsinteresting, r/OldSchoolCool, r/mildlyinteresting, r/funny, r/HistoryPorn; the yield test in section 12 decides which to add). The experiment runs only on posts in these communities.

1. **Ingest.** Posts and comments for the wild communities from the Arctic Shift archive (Reddit's API is closing; PRAW is not an option).
2. **Fetch and fingerprint.** Download Reddit's preview for every image; compute a perceptual hash and a DINOv2 embedding; index for nearest-neighbor search.
3. **Pair and verify.** For near-duplicate candidates, fetch full resolution, align, subtract, and classify the difference: *same* (recompression, resize, crop), *overlay* (caption bars, watermarks), *localized edit* (a compact changed region inside the content), or *global* (dropped).
4. **Audit every edit pair.** For each localized-edit pair, two annotators independently answer: which image is the edited one (first, second, cannot tell); is it a content edit and not a caption or sticker; does it look generative. Timestamps are hidden. Only pairs where both annotators agree on the direction enter the headline analysis. The label never depends on which image was posted first, so a debunk posted after a fake is handled correctly. **Automatic audit.** A vision-language model, shown both images with the changed region marked, answers the same three questions first. It is never a detector under test and never sees timestamps. It is used in two ways: on its own for a preliminary run before any hand labels exist, and as a first pass that the annotators confirm. Its agreement with the annotators is measured on a random sample of at least 200 pairs and reported, together with a check that its errors do not depend on posting order, image quality or kind of poster.
5. **Manipulated rows.** Every wild post carrying the edited image of an audited pair.
6. **Matched authentic rows.** Every wild post carrying the unedited image of an audited pair. Same pictures, so content is controlled.
7. **Fresh authentic rows.** A random sample of wild image posts whose image had no earlier copy or variant in the index when it was posted, about three per manipulated row. These stand for the ordinary original posts that make up most of a platform. They are presumed authentic; a hand-checked sample estimates how many are not.
8. **One row per author per image.** First appearances and reposts both count, for both labels.

Each row carries: label, kind of authentic post, whether an identical copy had been seen before, the pair's edit mask and area, overlay flag, and the annotators' "looks generative" answer.

**What the pipeline cannot see.** It finds edits that a pixel difference makes visible and that exceed a minimum area, and only when both images were posted in indexed communities. The smallest edits and edits whose original never reached Reddit are missing. The paper says so.

**Edit-request communities (secondary slice).** In r/photoshopbattles, r/PhotoshopRequest and r/picrequests the submission is the original and image replies are edits, so direction is known without an audit. Wild posts carrying those images form a separately reported slice. They are never pooled with the headline rows, because people who carry an edit out of such a community differ systematically from people who repost a viral original, and that difference comes from how the label was obtained. The feasibility probe found no sign that edits travel from these communities into wild ones (section 14), so this slice is expected to be small. It is optional and is not a fallback.

### 6.2 History graph

Nodes: User, Post, Image. The Image node is shared by every post that used that file. Edges: POSTED, HAS_IMAGE, COMMENTED_ON, CROSSPOSTED, SAME_AS (identical copies). All carry timestamps. Poster histories come from the archive's per-user endpoint, restricted to a trailing window.

Three things are removed before any feature is computed:
- all activity located in edit-request communities ("root-blind");
- for each row, every post that carries either image of that row's pair ("pair-blind");
- every label field: audit outcomes, edit direction, difference class, mask area. These live in the raw tables only.

The flat tables are the source of truth; the graph is a query engine built from them.

### 6.3 Post-time context features

| Family | Role | Examples |
|---|---|---|
| **P** Poster history | the social context under test (confirmatory) | account age measured from first observed activity; counts of posts and comments in the trailing 180 days; posting rate; spread across communities (entropy); share of image posts; share of prior image posts that were identical reposts of an earlier image; share that were altered variants of an earlier image, as computed automatically by step 3 |
| **S** Network structure | secondary, exploratory | from the previous month's snapshot of the user-image sharing graph: degree, PageRank, core number, local clustering |
| **N** Neighbors | secondary, exploratory; the graph-specific rung | among accounts that posted the same images as this poster before `t` (co-sharers in the user-image graph, excluding the row's pair): how many there are; their share of identical reposts; their share of altered variants, as computed automatically by step 3. Expected to be empty for many posters; the yield test reports how many have any co-sharer |
| **V** In-platform provenance | separate comparator, not counted as social context | has an identical copy of this exact image been posted in a wild community before `t`; how many times; how long ago |
| **T** Title text | content baseline | title embedding |

Not in the core study, and why:
- **Community-level statistics.** With a handful of communities, a community's statistics identify the community. Community effects are handled by averaging metrics within community.
- **Audience of the poster's earlier posts.** Requires crawling tens of thousands of commenter histories. Stretch.
- **Detector scores of historical images.** They exist only for images we chose to score, and for an authentic repost they are the detector's score on the same picture. Stretch.
- **Human labels of other posts.** Never used as features.

M1 is therefore strictly metadata: no detector output anywhere.

### 6.4 Models

**M0, image only.** FLAME and TruFor run as released over full-resolution images. **M0\*** is the strongest image-only baseline and the only one M2 is compared against: gradient-boosted trees over every image-only signal (calibrated FLAME and TruFor scores, predicted mask area and confidence), with the same learner, folds and tuning budget as the fused tree model.

**M1, history only.** Logistic regression on family P is the confirmatory model. Gradient-boosted trees [LightGBM] on P, and P plus S, are exploratory.

**M2, fusion.**
- **M2-prior (confirmatory):** `logit p = α·logit(p_M0*) + β·logit(p_M1) + γ`. Three parameters. If pixel evidence and history are conditionally independent given the label, Bayes' rule gives this form with α = β = 1: history acts as a prior that shifts the detector's odds [Saerens02].
- **M2-stack (exploratory):** gradient-boosted trees over image-only signals and P together [Wolpert92]. Always reported next to the same model with the history columns shuffled within community and month, so that extra model capacity is not mistaken for information.

All models are trained on manipulated rows against both kinds of authentic row pooled, and evaluated against each kind separately. Scores are calibrated on inner folds (Platt scaling [Platt99]).

**M3, graph model (stretch).** An inductive GraphSAGE [GraphSAGE] over the snapshot graph in place of engineered features.

### 6.5 Leakage rules

1. **Time cut and fixed window.** Features read only events in the 180 days before `t`. Rows are taken only from dates where the index already covers that window.
2. **Pair-blind.** Posts carrying either image of the row's pair are removed from families P and S. Family V is by definition about the image's own past, which is why it is reported separately and never called social context.
3. **Root-blind.** No activity in edit-request communities reaches any feature.
4. **No identities, no community statistics** in any model. The only identity models are the tripwires.
5. **Label fields never enter the feature graph.** No human labels and no detector scores describe history.
6. **Grouping.** Folds and bootstrap resampling use connected components of the graph that links authors to the pairs they posted, so no author and no pair crosses a split.
7. **Accounts.** Rows whose author is deleted are dropped. Account age comes from first observed activity, not from a profile field that later deletion would blank.

---

## 7. Experiments

### 7.1 Overview

| # | Experiment | Answers | Tier |
|---|---|---|---|
| E0 | Detector check on the TGIF test split, including recompressed variants | Do FLAME and TruFor run as published? | core |
| E1 | Fakeddit audit (one table or one paragraph) | Why can existing data not answer the question? | core |
| E2 | Main comparison against each kind of authentic post | H1, H2 | core, confirmatory |
| E3 | Trivial explanations and placebos | Is the result an artifact of how rows were chosen? | core |
| E4 | Generalization and identity checks | Is it identity or behavior? | core |
| E5 | Image difficulty | RQ3 | core, exploratory |
| E6 | Triage at fixed prevalence | RQ5 | core, exploratory |
| E7 | Survival and selection | Did deleted images bias the sample? | core |
| E8 | Which history: P versus S versus V; the hop ladder (P, then P+S, then P+S+N); new accounts | RQ4 | secondary |
| E9 | Edit-request slice; M3; audience; historical detector scores; second label source; Bluesky | Robustness beyond the core | stretch |

### 7.2 Details

**E0. Detector check.** Reproduce published image-level and pixel-level numbers for FLAME and TruFor on the TGIF test split and its JPEG and WEBP variants (CocoGlide too if time allows; it is 512 images). Output: a table matching the papers within tolerance.

**E1. Fakeddit audit.** For Fakeddit's Manipulated versus True posts, train classifiers on subreddit only, on subreddit plus whether the row is a comment, and on author ID only, under a random split and an unseen-user split. The second is near-perfect by construction, which is the point: it shows in one table how the benchmark was labeled. The paper says this is "consistent with" inflated graph results on Fakeddit; it claims "explains" only if we also rerun a RIFT-style model with and without ID features (optional).

**E2. Main comparison.** Repeated 5-fold cross-validation grouped by the components in rule 6, with inner folds for calibration and tuning. Report every model against matched authentic rows, against fresh authentic rows, and pooled.

**E3. Trivial explanations and placebos.** Each must fail to explain the result.
- *Repost status.* A table of label by "identical copy seen before," and a classifier on that one variable.
- *Time and community only.* A classifier on month and community.
- *Shuffled history.* M2 with history columns permuted within community and month. M2 must beat it, not just M0\*.
- *Sign check.* Fit M1 against each kind of authentic row separately. A feature whose coefficient changes sign between the two is reading how rows were selected and is flagged.
- *Compression shortcut.* Rescore all images after re-encoding them to one size and JPEG quality. If M0\* drops sharply, it was reading upload history, not manipulation.
- *Content.* A CLIP image-embedding probe against matched authentic rows should be near chance. If it is well above, the paper reports it and adds the probe's score to M0\*.
- *Label permutation* within community and month: everything should fall to chance.
- *Wrong time cut.* Recompute features using one week after posting, to show the inflation the protocol prevents.
- *Planted signal (added 2026-11-15).* Add an artificial effect of known size to one history feature for the manipulated rows, rerun E2, and show the pipeline recovers it. Repeat at a few sizes to find the smallest effect this corpus can detect. If the real result is null, this is what separates "no signal" from "a pipeline that could not have seen one."

**E4. Generalization and identity.** Grouped CV is primary. Leave-one-community-out and a temporal split are reported as checks. A random split is shown only to quantify inflation. Two tripwires, a classifier on raw author ID and one on raw subreddit ID, are run on the same split as the models and judged against a permutation null: they should be indistinguishable from it.

**E5. Image difficulty (RQ3).** Difficulty is defined by the image, never by the detector's score: edit area (under 5%, 5 to 20%, over 20%), bytes per pixel as a recompression proxy, and resolution. For each bin, score its manipulated rows against all authentic rows. The test is the coefficient on `logit(p_M1) × difficulty` in the fusion regression. A pure prior shift predicts zero.

**E6. Triage (RQ5).** Reweight so that manipulated posts are 1% and 5% of a stream whose background is the fresh authentic sample. Rank by M1; report the share of manipulated posts found at 5, 10 and 20% inspection budgets, as raw recall and as a fraction of the best achievable at that prevalence. Compare with random order and with ranking by V alone.

**E7. Survival and selection.** The archive keeps metadata for posts whose images are gone. Train a classifier to predict image survival from family P. If it is far from chance, rerun E2 with inverse-probability weights and report both.

**E8. Which history (secondary).** P alone, S alone, P plus S, and V alone. Rows split by the poster's prior activity: none, 1 to 9 items, 10 or more. An account with no history has no P features, so M2 falls back to M0\*; the paper reports how often that happens.

### 7.3 Baselines

| Baseline | Purpose |
|---|---|
| Prior only | floor |
| Time and community only | calendar and venue effects |
| Identical-copy-seen-before (V) | "it is just repost detection" |
| Author-ID and subreddit-ID tripwires | identity leakage, judged against a permutation null |
| FLAME, TruFor as released | what a platform gets off the shelf |
| M0\* (trees over all image-only signals, trained in-domain) | the fair image-only comparison |
| M2 with history shuffled | capacity control for the fused model |
| CLIP image probe; title-text model | content confounds |

### 7.4 Metrics and statistics

- **Primary metric.** AUROC computed within each community and averaged, under repeated grouped CV. Also AUPRC, true-positive rate at 1% and 5% false-positive rate, and calibration error.
- **Confirmatory tests: four, with Holm correction.**
  - H1 against matched authentic rows, and H1 against fresh authentic rows: AUROC(M2-prior) minus AUROC(M0\*).
  - H2 against matched, and H2 against fresh: AUROC(M1, logistic on P) minus the better of the time-and-community baseline and, for matched rows, the identical-copy baseline.
  - A hypothesis is supported only if both of its tests have intervals above zero.
- **Everything else is exploratory** and labeled that way in the paper.
- **Uncertainty.** Component-level bootstrap (rule 6) over repeated grouped CV, so that both sampling and fold assignment contribute. 95% intervals on every difference.
- **Effect-size margins are fixed after the pilot, before the full corpus is scored.** A simulation on pilot out-of-fold scores, with component resampling, gives the interval width the final sample can achieve. From it we write down the smallest gain we will call meaningful and the margin below which we will claim a null. Working value until then: 0.03 AUROC. If the final interval is wider than the null margin, the result is "inconclusive," and the paper says so.
- **Log-loss.** We report the relative reduction in held-out log-loss from M0\* to M2 at corpus prevalence. It depends on the model class and is described that way, not as a bound on information.

**Sample size, optimistic.** Smallest paired AUROC difference detectable with 80% power at the 5% level under simple assumptions (independent rows, no label noise, no refit variance). Real intervals will be wider; the pilot simulation replaces this table.

| Manipulated rows (equal authentic) | Detectable AUROC difference, at best |
|---|---|
| 150 | 0.06 to 0.09 |
| 300 | 0.04 to 0.06 |
| 500 | 0.03 to 0.05 |
| 1,000 | 0.02 to 0.03 |

Target: at least 500 manipulated rows from audited pairs. Below 300 the paper becomes a dataset-and-protocol paper with preliminary results.

### 7.5 Planned tables and figures

- Fig. 1: the deployment moment. One post, its image, and the poster's history.
- Fig. 2: the corpus pipeline with one real pair (original, edit, mask) and the two kinds of authentic post.
- Table 1: corpus statistics, including label by identical-copy-seen-before, audit agreement, share judged generative, edit-area distribution.
- Table 2: main results (E2).
- Table 3: trivial explanations and placebos (E3).
- Fig. 3: triage curves at 1% and 5% prevalence (E6).
- Fig. 4: gain by image difficulty (E5).
- Table 4: generalization and tripwires (E4); Fakeddit audit (E1).

Main results table shell:

| Model | AUROC vs matched | AUROC vs fresh | TPR@5%FPR vs fresh | Log-loss reduction vs M0\* |
|---|---|---|---|---|
| Prior only | 0.50 | 0.50 | | |
| Time and community only | | | | |
| Identical copy seen before | | | | |
| FLAME (released) | | | | |
| TruFor (released) | | | | |
| M0\* | | | | 0 |
| M1 (logistic, P) | | | | |
| M2-prior | | | | |
| M2-stack | | | | |
| M2-stack, history shuffled | | | | |

---

## 8. Outcomes and how each is written

| What we observe | What the paper says |
|---|---|
| H1 and H2 supported against both kinds of authentic post | Poster history is a complementary prior. Lead with the gain and the triage curve. |
| Supported against one kind only | The signal depends on what "authentic" is compared with. Report the sign check; do not claim a general effect. |
| M1 useful, M2 no better than M0\* | History predicts who posts edits but adds nothing once pixels are read. Lead with triage as cost saving. |
| Only V helps | The usable signal is "this picture has been here before," which is provenance, not social context. Reframe. |
| Nothing beats the trivial baselines | A controlled null within the pre-set margin, or "inconclusive" if the interval is too wide, plus E1. |
| Tripwires or placebos fail | Not a result. Find the leak. |

---

## 9. Anticipated reviewer objections

1. *"Your authentic posts are all reposts, so the model learns repost status."* Two kinds of authentic post, one of them never-seen images; a repost-status baseline; the sign check.
2. *"Earlier does not mean original."* Direction is decided by two annotators with timestamps hidden, for every pair in the headline analysis.
3. *"The label leaks through the community or the labeling route."* Headline rows come from pairs found between general communities. Edit-request communities are a separate slice and are erased from every history.
4. *"The gain is a weak baseline, or just a bigger model."* M0\* has the same learner and budget; M2 must also beat itself with history shuffled.
5. *"The detector is reading compression history."* The uniform re-encoding check.
6. *"Deleted images biased the sample."* The survival model and reweighting.
7. *"These are Photoshop jokes, not AI deception."* The annotators' generative judgment gives a slice; results are reported per community; the title follows the data. The paper does not claim to measure deceptive intent.
8. *"An adversary opens a new account."* The paper reports how many rows have no history and what happens to them.
9. *"This punishes people by association."* Intended use is triage and prior adjustment, not automatic labels; no identity or demographic features; false-positive rates reported per community.

---

## 10. Limitations and ethics

**Limitations.** One platform. Only edits whose original was also posted in indexed communities and whose difference is visible above a minimum area. Fresh authentic rows are presumed, not verified, authentic. Image survival biases the sample toward posts that were not removed; we measure and reweight but cannot remove it. Annotators can disagree on direction, and those pairs are dropped, which may remove the subtlest edits. Reddit hides voters. Intent to deceive is not observed.

**Ethics.** Public data only, no login. Poster-history aggregation needs an IRB determination, to be requested now, before the full build. Usernames are hashed with a salt and never released; images are not redistributed; a removal path is provided. The paper states plainly that history scores describe populations and must not be used to label individuals.

---

## 11. Paper outline

Eight pages plus references (four-page version in parentheses).

1. **Introduction** (1 page; 0.5). The gap between pixel detectors and where images live; the deployment moment; the question; contributions.
2. **Related work** (0.75; 0.4).
3. **Problem and protocol** (0.75; 0.4). Setting, three models, leakage rules, the two kinds of authentic post, confirmatory tests.
4. **Corpus** (1.5; 0.8). Edit pairs, audit, rows, statistics, one figure.
5. **Models** (0.5; 0.3).
6. **Experiments** (2.75; 1.3). E1 as motivation; E2; E3; then E4 to E7.
7. **Discussion, limitations, ethics** (0.5; 0.2).
8. **Conclusion** (0.25; 0.1).

Appendix: construction details, feature list, annotation guide, extra ablations, datasheet.

**Conclusion draft, positive case.** "On real Reddit images, a state-of-the-art detector leaves much undecided. What a platform already knows about the poster decides part of it, against both reposted originals and never-seen images, and after repost status, timing, community and identity are ruled out. At [π] prevalence, ranking by history alone finds [R]% of manipulated posts in the top [b]%. Manipulation detection should be evaluated where images live, with controls for how examples were chosen."

**Conclusion draft, null case.** "Once labels are independent of community, edit direction is verified, and users are held out, poster history adds less than [D] AUROC to a modern detector on Reddit images. The manipulation label of an existing benchmark is recoverable from metadata alone. We release the corpus and protocol so the question can be asked on other platforms."

---

## 12. Plan

**Work split.** Person A owns pixels: detectors, E0, the inference service, the align-and-diff routine, M0\*, the re-encoding check. Person B owns the graph: ingest, fetch, fingerprints, pairing, history, features, splits. They meet at one table keyed by image hash. The audit, E1 and E2 onward are shared.

**Schedule.** The first realistic deadline is a CVPR 2027 workshop, expected late February to mid-March 2027 (section 13). The plan also assumes a course report is due in mid-December, which needs confirming.

**Step zero: the yield test (first week).** Before building anything else, measure the two rates nobody knows.
1. Page through twelve months of posts for r/pics and r/OldSchoolCool (about 100,000 posts, about 1,000 archive calls).
2. Fetch previews for the image posts that are still up (about 40,000 images, a few hours at a polite rate).
3. Fingerprint them, find near-duplicate pairs, and run a first version of the align-and-diff step on the candidates.
4. Count: the share of image posts that have an earlier copy, the share of those pairs that are localized edits, and the number of localized-edit pairs.
5. Cross-check with the repost bot's comments, which point each flagged post at its earlier copy and can be listed by author.
6. Both team members look at every localized-edit pair found and mark "looks AI-made: yes, no, cannot tell." This gives the share of edits that appear generative, which nobody has measured, and decides whether the paper can say "AI-manipulated" (assumption A1).
7. Run the automatic audit on the same pairs and compare it with the hand marks. This is the first estimate of how much of the audit can be automated.

**Community choice for the yield test (revised 2026-11-14, Mohammed's suggestion).** Two subreddits were a cost limit that no longer applies: post records can come from the archive's monthly dump files and processing can run on the university cluster. (Correction, 2026-11-14, from the archive's download page: the monthly files hold every subreddit and run through 2026-10; the per-subreddit files cover only the top 40,000 subreddits and stop at 2023-12. All are distributed by torrent, which a university cluster may block. No single API call returns a whole subreddit: the search endpoint returns at most 100 posts per call, or 100 to 1,000 with `limit=auto`.) The test should also cover communities where a manipulated image is likely to be passed off as real, because that is the paper's motivating case. Candidates to add to r/pics and r/OldSchoolCool: r/interestingasfuck (already on the wild list), r/conspiracy, r/UFOs, and one political community with user-uploaded images. Not yet measured for any of the new ones: monthly image-post volume, whether the community is link-only, and how much of it is captioned memes (which the pipeline files as overlays, not edits). Check these with the archive's monthly counts before committing. Precedent for choosing such communities: [Chauhan25] used r/conspiracy, r/politics, r/conservative and r/propagandaposters. Community identity is still never a feature, and metrics are still averaged within community.

**Wider pool, chosen by rule (Mohammed, 2026-11-14; under discussion).** Do not hand-pick communities at all. Use the dump metadata for every subreddit to rank safe-for-work communities by number of image posts, drop edit-request and AI-art communities, fix an image budget (working figure: 1 to 2 million thumbnails), and take communities from the top of the ranking until the budget is filled. Pairs can then span communities. All of Reddit is out: it is too large to download politely, and an unfiltered crawl would pull in adult and possibly illegal images. First job, before any image is fetched: count image posts per community from the dumps to see how many communities fit the budget. None of these counts has been measured yet.

Notes from a search on 2026-11-14. (1) No recent public dataset ships Reddit image files at scale: RedCaps stops in 2020 and is links only; OP-Reddit-Image is drug-use posts under restricted access; Fakeddit stops in 2019. Recent sets that do ship Reddit images are small and built for one purpose each (found by search, details not yet verified): RealEdit (CVPR 2025; about 151,000 images of real edit requests and their edits, posts from 2012 to 2021), So-Fake-OOD (2025; about 100,000 curated Reddit source images), Reddit-V (RANLP 2025; about 27,000 posts with images and pre-engagement metadata, for virality prediction), S-HArM (2025; AI-focused subreddits). Leads: RealEdit as a second answer key for testing the pairing and direction steps; Reddit-V and "Dataset and Case Studies for Visual Near-Duplicates Detection in the Context of Social Media" (arXiv 2203.07167) for related work. Other Reddit datasets are slices of the same archive, so combining several adds duplicates and gaps, not coverage. (2) The archive's original bulk files are the source to use. A Parquet copy on Hugging Face (`open-index/arctic`, December 2005 to February 2026, 2.8 billion submissions, about 330 GB) is convenient but its schema omits removal status, preview links and crosspost parent, which the pipeline needs. (3) Poster histories can be cut from the same bulk files, which removes the per-author API lookups and their rate limit. (4) Adult-content images are not downloaded: an unfiltered crawl risks sexual images of minors, and edit pairs found there would be real people's photos next to sexualized fakes of them. Adult-content post records are kept as metadata, so history features such as "share of this account's posts flagged adult" remain available. The paper names sexualized fakes as an important case it does not cover. Refinement (Mohammed, 2026-11-14): "not safe for work" is one yes/no flag that mixes sexual content with graphic news, conflict and medical images, and the second group matters for misinformation. Rule: (a) flagged posts inside communities that are not adult-only are kept; (b) adult-only communities, identified by nearly all of their posts carrying the flag, are excluded unless hand-approved onto an allow-list of non-sexual ones (conflict, news, medical); (c) every downloaded image passes a local sexual-content classifier and is deleted on a hit before anyone views or stores it. The ethics request must say that annotators will see graphic non-sexual images.

**Time window and community list (Mohammed, 2026-11-14; working decision).** Labeled posts come from 1 January to 31 October 2026, the period in which AI editing tools were in wide use, which also raises the chance that the positive class can honestly be called AI-manipulated. Post records are taken from July 2025 so that every labeled post has its 180 days of poster history. The image pool searched for earlier copies starts with the same ten months; if the yield is low it is extended backward, because an image edited in 2026 can have an original posted years earlier. Communities: first rank all subreddits by image posts in the window from the monthly files, then curate from that ranking with written exclusion rules fixed before any result is seen (adult-only communities not on the allow-list, edit-request, AI-art, caption-meme, screenshot and drawing communities). The ranking and the exclusions go in an appendix. Target: 100 to 200 communities. Selection can favor communities where pairs are likely, using metadata only (Mohammed's idea, 2026-11-14): build a subreddit-to-subreddit graph from crossposts, reuse of the same image link, reuse of the same title, and posters shared between communities, and score each candidate by its surviving image posts times how much content it exchanges with other candidates. These signals find where pictures travel; whether edited copies follow the same routes is unmeasured. The score uses no labels and no image content, and the paper states that the corpus over-represents content that travels.

**What to save so nothing has to be fetched twice (2026-11-14).** The archive is static and can be re-read at any time; images on Reddit's servers are perishable, because a post deleted next month loses its image. So: (a) keep the complete raw record of every image post, never a trimmed selection of fields (the API's `fields` option cannot return preview links, gallery contents or removal status, so it is not used); (b) keep the image file itself, not only its fingerprint, with a download log (time, status, final URL, size, dimensions, checksum); (c) for gallery posts keep every image with its position; (d) fetch full-size copies for candidate pairs and sampled negatives as soon as pairing is done; (e) snapshot subreddit rules and sizes once. Comments and poster histories can be cut from the archive later. From the API documentation: rate limits are dynamic with no fixed quota, a few requests per second is acceptable for light use, HTTP 429 carries `X-RateLimit-Reset`, and the documentation asks that large jobs use the monthly dumps. Scores are 0 or 1 when first archived and are updated after about 36 hours. Lead: `/api/users/interactions/users` returns who an account has exchanged comments with inside a time window, which is the audience family at one call per poster (it can time out for very active accounts).

Working thresholds, to be confirmed by the team: 50 or more localized-edit pairs from this slice means the full corpus (more communities, three years) should reach the target, so go. Between 15 and 50, widen first: add communities where edited pictures are common, extend the window to three years (posts that are still up keep their images, so an older window costs fetch time, not survival), and allow the original to sit in any indexed community. Below 15, switch to the reduced paper described under the gate.

| When | Person A | Person B | Shared output |
|---|---|---|---|
| Week 1 | FLAME and TruFor running; E0; first align-and-diff | Yield test: ingest, fetch, fingerprints, candidate pairs for two subreddits | Yield numbers; E1; IRB request filed |
| Week 2 | Align-and-diff hardened | Widen to the pilot communities; verified edit pairs | Audit of pilot pairs; pilot gate |
| Weeks 3 to 4 | Score pilot rows; M0\* | Histories and P features for pilot rows | Preliminary E2 and E3; pilot simulation fixes margins; course report |
| Weeks 5 to 8 | Score full corpus | Scale to the full window; fresh sample | Full audit; E2 to E7 |
| Weeks 9 to 10 | Figures | Release packaging; E8 if time | Draft |
| Weeks 11 to 12 | | | Internal review, revision, submission |

**Pilot gate (end of week 2).** Go ahead with the full study only if: at least about 300 manipulated rows come from pairs where both annotators agree on direction, or the count clearly scales to that with the full window; images are retrievable for most rows; and the tripwires look like the permutation null.

**If the corpus stays small.** The probe says this is a real possibility. The paper then becomes a four-page corpus-and-protocol paper: contributions 1, 2 and 5, the detector results on real edit pairs, and the three-way comparison reported with its honest, wide interval. That is still a workshop paper, and the corpus can grow afterwards. A second platform (the Bluesky labeler in section 14) is the route to more data, at the price of weaker labels.

**Hand-labeling budget.** Every headline pair is judged by both people. At roughly half a minute per pair, 600 pairs is about five hours each. This replaces the sampled audit in Draft 1 and is the best use of the time freed by the cuts below.

**Cut from the core, in this order if time runs short.** The stretch items in E9; family S; E8; the temporal split; CocoGlide; the optional RIFT rerun.

**Compute.** Detectors run only on labeled rows, a few thousand images, well within one GPU session. Fingerprinting previews for the wild communities is the largest job. The full corpus will be a few times the pilot, not the full list times three years; the fetch rate decides how far it goes.

---

## 13. Target venues

Source: `research_notes/workshop_venues_2027.md` (27 venues with links). Most 2027 workshop lists are not announced yet, so the best fits rest on 2026 dates. "Confirmed" means the 2027 call is posted.

**Recommended, in order.**

1. **A CVPR 2027 forensics workshop** (Seattle, June 20-21, 2027). Candidates, based on 2026: SAFE, APAI, PP-MisDet. Expected deadline late February to mid-March (2026: Feb 27 to Mar 13). Eight pages in CVPR style; SAFE also ran a 2 to 4 page non-archival track. The workshop list is due Dec 22, 2026. Best audience for the detector comparison and the corpus.
2. **An ICWSM 2027 workshop** (Edinburgh). Candidates: MisD, CySoc. Expected deadline late March to early April. CySoc accepted non-archival two-page abstracts in 2026. Workshop proposals are due Jan 15, 2027, so neither is confirmed. Same timing, best single topical match: **MAD, Multimedia AI against Disinformation, at ICMR 2027** (Singapore, June 7-10; 2026 deadline Mar 25; decisions on workshops Jan 2, 2027).
3. **A KDD 2027 workshop** (San Jose, Aug 1-5, 2027), for example Integrity in Social Networks and Media. Expected around May; took 2 to 4 page short papers in 2026. The safety net if experiments slip. Dated fallback: ASONAM 2027 workshops, June 7, 2027, Athens (confirmed).

**Other dated options.**

| Deadline | Venue | Note |
|---|---|---|
| Jan 15, 2027 (confirmed) | ICWSM 2027 final round, including dataset papers | too early for results; a dataset paper needs the finished corpus |
| Feb 15, 2027 (confirmed) | ACM IH&MMSec 2027, Pittsburgh | archival forensics venue; needs results by early February; stretch |
| about Apr 1 (2026 date) | ACM Multimedia 2027 dataset track | a later home for the corpus |
| about May (2026 date) | NeurIPS 2027 Evaluations and Datasets track | corpus plus protocol; high bar |

**Things to know.**
- The CVPR Workshop on Media Forensics has not run since 2024. Do not plan around it.
- CVPR treats a workshop paper longer than four pages as a publication. A short non-archival version keeps the option of a later full paper.
- ACM venues charge an open-access fee in 2027 unless the university is in ACM Open. The Web Conference requires a full registration per paper.
- Deadlines already passed or too close: the AAAI-27 workshops and The Web Conference 2027 short papers.

**What this means for the schedule.** The twelve-week plan in section 12 ends in early February. That leaves a few weeks of margin before a CVPR workshop deadline. Plan a four-page version first and extend it to eight pages if the full results are in. Check the CVPR workshop list on Dec 22 and the ICMR list on Jan 2.

---

## 14. Feasibility evidence

Source: `research_notes/feasibility_probe_2026-11-14.md`. A read-only probe on 2026-11-14: 384 requests to the Arctic Shift archive and to Reddit's image servers. Counts are measured; image shares and yearly totals are estimated from samples of 100 to 300 posts.

**What works.**
- **The archive.** No key needed, current to the minute. Dependable: time-ordered listings (100 rows per call), lookups by post ID, URL and author, and monthly counts. Not dependable on large subreddits: keyword, title and flair search, which time out. So: page through posts by time, pull poster histories by author lookup, and use the dump files for anything that needs full-text search.
- **Volume is not the constraint.** The eight candidate wild subreddits had 481,100 posts in the last twelve months, about 305,000 of them image posts.

| Wild subreddit | Posts, Oct 2026 | Image share | Est. image posts per month |
|---|---|---|---|
| r/pics | 6,613 | 91% | 6,040 |
| r/mildlyinteresting | 4,843 | 95% | 4,620 |
| r/funny | 4,820 | 43% | 2,070 |
| r/interestingasfuck | 4,328 | 39% | 1,690 |
| r/OldSchoolCool | 2,047 | 74% | 1,510 |
| r/Damnthatsinteresting | 1,952 | 33% | 640 |
| r/HistoryPorn | 574 | 92% | 530 |
| r/nextfuckinglevel | 1,116 | 2% | 20 |

- **Images survive if the post is still up.** 89 of 90 checked, including posts from 2023. Images of posts deleted by their author are gone (0 of 16). Images of moderator-removed posts survive about half the time (21 of 36).
- **Many posts are removed.** Of 886 sampled image posts from October 2026, 43% were still up, 44% were moderator-removed, 7% removed by Reddit, and 6% deleted by the author. That leaves roughly 117,000 image posts a year still up across the eight subreddits, plus perhaps half of the moderator-removed ones.

**What is uncertain: how many edit pairs exist.** This is the number the whole study depends on, and the probe could not measure it without downloading and comparing images.
- Exact-URL reposts between wild subreddits: 0 of 274 sampled r/pics image posts. This badly undercounts, because reposts are usually re-uploads with a new URL.
- A repost-detection bot flagged about 15% of r/OldSchoolCool image posts, from only four events (plausible range 6 to 37%).
- Nobody has measured what share of reposts are localized edits and not plain copies.
- The probe's inferred range for manipulated wild posts from pairs between the eight subreddits is **about 6 to 700 a year**, with low hundreds the most defensible single figure. It assumes 2 to 10% of image posts have an earlier copy and 0.5 to 5% of those are localized edits. Neither assumption is measured. Our target is 500.

**Edits do not seem to travel from edit-request communities into wild ones.** None of 38 wild crossposts had a parent in an edit-request community; none of 6 resolved crossposts out of those communities went to a wild subreddit; none of 9 edit image URLs was ever submitted as a post; none of 12 requesters posted an image in a wild subreddit within 30 days. The samples are small, so this is a loose bound, not proof of zero. But the edit-request slice should be expected to yield few rows and cannot serve as a fallback.

**Other findings that change the plan.**
- **Moderator removals are not a usable label for edits.** r/pics explicitly allows manipulated images and bans AI-generated ones, and in the three subreddits checked the AI rule is bundled with a screenshot rule.
- **r/nextfuckinglevel is now almost all video** and is dropped from the list.
- **A second platform candidate exists.** Bluesky has a public community-run labeler, "AI Imagery Labeler," with labels for suspected AI imagery and suspected AI-modified imagery, on a platform where likes, reposts and follows are public. Bulk retrieval of its labels is unconfirmed, and its labels are weaker than pixel comparison because they depend on what people chose to report. Stretch only.

**Consequence.** Section 12 now starts with a short yield test that measures the two unknown rates before anything else is built.

---

## 15. Assumptions in this draft, and decisions still open

Assumptions made so the proposal is complete. Each is the team's to overturn.

- **A1. Positive class.** Any localized content edit, whatever the tool. The AI-edit slice is reported using the annotators' judgment. Reason: pixel comparison finds edits, not tools, and a platform wants doctored images flagged either way.
- **A2. Compute.** One GPU session and a laptop. Hence detectors run only on labeled rows.
- **A3. Network structure (family S) is kept as a secondary analysis** because it is the course's subject and the team's original interest, but it is outside the confirmatory tests.
- **A4. Fully generated images and restorations are out of scope.** AI-art communities and r/estoration are not used.
- **A5. Second label source and second platform are stretch goals.**

Still open:
- Course deadline, and what the course deliverable must contain.
- The yield-test thresholds (50 and 15 localized-edit pairs) and what to do in the middle band.
- Final community list and time window (after the yield test).
- Whether a small-corpus, four-page paper is an acceptable outcome for the course and for you.
- Automatic audit (proposed by Mohammed, 2026-11-14, adopted in this draft): automatic labels first, to show the pairs and the signal exist; hand labels before the paper. Still open: whether every headline pair is hand-confirmed (recommended while the corpus is under about 1,000 pairs) or only a validation sample of at least 200.
- IRB determination: who asks the advisor. This should happen this week.
- FLAME's license is not stated in its repository; check before releasing anything derived from it.
- Venue choice: shortlist in section 13; decide once the CVPR and ICMR workshop lists are out (Dec 22 and Jan 2).

---

## 16. What the independent review changed

Draft 1 was given to a reviewer instructed to find reasons to reject. The verdict on Draft 1 was reject. The table records each point and the response. All ten were accepted in substance.

| # | Problem found in Draft 1 | Change in Draft 2 |
|---|---|---|
| 1 | Every authentic row was a repost and most manipulated rows were not, so "is this a repost" predicted the label from both pixels and history. Triage numbers were meaningless because prevalence came from sampling. | A second kind of authentic row: never-seen images. Both hypotheses must hold against each kind. Repost-status baseline, sign check, re-encoding check. Triage at stated prevalence. |
| 2 | Rows anchored in edit-request communities made the labeling route equal the label and brought edit-community activity into poster histories: Fakeddit's leak, moved to the poster. | Headline rows come only from pairs found between general communities. Edit-request communities are a separate slice and are erased from all histories. |
| 3 | "Earliest copy is the original" decided the label. A debunk posted after a fake would be labeled the wrong way round. | Two annotators decide direction for every headline pair, timestamps hidden. The label is a property of the image. |
| 4 | The provenance family contradicted the rule that removes a row's own lineage from history; several features encoded the label or the detector's score on the same picture. | Provenance is counts of identical copies only, reported separately and not called social context. No detector scores, human labels or edit attributes in any feature. |
| 5 | Decision rules could not return their own outcomes: the null band was narrower than the achievable interval; the triage threshold was impossible at balanced classes; "M2" was eight models. | One confirmatory model per hypothesis, four tests, Holm. Margins fixed from a pilot simulation. Triage reported relative to its ceiling at stated prevalence. |
| 6 | "Gain is largest where the detector is uncertain" is true by arithmetic under a pure prior shift. | Difficulty is defined by the image (edit area, recompression, resolution) and tested as an interaction term. |
| 7 | The image-only baseline had less capacity than the fused model; "bits of information" was not a bound. | Same learner and budget for M0\*; shuffled-history control; log-loss reported as a model-dependent reduction. |
| 8 | Features reflected what the archive holds in 2026; survival was selected on label and context. | Survival model with reweighting; fixed trailing window; account age from first activity; deleted authors dropped; time-and-community baseline. |
| 9 | Overclaims: "independent of any detector," "explains" RIFT's results, a mechanism claim that sample size could not support, community history inseparable from community identity. | Claims reworded; mechanism question dropped; community statistics removed; root list reconciled; tripwires judged against a permutation null. |
| 10 | Scope did not fit twelve weeks. | Audience features, historical detector scores, the graph model and second sources moved to stretch; structure and cold-start made secondary; time reinvested in the full audit and the fresh sample. |

One point where this draft goes less far than the reviewer asked: the reviewer would cut network-structure features entirely. They stay as a secondary analysis (assumption A3).

---

## 17. References, grouped by role

Checked on 2026-11-14 against primary records (arXiv, DOI, CVF, ACL Anthology, proceedings pages). Full entries with status notes are in `bibliography.md`. Caveats: items shown as arXiv-only may have a recent acceptance the check did not find; So-Fake's author list changed between arXiv versions; [CNotesAI] changed its sample between versions, so any figure quoted from it must be rechecked against version 2. CocoGlide has no separate reference and is cited through [TruFor].

**Detectors and forensic benchmarks**
- [TruFor] Fabrizio Guillaro, Davide Cozzolino, Avneesh Sud, Nicholas Dufour, Luisa Verdoliva. TruFor: Leveraging All-Round Clues for Trustworthy Image Forgery Detection and Localization. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 20606–20615, 2023. https://openaccess.thecvf.com/content/CVPR2023/html/Guillaro_TruFor_Leveraging_All-Round_Clues_for_Trustworthy_Image_Forgery_Detection_and_CVPR_2023_paper.html
- [CATNet] Myung-Joon Kwon, Seung-Hun Nam, In-Jae Yu, Heung-Kyu Lee, Changick Kim. Learning JPEG Compression Artifacts for Image Manipulation Detection and Localization. International Journal of Computer Vision 130(8):1875–1895, 2022. https://doi.org/10.1007/s11263-022-01617-5
- [IMLViT] Xiaochen Ma, Bo Du, Zhuohang Jiang, Xia Du, Ahmed Y. Al Hammadi, Jizhe Zhou. IML-ViT: Benchmarking Image Manipulation Localization by Vision Transformer. arXiv:2307.14863, 2023 (v4, November 2024). https://arxiv.org/abs/2307.14863
- [BenCo] Xiaochen Ma, Xuekang Zhu, Lei Su, et al. IMDL-BenCo: A Comprehensive Benchmark and Codebase for Image Manipulation Detection & Localization. Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Datasets and Benchmarks Track, pp. 134591–134613, 2024. https://proceedings.neurips.cc/paper_files/paper/2024/hash/f280a398c243b5fdaa09f57ece880fc9-Abstract-Datasets_and_Benchmarks_Track.html
- [Mesorch] Xuekang Zhu, Xiaochen Ma, Lei Su, et al. Mesoscopic Insights: Orchestrating Multi-Scale & Hybrid Architecture for Image Manipulation Localization. Proceedings of the AAAI Conference on Artificial Intelligence 39(10):11022–11030, 2025. https://doi.org/10.1609/aaai.v39i10.33198
- [SAFIRE] Myung-Joon Kwon, Wonjun Lee, Seung-Hun Nam, Minji Son, Changick Kim. SAFIRE: Segment Any Forged Image Region. Proceedings of the AAAI Conference on Artificial Intelligence 39(4):4437–4445, 2025. https://doi.org/10.1609/aaai.v39i4.32467
- [FakeShield] Zhipei Xu, Xuanyu Zhang, Runyi Li, Zecheng Tang, Qing Huang, Jian Zhang. FakeShield: Explainable Image Forgery Detection and Localization via Multi-modal Large Language Models. International Conference on Learning Representations (ICLR), 2025. https://openreview.net/forum?id=pAQzEY7M03
- [SIDA] Zhenglin Huang, Jinwei Hu, Xiangtai Li, et al. SIDA: Social Media Image Deepfake Detection, Localization and Explanation with Large Multimodal Model. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 28831–28841, 2025. https://openaccess.thecvf.com/content/CVPR2025/html/Huang_SIDA_Social_Media_Image_Deepfake_Detection_Localization_and_Explanation_with_CVPR_2025_paper.html
- [FLAME] Yiming Wang, Baiqi Wu, Qingming Li, Jiahao Chen, Tong Zhang, Shouling Ji. Order within Chaos: Capturing Intrinsic Energy Anomalies for AI-Manipulated Image Forgery Localization. Proceedings of the 43rd International Conference on Machine Learning (ICML), PMLR 306:131220–131246, 2026. https://proceedings.mlr.press/v306/wang26iy.html
- [UnivFD] Utkarsh Ojha, Yuheng Li, Yong Jae Lee. Towards Universal Fake Image Detectors That Generalize Across Generative Models. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 24480–24489, 2023. https://openaccess.thecvf.com/content/CVPR2023/html/Ojha_Towards_Universal_Fake_Image_Detectors_That_Generalize_Across_Generative_Models_CVPR_2023_paper.html
- [NPR] Chuangchuang Tan, Yao Zhao, Shikui Wei, Guanghua Gu, Ping Liu, Yunchao Wei. Rethinking the Up-Sampling Operations in CNN-based Generative Network for Generalizable Deepfake Detection. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 28130–28139, 2024. https://openaccess.thecvf.com/content/CVPR2024/html/Tan_Rethinking_the_Up-Sampling_Operations_in_CNN-based_Generative_Network_for_Generalizable_CVPR_2024_paper.html
- [AIDE] Shilin Yan, Ouxiang Li, Jiayin Cai, et al. A Sanity Check for AI-generated Image Detection. International Conference on Learning Representations (ICLR), 2025. https://openreview.net/forum?id=ODRHZrkOQM
- [CommFor] Jeongsoo Park, Andrew Owens. Community Forensics: Using Thousands of Generators to Train Fake Image Detectors. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 8245–8257, 2025. https://openaccess.thecvf.com/content/CVPR2025/html/Park_Community_Forensics_Using_Thousands_of_Generators_to_Train_Fake_Image_CVPR_2025_paper.html
- [BFree] Fabrizio Guillaro, Giada Zingarini, Ben Usman, Avneesh Sud, Davide Cozzolino, Luisa Verdoliva. A Bias-Free Training Paradigm for More General AI-generated Image Detection. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 18685–18694, 2025. https://openaccess.thecvf.com/content/CVPR2025/html/Guillaro_A_Bias-Free_Training_Paradigm_for_More_General_AI-generated_Image_Detection_CVPR_2025_paper.html
- [FakeOrJPEG] Patrick Grommelt, Louis Weiss, Franz-Josef Pfreundt, Janis Keuper. Fake or JPEG? Revealing Common Biases in Generated Image Detection Datasets. Computer Vision – ECCV 2024 Workshops, Part XXII, Lecture Notes in Computer Science, Springer, pp. 80–95, 2025. https://doi.org/10.1007/978-3-031-92089-9_6
- [Wang20] Sheng-Yu Wang, Oliver Wang, Richard Zhang, Andrew Owens, Alexei A. Efros. CNN-Generated Images Are Surprisingly Easy to Spot... for Now. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 8695–8704, 2020. https://openaccess.thecvf.com/content_CVPR_2020/html/Wang_CNN-Generated_Images_Are_Surprisingly_Easy_to_Spot..._for_Now_CVPR_2020_paper.html
- [Wu22] Haiwei Wu, Jiantao Zhou, Jinyu Tian, Jun Liu. Robust Image Forgery Detection Over Online Social Network Shared Images. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 13440–13449, 2022. https://openaccess.thecvf.com/content/CVPR2022/html/Wu_Robust_Image_Forgery_Detection_Over_Online_Social_Network_Shared_Images_CVPR_2022_paper.html
- [TGIF] Hannes Mareen, Dimitrios Karageorgiou, Glenn Van Wallendael, Peter Lambert, Symeon Papadopoulos. TGIF: Text-Guided Inpainting Forgery Dataset. 2024 IEEE International Workshop on Information Forensics and Security (WIFS), pp. 1–6, 2024. https://doi.org/10.1109/WIFS61860.2024.10810690
- [TGIF2] Hannes Mareen, Dimitrios Karageorgiou, Paschalis Giakoumoglou, Peter Lambert, Symeon Papadopoulos, Glenn Van Wallendael. TGIF2: Extended Text-Guided Inpainting Forgery Dataset and Benchmark. Journal on Information Security (Springer) 2026, article 13, 2026. https://doi.org/10.1186/s13635-026-00235-9
- [MagicBrush] Kai Zhang, Lingbo Mo, Wenhu Chen, Huan Sun, Yu Su. MagicBrush: A Manually Annotated Dataset for Instruction-Guided Image Editing. Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track, pp. 31428–31449, 2023. https://proceedings.neurips.cc/paper_files/paper/2023/hash/64008fa30cba9b4d1ab1bd3bd3d57d61-Abstract-Datasets_and_Benchmarks.html
- [AutoSplice] Shan Jia, Mingzhen Huang, Zhou Zhou, Yan Ju, Jialing Cai, Siwei Lyu. AutoSplice: A Text-prompt Manipulated Image Dataset for Media Forensics. IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW), Workshop on Media Forensics, pp. 893–903, 2023. https://openaccess.thecvf.com/content/CVPR2023W/WMF/html/Jia_AutoSplice_A_Text-Prompt_Manipulated_Image_Dataset_for_Media_Forensics_CVPRW_2023_paper.html
- [GenImage] Mingjian Zhu, Hanting Chen, Qiangyu Yan, et al. GenImage: A Million-Scale Benchmark for Detecting AI-Generated Image. Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track, pp. 77771–77782, 2023. https://proceedings.neurips.cc/paper_files/paper/2023/hash/f4d4a021f9051a6c18183b059117e8b5-Abstract-Datasets_and_Benchmarks.html
- [Pandolfini25] Serafino Pandolfini, Lorenzo Pellegrini, Matteo Ferrara, Davide Maltoni. Detecting Localized Deepfakes: How Well Do Synthetic Image Detectors Handle Inpainting? arXiv:2512.16688, 2025. https://arxiv.org/abs/2512.16688
- [SoFake] Zhenglin Huang, Xiangtai Li, Xi Yang, et al. So-Fake: Benchmarking and Explaining Social Media Image Forgery Detection. arXiv:2505.18660, 2025 (v5, July 2026). https://arxiv.org/abs/2505.18660
- [DFEval24] Nuria Alina Chandra, Hannah Lee, Ryan Murtfeldt, et al. Deepfake-Eval-2024: A Multi-Modal In-the-Wild Benchmark of Deepfakes Circulated in 2024. arXiv:2503.02857, 2025 (v5, May 2026). https://arxiv.org/abs/2503.02857
- [OpenFake] Victor Livernoche, Akshatha Arodi, Andreea Musulan, et al. OpenFake: An Open Dataset and Platform Toward Real-World Deepfake Detection. arXiv:2509.09495, 2025. https://arxiv.org/abs/2509.09495

**Datasets with social context**
- [Fakeddit] Kai Nakamura, Sharon Levy, William Yang Wang. Fakeddit: A New Multimodal Benchmark Dataset for Fine-grained Fake News Detection. Proceedings of the Twelfth Language Resources and Evaluation Conference (LREC), pp. 6149–6157, 2020. https://aclanthology.org/2020.lrec-1.755/
- [PSBattles] Silvan Heller, Luca Rossetto, Heiko Schuldt. The PS-Battles Dataset - an Image Collection for Image Manipulation Detection. arXiv:1804.04866, 2018. https://arxiv.org/abs/1804.04866
- [VMU15] Christina Boididou, Katerina Andreadou, Symeon Papadopoulos, et al. Verifying Multimedia Use at MediaEval 2015. Working Notes Proceedings of the MediaEval 2015 Workshop, CEUR Workshop Proceedings Vol-1436, 2015. https://ceur-ws.org/Vol-1436/Paper4.pdf
- [VMU16] Christina Boididou, Symeon Papadopoulos, Duc-Tien Dang-Nguyen, et al. Verifying Multimedia Use at MediaEval 2016. Working Notes Proceedings of the MediaEval 2016 Workshop, CEUR Workshop Proceedings Vol-1739, 2016. https://ceur-ws.org/Vol-1739/MediaEval_2016_paper_3.pdf
- [MuMiN] Dan Saattrup Nielsen, Ryan McConville. MuMiN: A Large-Scale Multilingual Multimodal Fact-Checked Misinformation Social Network Dataset. Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR), pp. 3141–3153, 2022. https://doi.org/10.1145/3477495.3531744
- [FakeNewsNet] Kai Shu, Deepak Mahudeswaran, Suhang Wang, Dongwon Lee, Huan Liu. FakeNewsNet: A Data Repository with News Content, Social Context, and Spatiotemporal Information for Studying Fake News on Social Media. Big Data 8(3):171–188, 2020. https://doi.org/10.1089/big.2020.0062
- [FakeSV] Peng Qi, Yuyan Bu, Juan Cao, et al. FakeSV: A Multimodal Benchmark with Rich Social Context for Fake News Detection on Short Video Platforms. Proceedings of the AAAI Conference on Artificial Intelligence 37(12):14444–14452, 2023. https://doi.org/10.1609/aaai.v37i12.26689
- [CONVEX] Zacharias Chrysidis, Stefanos-Iordanis Papadopoulos, Symeon Papadopoulos. The Synthetic Media Shift: Tracking the Rise, Virality, and Detectability of AI-Generated Multimodal Misinformation. IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW), 3rd Workshop on New Trends in AI-Generated Media and Security (AIMS), pp. 8626–8635, 2026. https://openaccess.thecvf.com/content/CVPR2026W/AIMS/html/Chrysidis_The_Synthetic_Media_Shift_Tracking_the_Rise_Virality_and_Detectability_CVPRW_2026_paper.html
- [AMMeBa] Nicholas Dufour, Arkanath Pathak, Pouya Samangouei, et al. AMMeBa: A Large-Scale Survey and Dataset of Media-Based Misinformation In-The-Wild. arXiv:2405.11697, 2024. https://arxiv.org/abs/2405.11697

**Social context and graphs for misinformation**
- [Castillo11] Carlos Castillo, Marcelo Mendoza, Barbara Poblete. Information credibility on Twitter. Proceedings of the 20th International Conference on World Wide Web (WWW), pp. 675–684, 2011. https://doi.org/10.1145/1963405.1963500
- [Shu19] Kai Shu, Xinyi Zhou, Suhang Wang, Reza Zafarani, Huan Liu. The Role of User Profiles for Fake News Detection. Proceedings of the 2019 IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining (ASONAM), pp. 436–439, 2019. https://doi.org/10.1145/3341161.3342927
- [Vosoughi18] Soroush Vosoughi, Deb Roy, Sinan Aral. The spread of true and false news online. Science 359(6380):1146–1151, 2018. https://doi.org/10.1126/science.aap9559
- [Friggeri14] Adrien Friggeri, Lada A. Adamic, Dean Eckles, Justin Cheng. Rumor Cascades. Proceedings of the International AAAI Conference on Web and Social Media (ICWSM) 8(1):101–110, 2014. https://doi.org/10.1609/icwsm.v8i1.14559
- [Ma17] Jing Ma, Wei Gao, Kam-Fai Wong. Detect Rumors in Microblog Posts Using Propagation Structure via Kernel Learning. Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pp. 708–717, 2017. https://aclanthology.org/P17-1066/
- [BiGCN] Tian Bian, Xi Xiao, Tingyang Xu, et al. Rumor Detection on Social Media with Bi-Directional Graph Convolutional Networks. Proceedings of the AAAI Conference on Artificial Intelligence 34(01):549–556, 2020. https://doi.org/10.1609/aaai.v34i01.5393
- [GCAN] Yi-Ju Lu, Cheng-Te Li. GCAN: Graph-aware Co-Attention Networks for Explainable Fake News Detection on Social Media. Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL), pp. 505–514, 2020. https://aclanthology.org/2020.acl-main.48/
- [FANG] Van-Hoang Nguyen, Kazunari Sugiyama, Preslav Nakov, Min-Yen Kan. FANG: Leveraging Social Context for Fake News Detection Using Graph Representation. Proceedings of the 29th ACM International Conference on Information & Knowledge Management (CIKM), pp. 1165–1174, 2020. https://doi.org/10.1145/3340531.3412046
- [UPFD] Yingtong Dou, Kai Shu, Congying Xia, Philip S. Yu, Lichao Sun. User Preference-aware Fake News Detection. Proceedings of the 44th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR), pp. 2051–2055, 2021. https://doi.org/10.1145/3404835.3462990
- [dEFEND] Kai Shu, Limeng Cui, Suhang Wang, Dongwon Lee, Huan Liu. dEFEND: Explainable Fake News Detection. Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), pp. 395–405, 2019. https://doi.org/10.1145/3292500.3330935
- [Monti19] Federico Monti, Fabrizio Frasca, Davide Eynard, Damon Mannion, Michael M. Bronstein. Fake News Detection on Social Media using Geometric Deep Learning. arXiv:1902.06673, 2019. https://arxiv.org/abs/1902.06673
- [EANN] Yaqing Wang, Fenglong Ma, Zhiwei Jin, et al. EANN: Event Adversarial Neural Networks for Multi-Modal Fake News Detection. Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), pp. 849–857, 2018. https://doi.org/10.1145/3219819.3219903
- [MVAE] Dhruv Khattar, Jaipal Singh Goud, Manish Gupta, Vasudeva Varma. MVAE: Multimodal Variational Autoencoder for Fake News Detection. The World Wide Web Conference (WWW), pp. 2915–2921, 2019. https://doi.org/10.1145/3308558.3313552
- [SpotFake] Shivangi Singhal, Rajiv Ratn Shah, Tanmoy Chakraborty, Ponnurangam Kumaraguru, Shin'ichi Satoh. SpotFake: A Multi-modal Framework for Fake News Detection. 2019 IEEE Fifth International Conference on Multimedia Big Data (BigMM), pp. 39–47, 2019. https://doi.org/10.1109/BigMM.2019.00-44
- [KMGCN] Youze Wang, Shengsheng Qian, Jun Hu, Quan Fang, Changsheng Xu. Fake News Detection via Knowledge-driven Multimodal Graph Convolutional Networks. Proceedings of the 2020 International Conference on Multimedia Retrieval (ICMR), pp. 540–547, 2020. https://doi.org/10.1145/3372278.3390713
- [MFAN] Jiaqi Zheng, Xi Zhang, Sanchuan Guo, Quan Wang, Wenyu Zang, Yongdong Zhang. MFAN: Multi-modal Feature-enhanced Attention Networks for Rumor Detection. Proceedings of the Thirty-First International Joint Conference on Artificial Intelligence (IJCAI), pp. 2413–2419, 2022. https://doi.org/10.24963/ijcai.2022/335
- [RIFT] Parth Joshi. RIFT - Reddit Information Falsity Tagger. Master's Project 1550, San José State University, 2025. https://scholarworks.sjsu.edu/etd_projects/1550

**Forensics combined with context**
- [Phan16] Quoc-Tin Phan, Alessandro Budroni, Cecilia Pasquini, Francesco G. B. De Natale. A Hybrid Approach for Multimedia Use Verification. Working Notes Proceedings of the MediaEval 2016 Workshop, CEUR Workshop Proceedings Vol-1739, 2016. https://ceur-ws.org/Vol-1739/MediaEval_2016_paper_47.pdf
- [Boididou18] Christina Boididou, Symeon Papadopoulos, Markos Zampoglou, Lazaros Apostolidis, Olga Papadopoulou, Yiannis Kompatsiaris. Detection and visualization of misleading content on Twitter. International Journal of Multimedia Information Retrieval 7(1):71–86, 2018. https://doi.org/10.1007/s13735-017-0143-x
- [Boididou18b] Christina Boididou, Stuart E. Middleton, Zhiwei Jin, et al. Verifying information with multimedia content on Twitter: A comparative study of automated approaches. Multimedia Tools and Applications 77(12):15545–15571, 2018. https://doi.org/10.1007/s11042-017-5132-9
- [NewsCLIPpings] Grace Luo, Trevor Darrell, Anna Rohrbach. NewsCLIPpings: Automatic Generation of Out-of-Context Multimodal Media. Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing (EMNLP), pp. 6801–6817, 2021. https://aclanthology.org/2021.emnlp-main.545/
- [Abdelnabi22] Sahar Abdelnabi, Rakibul Hasan, Mario Fritz. Open-Domain, Content-based, Multi-modal Fact-checking of Out-of-Context Images via Online Resources. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 14940–14949, 2022. https://openaccess.thecvf.com/content/CVPR2022/html/Abdelnabi_Open-Domain_Content-Based_Multi-Modal_Fact-Checking_of_Out-of-Context_Images_via_Online_Resources_CVPR_2022_paper.html
- [MetaAIGC] Chenyang Yang, Shen Yan, Yibo Yang, et al. Detecting AI-Generated Content on Social Media with Multi-modal Language Models. Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 6: Industry Track), pp. 217–229, 2026. https://aclanthology.org/2026.acl-industry.15/

**Who shares synthetic media, and how images travel on Reddit**
- [SynthPol] Zhiyi Chen, Jinyi Ye, Beverlyn Tsai, Emilio Ferrara, Luca Luceri. Synthetic Politics: Prevalence, Spreaders, and Emotional Reception of AI-Generated Political Images on X. Proceedings of the 36th ACM Conference on Hypertext and Social Media (HT '25), pp. 11–21, 2025. https://doi.org/10.1145/3720553.3746675
- [CanElection] Victor Livernoche, Andreea Musulan, Zachary Yang, Jean-François Godbout, Reihaneh Rabbany. Deepfakes in the 2025 Canadian Election: Prevalence, Partisanship, and Platform Dynamics. Proceedings of the ACM Web Conference 2026 (WWW '26), pp. 8717–8720, 2026. https://doi.org/10.1145/3774904.3792948
- [DiResta24] Renée DiResta, Josh A. Goldstein. How spammers and scammers leverage AI-generated images on Facebook for audience growth. Harvard Kennedy School (HKS) Misinformation Review 5(4), 2024. https://doi.org/10.37016/mr-2020-151
- [CNotesAI] Chiara Drolsbach, Emma Demirel, Nicolas Pröllochs. Characterizing AI-Generated Misinformation on Social Media. arXiv:2505.10266, 2025 (v2, July 2026). https://arxiv.org/abs/2505.10266
- [Chauhan25] Saumya Chauhan, Mila Hong, Maria Vazhaeparambil. When GenAI Meets Fake News: Understanding Image Cascade Dynamics on Reddit. 2025 IEEE MIT Undergraduate Research Technology Conference (URTC), pp. 1–5, 2025. https://doi.org/10.1109/URTC68753.2025.11533062
- [Matatov24] Hana Matatov, Marianne Aubin Le Quéré, Ofra Amir, Mor Naaman. Examining the Prevalence and Dynamics of AI-Generated Media in Art Subreddits. arXiv:2410.07302, 2024 (v3, September 2025). https://arxiv.org/abs/2410.07302
- [Lakkaraju13] Himabindu Lakkaraju, Julian McAuley, Jure Leskovec. What's in a Name? Understanding the Interplay between Titles, Content, and Communities in Social Media. Proceedings of the International AAAI Conference on Web and Social Media (ICWSM) 7(1):311–320, 2013. https://doi.org/10.1609/icwsm.v7i1.14408
- [Cheng14] Justin Cheng, Lada A. Adamic, P. Alex Dow, Jon Kleinberg, Jure Leskovec. Can cascades be predicted? Proceedings of the 23rd International Conference on World Wide Web (WWW), pp. 925–936, 2014. https://doi.org/10.1145/2566486.2567997
- [Birdwatch] Stefan Wojcik, Sophie Hilgard, Nick Judd, et al. Birdwatch: Crowd Wisdom and Bridging Algorithms can Inform Understanding and Reduce the Spread of Misinformation. arXiv:2210.15723, 2022. https://arxiv.org/abs/2210.15723

**Provenance and lineage**
- [Dias12] Zanoni Dias, Anderson Rocha, Siome Goldenstein. Image Phylogeny by Minimal Spanning Trees. IEEE Transactions on Information Forensics and Security 7(2):774–788, 2012. https://doi.org/10.1109/TIFS.2011.2169959
- [Moreira18] Daniel Moreira, Aparna Bharati, Joel Brogan, et al. Image Provenance Analysis at Scale. IEEE Transactions on Image Processing 27(12):6109–6123, 2018. https://doi.org/10.1109/TIP.2018.2865674
- [Zannettou18] Savvas Zannettou, Tristan Caulfield, Jeremy Blackburn, et al. On the Origins of Memes by Means of Fringe Web Communities. Proceedings of the Internet Measurement Conference 2018 (IMC '18), pp. 188–202, 2018. https://doi.org/10.1145/3278532.3278550
- [C2PA] Coalition for Content Provenance and Authenticity (C2PA). Content Credentials: C2PA Technical Specification, version 2.5. October 2026. https://spec.c2pa.org/specifications/specifications/2.5/specs/C2PA_Specification.html

**Evaluation pitfalls**
- [Mu23] Yida Mu, Kalina Bontcheva, Nikolaos Aletras. It's about Time: Rethinking Evaluation on Rumor Detection Benchmarks using Chronological Splits. Findings of the Association for Computational Linguistics: EACL 2023, pp. 736–743, 2023. https://aclanthology.org/2023.findings-eacl.55/
- [StepanovaRoss23] Nataliya Stepanova, Björn Ross. Temporal Generalizability in Multimodal Misinformation Detection. Proceedings of the 1st GenBench Workshop on (Benchmarking) Generalisation in NLP, pp. 76–88, 2023. https://aclanthology.org/2023.genbench-1.6/
- [ColdUsers] Sai Keerthana Karnam, Abhirup Kundu, Jashn Arora, Manish Jain, Animesh Mukherjee. Real-World Challenges in Fake News Detection: Dealing with Posts by Cold Users. Proceedings of the International AAAI Conference on Web and Social Media (ICWSM) 20(1):1190–1201, 2026. https://doi.org/10.1609/icwsm.v20i1.42689
- [VERITE] Stefanos-Iordanis Papadopoulos, Christos Koutlis, Symeon Papadopoulos, Panagiotis C. Petrantonakis. VERITE: A Robust Benchmark for Multimodal Misinformation Detection Accounting for Unimodal Bias. International Journal of Multimedia Information Retrieval 13(1), article 4, 2024. https://doi.org/10.1007/s13735-023-00312-6
- [Geirhos20] Robert Geirhos, Jörn-Henrik Jacobsen, Claudio Michaelis, et al. Shortcut learning in deep neural networks. Nature Machine Intelligence 2(11):665–673, 2020. https://doi.org/10.1038/s42256-020-00257-z

**Methods and tools**
- [GraphSAGE] William L. Hamilton, Rex Ying, Jure Leskovec. Inductive Representation Learning on Large Graphs. Advances in Neural Information Processing Systems 30 (NIPS 2017), 2017. https://proceedings.neurips.cc/paper_files/paper/2017/hash/5dd9db5e033da9c6fb5ba83c7a7ebea9-Abstract.html
- [GCN] Thomas N. Kipf, Max Welling. Semi-Supervised Classification with Graph Convolutional Networks. International Conference on Learning Representations (ICLR), 2017. https://openreview.net/forum?id=SJU4ayYgl
- [RGCN] Michael Schlichtkrull, Thomas N. Kipf, Peter Bloem, Rianne van den Berg, Ivan Titov, Max Welling. Modeling Relational Data with Graph Convolutional Networks. The Semantic Web: 15th International Conference, ESWC 2018, Lecture Notes in Computer Science, Springer, pp. 593–607, 2018. https://doi.org/10.1007/978-3-319-93417-4_38
- [HGT] Ziniu Hu, Yuxiao Dong, Kuansan Wang, Yizhou Sun. Heterogeneous Graph Transformer. Proceedings of The Web Conference 2020 (WWW '20), pp. 2704–2710, 2020. https://doi.org/10.1145/3366423.3380027
- [LightGBM] Guolin Ke, Qi Meng, Thomas Finley, et al. LightGBM: A Highly Efficient Gradient Boosting Decision Tree. Advances in Neural Information Processing Systems 30 (NIPS 2017), 2017. https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html
- [Grinsztajn22] Léo Grinsztajn, Edouard Oyallon, Gaël Varoquaux. Why do tree-based models still outperform deep learning on typical tabular data? Advances in Neural Information Processing Systems 35 (NeurIPS 2022), Datasets and Benchmarks Track, pp. 507–520, 2022. https://proceedings.neurips.cc/paper_files/paper/2022/hash/0378c7692da36807bdec87ab043cdadc-Abstract-Datasets_and_Benchmarks.html
- [Platt99] John C. Platt. Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods. In Alexander J. Smola, Peter Bartlett, Bernhard Schölkopf, Dale Schuurmans (eds.), Advances in Large-Margin Classifiers, MIT Press, pp. 61–74, 1999. https://doi.org/10.7551/mitpress/1113.003.0008
- [Guo17] Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger. On Calibration of Modern Neural Networks. Proceedings of the 34th International Conference on Machine Learning (ICML), PMLR 70:1321–1330, 2017. https://proceedings.mlr.press/v70/guo17a.html
- [Saerens02] Marco Saerens, Patrice Latinne, Christine Decaestecker. Adjusting the Outputs of a Classifier to New a Priori Probabilities: A Simple Procedure. Neural Computation 14(1):21–41, 2002. https://doi.org/10.1162/089976602753284446
- [Wolpert92] David H. Wolpert. Stacked generalization. Neural Networks 5(2):241–259, 1992. https://doi.org/10.1016/S0893-6080(05)80023-1
- [DeLong88] Elizabeth R. DeLong, David M. DeLong, Daniel L. Clarke-Pearson. Comparing the Areas under Two or More Correlated Receiver Operating Characteristic Curves: A Nonparametric Approach. Biometrics 44(3):837–845, 1988. https://doi.org/10.2307/2531595
- [HanleyMcNeil82] James A. Hanley, Barbara J. McNeil. The meaning and use of the area under a receiver operating characteristic (ROC) curve. Radiology 143(1):29–36, 1982. https://doi.org/10.1148/radiology.143.1.7063747
- [DINOv2] Maxime Oquab, Timothée Darcet, Théo Moutakanni, et al. DINOv2: Learning Robust Visual Features without Supervision. Transactions on Machine Learning Research (TMLR), 2024. https://openreview.net/forum?id=a68SUt6zFt
- [CLIP] Alec Radford, Jong Wook Kim, Chris Hallacy, et al. Learning Transferable Visual Models From Natural Language Supervision. Proceedings of the 38th International Conference on Machine Learning (ICML), PMLR 139:8748–8763, 2021. https://proceedings.mlr.press/v139/radford21a.html
- [Pushshift] Jason Baumgartner, Savvas Zannettou, Brian Keegan, Megan Squire, Jeremy Blackburn. The Pushshift Reddit Dataset. Proceedings of the International AAAI Conference on Web and Social Media (ICWSM) 14:830–839, 2020. https://doi.org/10.1609/icwsm.v14i1.7347
