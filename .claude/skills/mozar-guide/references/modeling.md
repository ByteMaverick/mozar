# Modeling: the notebook and how to extend it

All modeling lives in `modeling.ipynb`. It reads `features.csv` (one row per post) and writes
`results/scores.csv`. Run it on the sample first: `MOZAR_DATA=sample_data jupyter lab modeling.ipynb`
(the sample has too few posts to fit models, but every cell runs).

## What each section does

| Section | What happens |
|---|---|
| 1. Data | Loads the features, sets `y = 1` for manipulated posts, shows counts per subreddit and average feature values per label. |
| 2. Working subset | A random, shuffled sample for quick runs. `FRACTION` keeps a share of each class; `NEG_PER_POS` caps authentic posts per manipulated post. Default: everything. |
| 3. Splits and scoring | Builds the groups (every post that shares an account or a picture is in one group), the log-scaled feature matrix `X`, and helpers: `folds` (grouped, stratified), `cv_scores` (out-of-fold scores), `auc_ci` (AUROC with a bootstrap interval). |
| 4. M0 | Reads detector scores from `results/m0_scores.csv` when they exist and recalibrates them on Reddit images. |
| 5. M1 compared | Four model families, each tuned by grid search inside nested grouped cross-validation. Table of AUROC (with interval) and average precision. |
| 6. M1 chosen | The best family is tuned on all the data; its coefficients or importances are shown. |
| 7. M2 | Late fusion (confirmatory) and stacking (exploratory). |
| 8. Checks | Shuffled history must fall to chance. |
| 9. Save | Writes every score column to `results/scores.csv`. |

## Why it is built this way

**Class weights.** Manipulated posts are rare (20% of rows in the dataset table, about 0.1% of all images).
Without weighting, a model can score well by calling everything authentic. `class_weight="balanced"` (logistic
regression, trees, random forest) and `scale_pos_weight = authentic / manipulated` (XGBoost) make the total
cost of errors on each class equal. Do not oversample before splitting: copies of the same post would land in
training and testing (Kapoor and Narayanan 2023 list this as a classic leak). If oversampling (SMOTE) is ever
tried, it goes inside the training folds only.

**Nested cross-validation.** Grid search picks hyperparameters. If it picks them on the same posts that are then
used to report the score, the score is optimistic. So the outer folds give the score, and `GridSearchCV` runs
inside each outer training part with its own inner folds. Both levels group by account and picture
(`groups=` is passed to the search).

**Scoring.** AUROC for comparability with the literature; average precision because positives are rare (its
floor is the base rate, printed above the table, not 0.5). Grid search optimizes average precision.

**Grids are small on purpose.** With a few dozen positives, big grids overfit the inner folds. Current grids:

| Model | Grid | Fixed |
|---|---|---|
| Logistic regression | `C` in 0.01, 0.1, 1, 10 | standardized inputs |
| Decision tree | `max_depth` 2, 3, 4; `min_samples_leaf` 1, 5, 10 | |
| Random forest | `max_depth` 2, 4, none; `min_samples_leaf` 1, 5 | 300 trees |
| XGBoost | `learning_rate` 0.03, 0.1; `max_depth` 2, 3, 4 | 200 trees |

Widen a grid only when there are a few hundred positives, and add `n_estimators` or `subsample` for XGBoost then.

**Which model counts.** The proposal fixes logistic regression on the history features as the confirmatory M1
(column `m1`). The winner of the comparison table is kept as `m1_best` and reported as exploratory, with a note
that picking the best of four on the same folds is slightly optimistic.

## Adding a model

Add one entry to `MODELS` in section 5: a name, an unfitted estimator, and a small grid. It must have
`predict_proba` and accept the class weighting in some form. Everything else (nested search, table, saved
column `m1_<name>`) follows automatically. Good next candidates: LightGBM, an L1-regularized logistic regression
(to see which features survive), a small MLP (only with many more positives).

## What to report for every model

- AUROC with its 95% bootstrap interval, and average precision with the base rate.
- The settings chosen in each outer fold (if they differ a lot, the model is unstable at this sample size).
- Results against matched authentic posts and against fresh ones, separately, as well as pooled
  (filter `data.label` before scoring).
- The shuffled-history control next to it.

## After the simple models: graph models

1. **Snapshot GNN.** For each labeled post, cut the graph at its posting time and run a heterogeneous GNN
   (GraphSAGE or R-GCN, one weight matrix per link type) to classify the post node. Time enters as a feature on
   each link (days before the post).
2. **Temporal GNN (TGN, Rossi et al. 2020; or TGAT).** Reads the links as a time-ordered stream and keeps a memory
   per node, so order and bursts become signal. PyTorch Geometric ships an implementation; it is not installed
   in the shared environment yet (`pip install torch-geometric` on the login node).

For both: remove each labeled post's own `VARIANT_OF` and `SAME_AS` links before it is scored, use only links
dated before its posting time, and keep the same grouped folds. Expect them to need several hundred positives
before they beat the trees.
