---
name: mozar-guide
description: Onboarding and working guide for the Mozar project (social context for image manipulation detection on Reddit). Use when someone is new to the repo, needs to log in to the SJSU CoE HPC or set up SSH, asks how the pipeline, data or graph work, asks what is weak or unfinished, works on modeling.ipynb (logistic regression, decision trees, random forest, XGBoost, grid search, class weights), or works on fusing the image detectors with the social signal.
---

# Mozar guide

You are helping a member of Team Mozar (Mohammed Ansari, Lazar Cankovic) find their way around the project
and do their part of the work. The person you are helping most often is **Lazar**, who knows computer vision
models well and is new to this codebase and to the cluster. His assignment is the **modeling** (section 4)
and, above all, the **fusion of the image detectors with the social signal** (section 5).

## How to use this guide

Work through it as a path, one step at a time. Explain plainly, check the step worked, then move on.
Do not dump a whole reference file on the person; read it yourself and walk them through the part they need.

| Step | Goal | Read |
|---|---|---|
| 1 | Log in to the cluster and open the shared project folder | [references/access.md](references/access.md) |
| 2 | Understand what the project is and how the data is built | [references/project.md](references/project.md) |
| 3 | Know what is weak or unfinished before trusting any number | [references/weaknesses.md](references/weaknesses.md) |
| 4 | Run and extend the modeling notebook | [references/modeling.md](references/modeling.md) |
| 5 | Work out how to inject the social signal into the image detectors | [references/fusion.md](references/fusion.md) |
| - | Papers to read and cite, by topic | [references/papers.md](references/papers.md) |

If the person asks something specific, jump straight to the matching file.

## The project in five sentences

Image forensics detectors look only at pixels, and they are weak on real platform images. A Reddit post
also comes with its poster's history. We find pairs of Reddit images where one is a local edit of the other,
label which one is the edit, and compare three predictors on those posts: the detector alone (M0), the
poster's history alone (M1), and both combined (M2). The question is whether M2 beats M0, and how far M1
gets alone. The dataset itself, with real social context attached to verified edits, is a contribution.

## Ground rules (never break these)

1. **Nothing after the post.** Features for a post use only what happened before its posting time.
2. **A post never sees its own pair.** The link between a post's image and its edited twin is hidden when its
   features are computed, and must be removed from any graph a model reads for that post.
3. **Splits by account and picture.** An account or a picture never sits in both training and testing.
   The notebook builds these groups; keep using them for every new model.
4. **No usernames outside the raw post files.** Everything else uses account codes (`u_` plus 12 characters).
   Never print, commit or share real usernames. **The repository is public**: never commit real data,
   raw posts, images, SJSU IDs, passwords, keys or tokens. Only `sample_data/` holds data, and it is scrubbed.
5. **Adult posts are never downloaded.**
6. **Do not touch Mohammed's running jobs** (`mozar-pairs`, `mozar-judge`, the collection on the login node).
   Do not start a second collection: the archive is shared and rate-limited, and two copies would double the load.
7. **Commits:** in this repository, commit messages carry no co-author or tool attribution lines.

## Where things are

| What | Where |
|---|---|
| Code (GitHub, public) | https://github.com/ByteMaverick/mozar; anyone can clone it, and pushing needs Mohammed to add you as a collaborator |
| Shared copy on the cluster | `/data/nsf-jg/mozar` (group `nsf-jg`, readable and writable by the group) |
| Shared Python environment | `/data/nsf-jg/mozar/.venv` |
| The live data and running pipeline | Mohammed's home folder; the shared folder gets a copy (see access.md) |
| Small real sample of every data file | `sample_data/` in the repo; run anything on it with `MOZAR_DATA=sample_data` |
| Proposal, design notes, bibliography | `docs/` |
| Figures (and the script that draws them) | `docs/img/`, `docs/make_figures.py` |

## Status on 15 November 2026

- The whole pipeline is built and has run end to end on one month (8 October to 8 November 2026, 15 subreddits).
- January to October 2026 is being collected now, with downloads, pair finding and labeling running in parallel.
- One month gave 48,924 posts, 16,078 images, 1,260 look-alike pairs, 121 edit candidates, 17 labeled pairs,
  12 manipulated posts, and 55 pairs waiting for a hand check. By mid-afternoon on 15 November, 61,348 images
  had been fingerprinted, giving 332 edit candidates.
- The detectors (FLAME, TruFor) have not been run yet. No model results exist yet.
- Deadlines: progress report 16 November 2026, class presentation about 28 November 2026, workshop paper
  around February 2027.

These numbers age quickly. On the cluster, ask Mohammed or check the shared folder for newer copies before
quoting them.
