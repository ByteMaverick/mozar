# Social Network-Aware Detection of AI-Manipulated Images

Team Mozar: Mohammed Ansari, Lazar Cankovic
Living design document. Last updated 2026-11-14.
Scope of this document: the whole project at the level of what, why, with what data, and who does which half. Internal details (schemas, hyperparameters, code structure) are left to the two builders.

**Read `proposal.md` (Draft 2) first.** After an independent review on 2026-11-14 it supersedes this document on: how rows are labeled and chosen (section 3C), which features are allowed (sections 4 and 5), the model definitions (section 2), and the statistical rules (section 6). The reasons are in `proposal.md` section 16. The research question, the choice of TGIF, FLAME and TruFor, the post-time rule, and the work split below still stand.

Supporting material:
- **Paper proposal (title, gaps, contributions, related work, method, experiments, outline, references): `proposal.md`**
- Dataset survey report (read this first): `reports/Manipulation datasets for social graph coupling.md`
- Raw research notes behind it: `research_notes/Manipulation datasets for social graph coupling/`
- Prior art we build on: RIFT (Joshi, SJSU 2025), https://github.com/Parth-Joshi-6669/RIFT

---

## 1. Research question

**Can social-network attributes improve the accuracy of predicting whether an image posted on a social platform was AI-manipulated?**

Two hypotheses:

- **H1.** Adding social context to a state-of-the-art image-manipulation detector improves its accuracy, and the improvement is concentrated on subtle edits where the detector alone is uncertain.
- **H2.** Social attributes alone, with no access to the pixels, are a usable early signal that an image may be manipulated.

### The deployment moment

The system is judged at the instant a post goes up. A page calling itself "World News" posts a doctored photo; nobody has reacted yet; we want a label on it right then. Therefore:

- Nothing about the post's own reactions (its likes, its comments, its reposts) may be a feature.
- Everything we use must already exist at posting time: the poster's past, the community's past, and the image's past (earlier appearances elsewhere).
- Evaluation is temporal: the graph is frozen at the post's timestamp, features are computed from history only, and the prediction is compared to truth.

A secondary "one hour after posting" mode may be reported separately, since platforms also act after the fact, but it is not the headline.

### Why this question

- Fully AI-generated images are increasingly detectable. Subtle localized edits are not. The best published localizer (FLAME, ICML 2026) averages pixel-F1 0.46 on editors it has not seen; on Nano Banana edits it gets 0.30 and TruFor gets 0.09. On compressed, platform-style images detectors fall further.
- A manipulated image on a platform does not exist in isolation. It was posted by someone with a history, into a community with a history, and often it appeared somewhere before. That context may contain evidence the pixels do not.
- Nobody has tested this. As of November 2026 no paper fuses a pixel-level manipulation detector with poster, community, or propagation features and reports a vision-only vs vision+social ablation. The nearest work (MediaEval 2015-2016) asked the inverse question with 2015-era forensics and abandoned it.
- Practical payoff: a platform that already runs a detector over uploads could add this layer using data it already has.

### What we are explicitly NOT doing

- **No community-as-proxy.** We do not let the model learn "this subreddit posts fakes." Raw community identity is never a feature.
- **No synthetic or simulated networks.** If we generate the network, the social signal is whatever we chose to put in.
- **No editing images ourselves for the graph.** If we manipulate an image after it was posted, the people who reacted were reacting to the unedited picture; their behavior carries no information about our edit, and the social model is at chance by construction.
- **No labeling the real-world corpus with the detector we are testing.** Then "manipulated" would mean "the detector can tell," the hard cases would be defined out of the positive class, and the comparison would be circular.
- **No fake-news-as-proxy.** Fakeddit's misinformation label is not a manipulation label; most "fake" posts there have untouched photos, and using it would turn the project back into RIFT.

---

## 2. Approach: three models, one comparison

| Model | Input | Role |
|---|---|---|
| **M0: image only** | pixels | the best published manipulation detector, run as released. The baseline. |
| **M1: social only** | our post-time social attributes, no pixels | tests H2 |
| **M2: image + social** | M0's score (and/or embedding) fused with the social attributes | tests H1 |

Same rows, same splits, same metrics. Outcomes and what they mean:

- M2 > M0 by a margin that survives confidence intervals, largest where M0's score is near 0.5: social context helps, especially where vision is weak. The result we hope for.
- M2 ≈ M0 and M1 ≈ chance, with all controls in place: social context carries no information beyond the pixels for this corpus. Still a valid, reportable result.
- M1 clearly above chance and above the prior-only dummy: social attributes alone are a cheap early signal.

Later extension, not in the first pass: M3, a learned graph embedding (GNN over the user/post/image/community graph) in place of engineered attributes, to compare "hand-designed features" against "learned over the graph."

---

## 3. Data

There are two completely separate data assets. They never mix.

### 3A. Lab benchmark: TGIF (+ CocoGlide)

**Role:** validate that M0 runs and reproduces its published numbers, and define what "hard" means. **Never enters the graph.** These images were never posted anywhere, so there is no social context to attach.

**Decision (Mohammed): TGIF**, Text-Guided Inpainting Forgery, IDLab Media, Ghent University / imec. IEEE WIFS 2024, extended as TGIF2.

How it was built: 3,124 real COCO photos (Flickr originals, re-fetched at up to 1024 px). For each, a COCO object mask is inpainted by a text-guided model: Stable Diffusion 2, SDXL, Adobe Firefly via Photoshop; TGIF2 adds FLUX.1. Two output styles per edit:
- **spliced (sp):** the generated region is pasted into the original pixels; only the masked area is synthetic. This is the "pen becomes knife" case.
- **fully regenerated (fr):** the whole image is re-rendered by the diffusion model; the semantic change is still local, but every pixel passed through the generator.

24 forged variants per original: 74,976 forged in TGIF, 271,788 with TGIF2. Splits by object category (~80/10/10): train 58,560 / 2,440, val 8,184 / 341, test 8,232 / 343 (forged / authentic). Strong class imbalance; use macro metrics.

Ships with: originals, masks (segmentation, bbox, random-rect, Photoshop-adapted), per-image generator settings and aesthetic scores, JPEG Q80/Q60 and WEBP Q80/Q60 recompressed test variants that simulate platform re-encoding, benchmark results, and the generation code. CC BY-SA 4.0. Links verified live 2026-11-06.

Published pixel-F1 at 0.5, uncompressed (SD2-sp / PS-sp / SD2-fr / SDXL-fr): TruFor 0.83 / 0.79 / 0.19 / 0.18; CAT-Net 0.87 / 0.85 / 0.04 / 0.03. Under JPEG Q80 the spliced sets collapse too (TruFor 0.32 / 0.44). Caveat: fully regenerated images are hard for localizers but easy for whole-image synthetic detectors (DIMD AUC 1.00, PatchCraft 0.98), because the entire image carries a generator fingerprint. They are not a true hard case.

**Hard-subset definition (Claude's call, from published evidence):** spliced edits after platform-style recompression; FLUX and Firefly inpaints (DINOv3 detectors at AUROC 0.41-0.45); any edit covering under ~5% of the image (all detectors near chance). On the real-world corpus the same definition is applied using the pixel-diff mask from lineage (see 3C).

**CocoGlide** (512 COCO/GLIDE pairs, from the TruFor paper) is run alongside purely so our M0 numbers are comparable with every other paper's table.

TGIF is not yet the field's standard leaderboard. The classic IMDL-BenCo suite (CASIA, Columbia, COVERAGE, NIST16, IMD2020) is the standard for older splicing forgeries; for AI edits there is no settled benchmark and each 2025-2026 paper picks its own mix. We state this in the paper.

- Paper: https://arxiv.org/abs/2407.11566
- Repo: https://github.com/IDLabMedia/tgif-dataset
- Images: https://cloud.ilabt.imec.be/index.php/s/xEeAzrY7ES9KA8o
- TGIF2 FLUX: https://cloud.ilabt.imec.be/index.php/s/KG48tLZZzifC5WE

### 3B. The detector, M0

**Decision (Mohammed): FLAME (ICML 2026) as the best-performing model. TruFor (CVPR 2023) alongside as the citable baseline everyone compares against.**

FLAME: "Order within Chaos: Capturing Intrinsic Energy Anomalies for AI-Manipulated Image Forgery Localization", Wang et al., ICML 2026.
- Paper: https://arxiv.org/abs/2606.02178
- Code + weights: https://github.com/phoenixnir/FLAME (checkpoint under tag v0.1.0, SAM 2 backbone; license not stated in README, check before publishing)
- What it is: a frozen SAM 2 (Meta's foundation segmentation model) fed the image plus a hand-designed "energy anomaly" map, with a small trained adapter that outputs the edited-region mask and an image-level score. Not an LLM. Supervised on (image, mask) pairs.
- Trained on MagicBrush + a subset of SID-Set. Evaluated OOD on CocoGlide, AutoSplice, and self-generated Nano Banana / Qwen-Image-Edit / Flux Kontext sets. Does NOT use TGIF, so our TGIF numbers are honest out-of-distribution numbers.
- OOD average pixel IoU / F1: FLAME 0.358 / 0.459; TruFor 0.247 / 0.324; Mesorch 0.207 / 0.268. Image-level accuracy average 0.639.

TruFor: SegFormer backbone on RGB plus a learned noise-residual branch, outputs anomaly map and image-level score. Public weights, Docker. License "informational and nonprofit purposes only."

**How M0 is used:** run as released over every image, lab and real-world. We take the image-level score (and optionally the embedding) as M0's output. **We do not retrain M0 on the real-world corpus.** Real platform images are out of distribution for it by construction, which is the realistic deployment condition.

**Fairness control (Claude's call):** also report an M0 fine-tuned on the training split of the real-world corpus, so a reviewer cannot attribute the social gain to a weak baseline. If social context still helps the fine-tuned M0, the result stands.

SID-Set is held in reserve as training-side image data only if fine-tuning is needed.

### 3C. The real-world corpus (the contribution)

**This is the dataset the project produces, and the only data the graph and M1/M2 ever see.** No released dataset pairs trustworthy manipulation labels with real social context (see the survey). Building this is unavoidable and is the paper's main contribution.

**Platform (Claude's call): Reddit, via the Arctic Shift archive.** Reddit's public Data API is shutting down (no new access after 2026-10-31, all public access ends March 2027), so RIFT's PRAW path is gone. Arctic Shift has monthly dumps of every post and comment (all subreddits in one file per month, through 2026-10 as of 2026-11-14; per-subreddit files exist only for the top 40,000 subreddits and stop at 2023-12; distribution is by torrent), plus a free API with comment trees, user histories, and flair aggregates. Images are not archived; they must be fetched live from Reddit while posts survive, so fetching happens immediately after download. Bluesky (open firehose, public likes/reposts/follows, images on CDN, no key) is the optional second platform; it exposes likers, which Reddit does not.

**Label source: lineage.** The manipulation label comes from the image's own history, not from a community name, not from us, not from the detector.

Three kinds of lineage match:
1. A wild image matches an edit from a **root community** where edits are known to be edits by thread structure: r/photoshopbattles (submissions are originals, image comments are edits), r/PhotoshopRequest and r/estoration (request post is authentic, image replies are edits), AI-art subs with mandatory flair. The wild post is labeled **manipulated**.
2. A wild image matches a root **original**. The wild post is labeled **authentic**.
3. A wild image matches an **earlier wild image** and the pixels differ in a localized region. The later one is labeled manipulated, the earlier authentic. No root involved; this is the "politician holding a different sign" case.

Timestamps give direction: the earlier appearance is the origin. The pixel diff between origin and copy gives an edit mask for free, which is how the hard-subset definition (edit area under ~5%) transfers to real data.

**Wild communities** are large general subreddits where nobody declares anything: r/pics, r/interestingasfuck, r/Damnthatsinteresting, r/OldSchoolCool, r/HistoryPorn, r/mildlyinteresting, political and conspiracy image subs. Final list is a builder decision. Both classes must appear in the same wild communities, which lineage guarantees since originals get reposted too.

**Why this stays faithful to the deception scenario:** the wild repost is the deployment moment. A real account lifted a real edit (or a real original) and posted it with no disclosure. The label is grounded by the image's past; the community the repost landed in is not the community that labeled it.

**Honest limits, stated in the paper:**
- The corpus is "images that got reposted." Both classes are subject to that, so the comparison is fair, but the conclusion is about content that spreads, not all content. Content that spreads is what platforms care about most.
- Not every reposter means to deceive. Some reshare a photoshopbattles edit as a joke.
- Manipulated images the deceptive actor made themselves and that never appeared anywhere before have no lineage. For those only poster and community history exist as features, and only fact-checks or detector+human can label them.

**Scale unknown until the pilot.** The pilot's output is one number: matched manipulated wild posts with surviving images. Above a few hundred, proceed. Below, use the fallback.

**The full construction design, stage by stage, with the rules for every ambiguity (what counts as a row, how overlays and crops are classified, how far user histories extend, the tripwire protocol, the pilot gate), is in `docs/superpowers/specs/2026-11-06-dataset-construction-design.md`.** That document governs where this section is vague.

### 3D. Fallbacks and the wild check

- **Fallback for the experiment: within-community disclosure corpus.** Communities with a mandatory AI-edit flair; flagged and unflagged posts from the same subreddit; label from the flair; features from poster and engager history; test on held-out users and subreddits. Not deception in the wild, and the paper says so, but it answers whether context carries information beyond the pixels, which is the thing the deception application depends on.
- **Wild transfer check: CONVEX** (X Community Notes, April 2026). 66K image posts marked Edited / AI-generated by notes, with engagement counts. No media and no author fields ship. Real deception with real labels. **Cost reality:** rehydrating a few thousand posts to get the images costs tens of dollars and shows only that M0 transfers. Showing that the *social* gain transfers needs each post's author and that author's timeline for post-time features, at $0.01 per user plus $0.005 per post read, roughly $1K to $3K for a few thousand posts. Also, CONVEX's negative class is "miscaptioned," not verified-authentic. Decision pending (section 11): budget it, run the cheap M0-only version, or drop it and say so.
- **Negative control: Fakeddit audit.** One afternoon. Train subreddit-only and author-only classifiers for Fakeddit's Manipulated vs True. Show they score near-perfect. This is the slide that explains why the existing dataset cannot answer the question.

---

## 4. Graph ontology

High level only; the schema is a builder decision.

**Nodes:** User, Post, Image, Community. The Image is its own node, shared across every post that used it, so "where else has this picture been" is a one-hop query.

**Edges:** POSTED (User→Post), POSTED_IN (Post→Community), HAS_IMAGE (Post→Image), COMMENTED_ON (User→Post), CROSSPOSTED (Post→Post), REPLIED_TO (Post→Post, for root-community threads), VARIANT_OF (Image→Image, from lineage, carrying the pixel-diff mask area). Bluesky adds LIKED, REPOSTED, FOLLOWS.

**Attributes on nodes:** timestamps everywhere; on Image, the M0 score and the lineage label where one exists; on User, account age and activity counts; on Community, size.

User nodes carry each user's full Reddit history from Arctic Shift, not just activity in the subreddits we picked.

**Two kinds of social information, kept separate because they feed different experiments:**
- **Engineered attributes** (feed M1 and M2 in the first pass): aggregates computed by graph queries.
- **Relations** (feed M3 later): the structure itself, learned over by a GNN.

Storage is a builder decision. RIFT used Neo4j and exported to PyTorch Geometric; that pattern is fine, but RIFT's row-by-row loader will not scale and should be replaced with batched loading.

---

## 5. Features at post time

Every feature for a post at time t is a graph query that stops at t. Categories:

- **Poster history:** account age, prior post count, posting rate, spread of communities, fraction of prior images with a manipulated lineage label, mean M0 score over prior images, prior engagement received.
- **Community history:** same aggregates over the community's prior images, leave-one-out so the post being judged is not in its own feature.
- **Image history:** number of prior appearances, time since first appearance, spread velocity across communities, M0 score and engagement at earlier appearances, number of distinct prior posters.
- **Engager history (of the poster's prior posts, not this one):** prior manipulated rate of the users who engaged with the poster's earlier posts, overlap of those users with known high-manipulation posters.

**Anti-leakage rules (non-negotiable):**
- No raw user ID, community ID, or thread-position field as a feature.
- Image-history features never include the origin's community name or whether the origin was a post or a comment; that is the label by another name. Only counts, timings, scores, and engagement.
- All aggregates are leave-one-out and time-cut.

Platform caveat: Reddit does not expose who upvoted, so visible engagers on Reddit are commenters and crossposters. Bluesky exposes likers, reposters, and followers.

---

## 6. Evaluation

**Splits**, all reported:
- unseen-user: test users never seen in training
- unseen-community: test subreddits never seen in training
- temporal: train before a date, test after
- unseen-generator (lab side, via TGIF)
- random, included only to show how much it inflates

Why these matter, with numbers to cite: on Fakeddit, accuracy is 0.93 on test posts whose users were seen in training and 0.72-0.76 on unseen users; random splits on Twitter15/16 inflate macro-F1 by 35-44 points over temporal splits.

**Controls:**
- **Identity tripwire:** a model given only raw user ID and subreddit ID, tested within community. If it scores high, something leaked and we find it before reporting anything.
- **Prior-only dummy**, because class priors drift over time.
- **Fine-tuned M0** alongside as-released M0, so the baseline is a fair fight.
- Image-only, social-only, and fused reported side by side with deltas and confidence intervals (VERITE showed image-only can beat naive multimodal fusion).

**Metrics:** AUROC, AUPRC, macro-F1, accuracy. Everything also reported on the hard subset (M0 score near 0.5, and edit area under ~5% where lineage gives a mask).

**Success criteria** are the outcome table in section 2.

---

## 7. What RIFT gives us, and what it does not

Repo: https://github.com/Parth-Joshi-6669/RIFT. Six scripts, about 940 lines total.

**Reusable as ideas:**
- The Neo4j schema sketch (Post, User, Subreddit; POSTED_BY, BELONGS_TO) and the Neo4j → PyTorch Geometric export pattern.
- The chunked-extraction-with-resume pattern in the Reddit fetch script.

**Not reusable as code:**
- The extraction script depends on PRAW, which is going away. Our source is Arctic Shift dumps and API.
- The Neo4j loader runs one transaction per statement per row with hardcoded Windows paths. It would take days at our scale. Batched loading is a rewrite, not an edit.
- The CLIP text-image similarity scripts are for a feature we do not need.

**Learn from it as a cautionary example.** Despite the thesis text, the released GCN trains on four features: upvotes, a label-encoded author ID, a label-encoded subreddit ID, and text-image similarity. The BERT and CLIP embeddings described in the thesis are not in the training code. The split is random and the label is Fakeddit's two-way label, which Fakeddit assigned by subreddit, so the subreddit ID alone is a plausible reason for its 95-96% accuracy. **Correction, 2026-11-14 (scripts re-read line by line, not run):** the graph does not reach the model. (1) The loader stores `(User)-[:POSTED_BY]->(Post)` but the training query matches `(Post)-[:POSTED_BY]->(User)`, so every post's author comes back "Unknown" and the author feature is constant. (2) Author nodes are named by their encoded numbers while the edge list uses real usernames, so the user-post edges fail the lookup and are dropped; the GCN script then falls back to self-loops. The live inputs are upvotes, subreddit ID and text-image similarity, one post at a time. An earlier version of this section said test posts stay connected to their authors during training; that was wrong. The author's own database may have differed from what the released loader builds, so confirm by running the code or asking him before saying this in the paper. We can say this politely in related work; it motivates our controls.

---

## 8. Work split

Two people, two halves, one meeting point. **Person A** owns everything that touches pixels. **Person B** owns everything that touches the graph. They meet at the fusion table.

**Person A: image side**
1. Download TGIF and CocoGlide. Set up FLAME and TruFor from their repos.
2. Reproduce published numbers on CocoGlide and TGIF. Produce the hard-subset definition with evidence.
3. Build the inference service: given a folder of images, output per-image score, embedding, and mask. This is what Person B calls over the real-world corpus.
4. Implement the pixel-diff step for lineage pairs: given (origin, copy), output the edit mask and its area.
5. Later: the fine-tuned-M0 fairness control, and the fusion head for M2.

**Person B: graph side**
1. Download Arctic Shift dumps for the root and wild subreddits over the chosen window. Fetch images immediately; record survival rate.
2. Hash and embed every image; run near-duplicate matching; produce the lineage table (origin, copy, direction, match type).
3. Build the graph: nodes, edges, attributes, user histories. Batched loading.
4. Write the feature queries with time-cut and leave-one-out. Produce the one-row-per-post table.
5. Define and implement the splits and the identity tripwire.
6. Later: Bluesky collector, CONVEX rehydration, M3 GNN.

**Shared**
- The pilot go/no-go decision.
- The Fakeddit audit (small, whoever has a free afternoon).
- Training and evaluating M1 and M2 on the feature table, and the write-up.

**Interface contract between A and B:** a CSV keyed by image hash with M0 score, embedding path, and mask path. Everything else is independent.

---

## 9. Phases

| Phase | What | Who | Gate / output |
|---|---|---|---|
| 0 | Dataset survey | done | `reports/` |
| 1 | M0 running, published numbers reproduced, hard subset defined | A | numbers match paper within tolerance |
| 2 | Arctic Shift pull for 5 root + 5 wild subreddits, images fetched, hashed, matched | B | count of matched manipulated wild posts with surviving images |
| 3 | **Pilot gate.** Decide lineage vs fallback. | both | go if count is in the hundreds and identity tripwire is low |
| 4 | Full corpus, graph, feature table, splits | B (A supplies M0 scores and masks) | feature table with labels |
| 5 | Train M1, M2; run the ladder; stratify by difficulty | both | results table |
| 6 | Fairness control, CONVEX check, Fakeddit audit | A / B / either | appendix results |
| 7 | Write-up | both | paper |

Phases 1 and 2 run in parallel and start now. Phase 3 is two weeks out.

**Pilot gate, precisely:** proceed with lineage only if (a) images survive at a usable rate, (b) at least a few hundred wild manipulated matches exist, and (c) the identity tripwire within community sits clearly below M0. Otherwise switch the experiment to the disclosure-flair corpus and keep the lineage matches as the wild check.

---

## 10. Decisions log

| Date | Decision | By |
|---|---|---|
| 2026-11-06 | Lab benchmark = TGIF, plus CocoGlide for comparability | Mohammed |
| 2026-11-06 | M0 = FLAME as best model, TruFor as citable baseline | Mohammed |
| 2026-11-06 | Three-model comparison (image / social / fused) | Mohammed |
| 2026-11-06 | Features frozen at post time; no features from the post's own reactions | Mohammed |
| 2026-11-06 | Graph-based: knowledge graph first, features derived by queries | Mohammed |
| 2026-11-06 | No synthetic networks; no self-made edits in the graph; no detector labels for the corpus | Claude's recommendation, accepted in discussion |
| 2026-11-06 | M0 run as released, not retrained on the corpus; fine-tuned variant as fairness control only | Claude's call |
| 2026-11-06 | Real-world corpus from Reddit via Arctic Shift; lineage as label source; disclosure-flair as fallback; CONVEX as wild check | Claude's call, pending team sign-off |
| 2026-11-06 | RIFT: reuse ideas and schema, not code | Claude's call |
| 2026-11-14 | Paper proposal drafted in `proposal.md`. New design elements it introduces, all pending team sign-off: M0* (stacked image-only baseline trained on the same folds) as the fair comparison for M2; two M1 variants (M1-meta with no detector output anywhere, M1-hist with cached detector scores of historical images); M2-prior (three-parameter log-odds fusion) alongside M2-stack; leave-lineage-out in all history aggregates; root communities are label-only and never feed features; triage curves as the operational test of H2; information added reported in bits; placebo tests (label permutation, CLIP probe, wrong time cut); cold-start stratification | Claude's proposal |
| 2026-11-14 | Assumed for the proposal, team to confirm: positive class = any localized content manipulation, AI-edit slice reported separately; fully generated images and restorations out of scope; second label source and Bluesky are stretch goals | Claude's assumption |
| 2026-11-14 | Proposal revised to Draft 2 after an independent hostile review (verdict on Draft 1: reject). Changes: label follows human-verified edit direction, not timestamps; headline rows from wild-to-wild edit pairs only, root-anchored rows a separate slice; second kind of authentic row (never-seen images); root-blind and pair-blind histories; no detector scores, human labels or community statistics as features; one confirmatory model per hypothesis with four Holm-corrected tests; difficulty defined by the image, not the detector score; M0* given the same learner as the fused model; survival check; audience features, historical detector scores and the graph model moved to stretch | Claude's proposal, pending team |
| 2026-11-14 | Venue shortlist: a CVPR 2027 forensics workshop (expected late Feb to mid-Mar), then an ICWSM 2027 workshop or MAD at ICMR 2027, then a KDD 2027 workshop. See `research_notes/workshop_venues_2027.md` | Claude's recommendation |
| 2026-11-14 | Feasibility probe of the Reddit archive (`research_notes/feasibility_probe_2026-11-14.md`): about 305,000 image posts a year in the candidate wild subreddits, roughly 117,000 still up; images of still-up posts survive, author-deleted ones do not; number of edit pairs unknown, inferred 6 to 700 manipulated wild posts a year; no sign of edits moving from edit-request communities into wild ones. Plan now starts with a one-week yield test on two subreddits, with go, widen, or reduce thresholds | Claude's proposal, thresholds pending team |
| 2026-11-14 | Reference list verified against primary records (91 entries, `bibliography.md`). Closest prior work identified: Chauhan et al. 2025, which predicts virality from AI status on Reddit cascades; it does not pre-empt the question | Verified |

## 11. Open questions

**Team decisions (change what gets built):**
- **Positive class: AI-manipulated only, or manipulated by any tool?** Title, M0 (FLAME, trained on AI edits) and TGIF say AI. The root communities produce a lot of manual Photoshop. If AI-only: the tool-type sub-label from comment text becomes required, the pilot gate gains a generative-fraction criterion, and the positive count drops by a large factor. If any-tool: the title and claim change, and TruFor or Mesorch become natural M0 choices alongside FLAME. Sub-decisions: AI-art flair subs yield fully generated images with no origin and no mask (exclude from lineage, keep for the fallback corpus?); r/estoration yields restorations and colorizations (deception? include with a flag or exclude?).
- **Compute, storage, calendar.** Deadline; GPU availability (scoring on the order of a million images with a SAM 2 model is days of GPU); local disk for dumps and images. These set how many subreddits and months the full corpus can cover and whether phase 3 in two weeks is realistic.
- **CONVEX budget.** $1K to $3K for a social-transfer check, tens of dollars for an M0-only check, or drop it (see 3D).

**Builder decisions:**
- Final root and wild subreddit lists, and the time window (B).
- Near-duplicate matching method and threshold (B).
- Whether to run Bluesky in the first pass or defer it (a collector is cheap and deletions are irreversible; start it regardless).

**Admin:**
- IRB determination for public social-media data with poster-history aggregation (ask the advisor).
- FLAME's license (unstated in README; check before publishing anything derived from it).
