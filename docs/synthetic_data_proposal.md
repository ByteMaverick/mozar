# Synthetic data proposal

Draft of 2026-11-15, for review before anything is built. Companion to `proposal.md`.

## 1. The proposal in one paragraph

We keep the real Reddit graph exactly as collected and make only two things:

1. **Edited images**, produced from our own real Reddit images, with the exact changed region recorded.
2. **A rule for which real re-posts carry an edit.** The rule is estimated from our real edit pairs and applied at several known strengths, including zero.

Every account, post, comment, timestamp and history stays real. Nothing social is invented. Statisticians call this design a *plasmode*: real data, with one known effect planted in it [Franklin14].

The reason for this design is that every natural pattern in the graph survives because we never generate the graph. The price is a limit on what it can prove, stated in section 2.

## 2. What it can and cannot show

| Question | Can synthetic data answer it? |
|---|---|
| Do FLAME and TruFor still work on images compressed the way Reddit compresses them? | Yes |
| How many real edits does our pair-finding miss? | Yes |
| With N edited posts, how large a social effect can our pipeline detect, and which model recovers it best? | Yes |
| Does the graph code (features, tree models, graph neural network) run correctly at scale? | Yes |
| Do people who post edited images really behave differently from people who post originals? (H1 and H2 in `proposal.md`) | **No. Only real pairs can.** |

The last row is the limit. If we decide which accounts carry the synthetic edits, any social signal we then measure is our own rule. The research found no paper that gets around this, and three bodies of work that show the danger (section 7). So the headline result stays on real pairs, and synthetic rows never enter the main comparison (E2).

Synthetic data can improve prediction on the image side, by setting detector thresholds on Reddit-style images. It cannot improve the social side.

## 3. Why we need it

- One month of 15 communities gave 16,926 usable images and 11 confirmed edited posts (about 30 to 40 expected after the hand check).
- A validation study needs at least 100 positive cases and ideally 200 [Collins16].
- The ten-month collection now running may reach that, but we will not know for a day or two.

## 4. Design

### 4.1 What stays real

The graph tables from `graph.py`, unchanged: users, posts and images; links for posted, has image, commented on, crossposted, same picture, and edited variant; each poster's 180-day history.

### 4.2 Synthetic edited images

Follows the generation steps of FLAME's own training set and OpenSDI [FLAME, OpenSDI].

1. Sample about 3,000 authentic images from our pool, matching the communities of the real edit pairs.
2. The labeling model we already have (Qwen3-VL-32B) proposes one change per image. A segmentation model outlines the region.
3. Make four kinds of edit, in the proportions seen in our hand-checked real pairs:
   - paste in an object from another Reddit image;
   - add, change or remove text;
   - remove an object (LaMa);
   - fill a region with an AI model (FLUX.1 Fill, which fits on one H100; research licence).
4. **Paste only the changed region back onto the original.** This gives an exact mask. It also matters for realism: when the whole image is regenerated, detectors score above 0.90, and when only the region is pasted back they fall to about 0.55 [InpaintEx].
5. Re-save every image the way Reddit does. In our sample, all 157 JPEGs from Reddit's image server used standard quality 75. To be confirmed on the full corpus.
6. Make three control versions of each source image: untouched, re-saved only, and passed through the AI model with nothing changed. The last control is needed because an unedited photo passed through such a model is flagged fake 91% of the time [InpaintEx].
7. Generate twice what we need, filter automatically, and hand-check 200 to 300.

### 4.3 Placing the edits in the real graph

The real edited posts we found are all re-posts: a picture is posted, and later an altered version appears. We already have many real *unaltered* re-posts (1,009 pairs in one month). The plan uses them.

1. Take a real re-post pair: original post A, later re-post B.
2. Swap B's image for a synthetic edit of it. The "same picture" link becomes an "edited variant" link. Nothing else changes: B's poster, time, community, comments and history are real.
3. Choose *which* re-posts get an edit by a rule with a strength setting:
   - **Strength 0:** chosen at random within community and month. Social features must score at chance (0.5) here. If they do not, the pipeline is leaking.
   - **Strength 1:** chosen with a probability fitted on the real pairs (real edited re-posts against real unaltered re-posts, using the history features). This ties the planted effect to the size the real data suggests.
   - **Strength 0.5 and 2:** the same rule, weaker and stronger.
4. Repeat with a second rule that the main model is not shaped for: an effect present only among accounts with ten or more prior posts. A simple shift on one feature is the easiest case for logistic regression, so one rule alone would flatter it [Karim26, Curth21].

The result is a curve: strength of the planted effect against how well each model recovers it. This is how astronomy reports what a detection pipeline can see [Kepler20].

### 4.4 What we are not doing

- **No invented accounts, histories or comments.** BotSim placed 1,000 AI-written accounts among 1,907 real Reddit accounts, and its authors note the synthetic accounts are structurally distinguishable [BotSim]. A review of 35 simulation papers found 15 validated only by "does it look believable" [Larooij25].
- **No simulated Reddit.** OASIS and Y Social are built to study how content spreads, not to make detection data. OASIS reports about 30% error against real cascades [OASIS, YSocial].
- **No added posts or links, and nothing posted to Reddit.**

## 5. How natural patterns are kept, and how we check

| Pattern | How it is kept | Check |
|---|---|---|
| Who posts and comments how much | No account, post, comment or link is added or removed | Counts identical before and after. A classifier on activity counts alone scores 0.5 at strength 0. This is the test that exposed earlier injection methods [Huang22]. |
| Posting times, and the gap between original and edit | The edit sits on a real re-post, at its real time | Compare gaps with the real edit pairs; reweight if they differ |
| Community mix | Re-posts sampled to match the real edit pairs | Table of shares |
| Kind and size of edit | Mixed to match hand-checked real pairs (so far 0.8% to 25% of the image) | Table; report whether a classifier can tell real edits from synthetic ones |
| Reddit's image processing | Step 5 of section 4.2 | Compression settings checked on the full corpus |
| One account posting both versions | Kept at the rate seen in real pairs | Share reported |

## 6. Files and experiments

**Files.** Each synthetic run writes its own folder, `data/synthetic/<run>/`, holding `nodes.csv`, `links.csv`, `index.csv` and `features.csv` in the existing formats, plus a `source` column (`real` or `synthetic`). The existing code and notebook run on it unchanged. The real tables are never modified.

**Experiments** (numbers from `proposal.md`):

| Experiment | Use of synthetic data |
|---|---|
| E0, detector check | Add the synthetic edits and their three controls, at Reddit compression |
| New: pair-finding audit | Hide 500 synthetic pairs in the image pool and report the share recovered, by edit size |
| E3, planted signal | Replace the single planted shift with the recovery curve of section 4.3 |
| Model comparison (logistic regression, tree models, graph model, fusion variants) | Compare under known truth, reported for both rules, since a benchmark's design can favour one method [Curth21] |
| E2, main result | None. Real pairs only. |

## 7. Precedents

"Opened" means a research agent read the source. "Listing" means only a search result or abstract was seen and the detail should be rechecked before it goes in the paper.

**Graph side**

| Source | What they did | What we take from it | Checked |
|---|---|---|---|
| [Franklin14] Franklin et al., *Comput. Stat. Data Anal.* 2014 | Plasmode: real patient records, outcome simulated with a known effect, including none | The overall design | Listing |
| [Kepler20] Kepler pipeline completeness, [arXiv 2010.04796](https://arxiv.org/abs/2010.04796) | Inject signals of known strength into real data; report the fraction recovered | The recovery curve and the pair-finding audit | Listing |
| [Huang22] Huang et al., [arXiv 2210.12941](https://arxiv.org/abs/2210.12941) | Showed injected graph anomalies are found by node degree and feature size alone (AUC 0.89 on Cora, no learning) | Keep degree untouched; run the counts-only check | Opened |
| [BOND] Liu et al., NeurIPS 2022, [arXiv 2206.10071](https://arxiv.org/abs/2206.10071) | Methods scoring about 0.8 on injected anomalies fall to about 0.5 on real ones | Why synthetic results never stand in for real ones | Opened |
| [GADBench] Tang et al., NeurIPS 2023, [arXiv 2306.12251](https://arxiv.org/abs/2306.12251) | Dropped injected anomalies; tree models beat graph networks on real ones | Tree models before a graph network | Opened |
| [BotSim] Qiao et al., AAAI 2025, [arXiv 2412.13420](https://arxiv.org/abs/2412.13420) | AI-written accounts placed among real Reddit accounts | The closest precedent, and why we keep accounts real | Opened |
| [OASIS] Yang et al., [arXiv 2411.11581](https://arxiv.org/abs/2411.11581); [YSocial] Rossetti et al., [arXiv 2408.00818](https://arxiv.org/abs/2408.00818) | Simulated platforms with AI agents | Not used as a data source | Opened |
| [Larooij25] Larooij and Törnberg, [arXiv 2504.03274](https://arxiv.org/abs/2504.03274) | Review of how such simulations are validated | Why we do not simulate | Opened |
| PETGEN (He et al., KDD 2021, [arXiv 2109.06777](https://arxiv.org/abs/2109.06777)); MALCOM (Le et al., ICDM 2020, [arXiv 2009.01048](https://arxiv.org/abs/2009.01048)) | Attached generated posts or comments to real histories; claimed only how the detector reacts | Precedent for synthetic content on real histories, with claims about the method only | Listing |
| OmniFake, Li et al., [arXiv 2509.25991](https://arxiv.org/abs/2509.25991) | Synthetic manipulations of real Reddit and news posts; poster information discarded | We keep the poster information they dropped | Opened |
| Raza, [arXiv 2605.12075](https://arxiv.org/abs/2605.12075) | Position paper: benchmarks that place synthetic content on realistic sharing graphs "are needed and none exist" | Positioning | Opened |
| [Karim26] Karim, [arXiv 2609.26186](https://arxiv.org/abs/2609.26186) | A plasmode "can refute but cannot certify" | The limit in section 2 | Abstract |
| [Curth21] Curth et al., NeurIPS 2021 Datasets and Benchmarks, [arXiv 2107.13346](https://arxiv.org/abs/2107.13346) | Semi-synthetic benchmarks favour some methods by construction | Two planted rules, not one | Abstract |

**Image side**

| Source | What they did | What we take from it | Checked |
|---|---|---|---|
| [FLAME] Wang et al., ICML 2026, [arXiv 2606.02178](https://arxiv.org/abs/2606.02178) | A vision-language model plans each edit, a segmentation model makes the mask, edit sizes are balanced, a second model verifies | Generation steps 2, 3 and 7. Also: image-level accuracy falls from 0.795 to 0.539 at JPEG quality 75 | Opened |
| [OpenSDI] Wang et al., CVPR 2025, [arXiv 2503.19653](https://arxiv.org/abs/2503.19653) | Same pattern on 300,000 images, with an automatic filter | The automatic filter | Opened |
| TGIF and TGIF2, Mareen et al., [arXiv 2407.11566](https://arxiv.org/abs/2407.11566), [arXiv 2603.28613](https://arxiv.org/abs/2603.28613) | Compared pasted-back and fully regenerated edits; TruFor falls from 0.83 to 0.32 at JPEG quality 80 | Paste-back; test at Reddit compression | Opened |
| [InpaintEx] Nebioglu et al., [arXiv 2602.00192](https://arxiv.org/abs/2602.00192) | Measured the paste-back effect and the false alarms on unedited images | Steps 4 and 6 | Opened |
| MIMLv2, Qu et al., [arXiv 2508.20987](https://arxiv.org/abs/2508.20987) | Adding synthetic edits to training lowered accuracy on real forgeries (0.494 to between 0.376 and 0.451) | We test and calibrate on synthetic edits; we do not train on them | Opened; recheck table values |
| RealEdit, Sushko et al., CVPR 2025, [arXiv 2502.03629](https://arxiv.org/abs/2502.03629); PSR, WACV 2026, [arXiv 2505.16181](https://arxiv.org/abs/2505.16181) | Collected real human edits from Reddit edit-request communities | The mix of edit kinds; a possible second real data source | Opened |
| [Collins16] Collins et al., *Stat. Med.* 2016 | At least 100 positive cases, ideally 200, to validate a prediction model | The target for real pairs | Opened |

The full notes are in `research_notes/Synthetic data for manipulation detection/`.

## 8. Work plan

| Step | What | Needs | Time |
|---|---|---|---|
| 1 | Pilot: 200 edits, hand-checked; run FLAME and TruFor on them | FLUX.1 Fill licence accepted on Hugging Face (it is a gated download) | 1 day |
| 2 | Scale to about 3,000 edits with controls | One H100. Speed per image is not published, so the pilot measures it | About 1 day |
| 3 | Pair-finding audit | Step 2 | Half a day |
| 4 | Graph tables at four strengths and two rules; run the notebook | Hand-checked real pairs to fit the rule (30 minimum, 100 or more is better) | 1 day |
| 5 | Recovery curve and the checks of section 5 | Step 4 | Half a day |

Steps 1 to 3 do not depend on the real pairs and can start now. Step 4 waits for the hand check.

## 9. Safeguards

- Synthetic images stay on the cluster. They are never posted or shared. What we release is the recipe, the masks and the post IDs.
- Automatic edits do not change a person's face or body, and do not add text that states a fact about a real person or event.
- Adult posts are already excluded at collection.

## 10. Decisions for the team

1. Is about 3,000 synthetic edits the right size?
2. Who accepts the FLUX.1 Fill licence? Without it we can still do three of the four edit kinds.
3. Do we add the edit-request communities (PSR) as a second real source? Those edits are openly requested, so they would be reported as a separate slice.
