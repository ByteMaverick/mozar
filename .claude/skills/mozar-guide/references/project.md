# How the project works

## The question

Forensic detectors such as FLAME (ICML 2026) and TruFor (CVPR 2023) judge an image by its pixels alone, and on
real platform images they are weak: FLAME averages about 0.46 pixel-F1 on editing tools it has not seen, and
recompression to the JPEG quality Reddit uses cuts both detectors sharply. A post, though, is never alone: an
account posted it, in a community, at a time, and the account has a history. We ask how much that history is
worth at the moment of posting, alone and added to the detector.

Existing social-context datasets (Fakeddit, and RIFT, which builds on it) label a post by the community it came
from, so a model can read the label from metadata. Our labels come from the image itself.

## The pipeline, step by step

All code is in `collect.py` (steps 1 to 7) and `graph.py` (steps 8 to 10). Settings are in `config.py`.
Every step reads the previous step's files, writes its own under `data/`, and skips work already done, so any
step can be rerun as more data arrives.

| Step | Command | What it does | Output |
|---|---|---|---|
| 1 | `collect.py posts` | Asks the Arctic Shift archive of Reddit for every post in each of the 15 subreddits between two dates, 100 per request, oldest first. | `posts/<sub>_<from>_<to>.jsonl` (raw, holds usernames) |
| 2 | `collect.py images` | Keeps posts with an image (first image of a gallery), skips adult posts, replaces usernames with account codes, downloads each distinct image once from Reddit's image server. Dead links go to `missing.txt`. | `posts/image_posts.csv`, `images/` |
| 3 | `collect.py pairs` | A 64-bit perceptual hash per image. Two images are a look-alike pair if at most 10 bits differ. Near-blank images are skipped; an image matching more than 10 others is treated as a template and dropped. Pair numbers never change between runs. | `pairs/hashes.csv`, `pairs/pairs.csv` |
| 4 | `collect.py diff` | Lines the two images up (ORB keypoints, RANSAC homography), blurs, subtracts, thresholds. Under 0.5% changed is an exact repost; over 40% or not alignable is a different picture; a band at the top or bottom is a caption; anything else is an **edit candidate**, outlined in red on both images. | `pairs/diff.csv`, `pairs/outline/` |
| 5 | `collect.py judge` | On one H100, Qwen3-VL-32B sees each candidate twice with the order swapped and answers six questions: real edit? which version? what trace? AI-made? confidence? what kind of picture (photo, meme, screenshot, other)? A pair is **labeled** only if both answers say "real edit" and name the same file. | `labels/judgments.jsonl`, `labels/decisions.csv` |
| 6 | `collect.py review`, then a person | A review page shows every candidate. A person writes `A`, `B` or `no` per pair in `labels/hand_check.csv`. A hand verdict always beats the model. | `pairs/review.html`, `labels/hand_check.csv` |
| 7 | `collect.py index` | One row per post: `manipulated` (carries the edit), `authentic_matched` (carries the original of a labeled pair), `authentic_fresh` (an image with no look-alike, three per manipulated post). | `index.csv` |
| 8 | `graph.py histories` | For each account in the index, its posts and comments in the 180 days before its post, from the archive. Usernames are not stored. | `histories/<account code>.jsonl` |
| 9 | `graph.py graph` | The graph as two tables (below). | `graph/nodes.csv`, `graph/links.csv` |
| 10 | `graph.py features` | One row of history numbers per post, as of its posting time, with its own pair hidden. | `features.csv` |

`docs/img/fig1_dataset.png` draws steps 1 to 9 with the one-month counts.

## The graph

The core follows RIFT (Joshi, SJSU 2025): Post, User and Subreddit nodes joined by `POSTED_BY` and `BELONGS_TO`.
We add an Image node and the links `HAS_IMAGE`, `COMMENTED_ON`, `CROSSPOSTED`, `SAME_AS` (exact repost) and
`VARIANT_OF` (one image is an edit of the other). Every link that comes from an action carries its time.

```
nodes.csv: id, type (User | Post | Subreddit | Image), subreddit, time
links.csv: src, dst, type, time
```

`VARIANT_OF` has no direction: which side is the edit is the label, and the label is never stored in the graph.
The tables load into Neo4j as they are, for looking at the graph; nothing in the pipeline needs Neo4j.

## The features (input to M1)

| Feature | Meaning |
|---|---|
| `n_posts`, `n_comments` | earlier posts and comments in the last 180 days |
| `posts_per_day`, `days_observed` | activity rate and how far back activity goes |
| `n_subreddits`, `subreddit_entropy` | how many communities, and how evenly spread |
| `share_image_posts` | share of earlier posts that were images |
| `n_prior_pool_posts` | earlier image posts inside our 15 communities |
| `prior_repost_share`, `prior_variant_share` | how often those were exact reposts, or altered versions, of pictures seen before |
| `has_history`, `history_capped` | whether there is any history, and whether it hit the 1,000-record cap |

## The 15 subreddits

| Group | Subreddits | Why |
|---|---|---|
| General photos | pics, OldSchoolCool | many reposts, so pairs are findable; old photos are often retouched |
| Viral | interestingasfuck, Damnthatsinteresting, nextfuckinglevel | high traffic, AI and altered images reported there |
| Political | PoliticalHumor, conspiracy, Conservative, PropagandaPosters | where a manipulated image matters most |
| Celebrity | Fauxmoi, popculturechat | celebrity photos are common edit targets |
| Film | shittymoviedetails, marvelstudios | posters and stills are edited and reposted constantly |
| Controls | aww, food | manipulation unlikely; a baseline |
| Added from July 2025 | mildlyinteresting, HistoryPorn, isthisAI, RealOrAI | real photos (the first two), and communities where people ask whether an image is real; chosen because the first 15 gave mostly meme edits |

The list was chosen by hand for the class run. The proposal plans 100 to 200 communities chosen by a written
rule for the paper.

## The three predictors

| Model | Sees | How |
|---|---|---|
| M0 | the image | FLAME and TruFor, used as released, not retrained; score recalibrated on Reddit images |
| M1 | the poster's history | logistic regression (fixed in advance); trees and XGBoost as comparisons |
| M2 | both | `logit p = a * logit(p_M0) + b * logit(p_M1) + c`; stacking as an exploratory alternative |

`docs/img/fig2_models.png` draws this. `docs/proposal.md` has the full plan (sections 6 and 7), the hypotheses
H1 and H2, and every check the paper must pass.

## Where the code runs

| Step | Where | Why |
|---|---|---|
| posts, images, histories | login node | need the internet |
| pairs, diff | a CPU job (`jobs/pairs.sbatch`) | heavy, no internet needed |
| judge | an H100 job (`jobs/judge.sbatch`) | needs a GPU; the model weights are in `models/` |
| index, review, graph, features, notebook | anywhere | light |

For a long collection, `jobs/long_run.sh` downloads images while posts are still being fetched and queues the
labeling job every hour, and `jobs/pairs.sbatch` repeats pair finding as images arrive.
