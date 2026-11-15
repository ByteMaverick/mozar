# Papers, by topic

Entries marked **verified** were checked against primary records on 14 November 2026 (see `docs/bibliography.md`,
which holds the full list of 90+ entries with notes). Entries marked **check** came from later research notes or
memory: confirm them before citing.

## Image forensics detectors (M0)

- **FLAME** (verified). Y. Wang, B. Wu, Q. Li, J. Chen, T. Zhang, S. Ji. *Order within Chaos: Capturing Intrinsic
  Energy Anomalies for AI-Manipulated Image Forgery Localization.* ICML 2026, PMLR 306:131220–131246.
  Our strongest detector. Trained on MagicBrush and SID-Set edits.
- **TruFor** (verified). F. Guillaro, D. Cozzolino, A. Sud, N. Dufour, L. Verdoliva. *TruFor: Leveraging All-Round
  Clues for Trustworthy Image Forgery Detection and Localization.* CVPR 2023, pp. 20606–20615.
  Gives a score, a localization map and a reliability map.
- **CAT-Net** (verified). M.-J. Kwon, S.-H. Nam, I.-J. Yu, H.-K. Lee, C. Kim. *Learning JPEG Compression Artifacts
  for Image Manipulation Detection and Localization.* IJCV 130(8):1875–1895, 2022. The fallback detector.
- **IML-ViT** (verified, arXiv 2307.14863) and **Mesorch** (verified, AAAI 2025): other localizers named in the
  related work.
- **SIDA** (verified). Z. Huang et al. *SIDA: Social Media Image Deepfake Detection, Localization and Explanation
  with Large Multimodal Model.* CVPR 2025, pp. 28831–28841.

## Forgery datasets and robustness

- **TGIF** (verified). H. Mareen, D. Karageorgiou, G. Van Wallendael, P. Lambert, S. Papadopoulos. *TGIF:
  Text-Guided Inpainting Forgery Dataset.* IEEE WIFS 2024. Our detector sanity check (E0), with JPEG and WEBP
  variants. Reports TruFor falling from about 0.83 to 0.32 pixel-F1 at JPEG quality 80 (check the exact figure).
- **MagicBrush** (verified). K. Zhang, L. Mo, W. Chen, H. Sun, Y. Su. NeurIPS 2023 Datasets and Benchmarks.
- **Inpainting Exchange** (check). Nebioglu, Bilgic, Popescu. arXiv 2602.00192. Pasting the inpainted region back
  onto the original drops detectors from above 90% to about 55% accuracy.
- **MIMLv2** (check). Qu et al. arXiv 2508.20987. Adding synthetic forgeries to training lowered accuracy on real
  forgeries; real web forgeries raised it.

## Social context for misinformation

- **Fakeddit** (verified). K. Nakamura, S. Levy, W. Y. Wang. LREC 2020, pp. 6149–6157. Labels assigned by
  subreddit, which is why we do not use its labels.
- **RIFT** (verified). P. Joshi. *RIFT - Reddit Information Falsity Tagger.* Master's Project 1550, SJSU, 2025.
  Our graph schema follows it.
- **Castillo et al. 2011** (verified, WWW): credibility from account and message features.
- **Shu et al. 2019** (verified, ASONAM): user profiles alone predict who shares fake news.
- **Vosoughi, Roy, Aral 2018** (verified, Science 359:1146–1151): false news spreads differently.
- **Graph models for fake news** (all verified): Bi-GCN (AAAI 2020), GCAN (ACL 2020), FANG (CIKM 2020),
  UPFD (SIGIR 2021), dEFEND (KDD 2019).

## Evaluation pitfalls

- **Mu, Bontcheva, Aletras 2023** (verified, Findings of EACL): random splits inflate rumor-detection F1 by 35 to 44
  points over chronological splits.
- **Karnam et al. 2026, cold users** (verified, ICWSM 20): Fakeddit accuracy 0.93 for seen users, 0.72 to 0.76 for
  unseen ones. Why we split by account.
- **Kapoor and Narayanan 2023** (check). *Leakage and the Reproducibility Crisis in Machine-Learning-based Science.*
  Patterns 4(9). Oversampling before splitting is a leak.
- **Collins, Ogundimu, Altman 2016** (check). Statistics in Medicine. At least 100 events, ideally 200, to validate a
  prediction model.

## Fusion and calibration

- **Saerens, Latinne, Decaestecker 2002** (verified). *Adjusting the Outputs of a Classifier to New a Priori
  Probabilities.* Neural Computation 14(1):21–41. The prior-shift reading of late fusion.
- **Wolpert 1992** (verified). *Stacked generalization.* Neural Networks 5(2):241–259.
- **Platt 1999** (verified). *Probabilistic Outputs for Support Vector Machines.* Platt scaling, used to recalibrate M0.

## Graphs

- **GraphSAGE** (verified). W. L. Hamilton, R. Ying, J. Leskovec. NeurIPS 2017. The planned snapshot GNN.
- **TGN** (check). E. Rossi et al. *Temporal Graph Networks for Deep Learning on Dynamic Graphs.* arXiv 2006.10637,
  2020. The planned time-aware GNN.
- **GADBench** (check). J. Tang et al. NeurIPS 2023, arXiv 2306.12251. Tree models beat specialized GNNs on real
  graph anomalies.
- **BOND** (check). K. Liu et al. NeurIPS 2022, arXiv 2206.10071. Injected anomalies are easy; real ones are not.

## Matching images

- **Zannettou et al. 2018** (verified). *On the Origins of Memes by Means of Fringe Web Communities.* IMC 2018,
  pp. 188–202. Perceptual hashing to track image variants across communities; our step 3 follows it.
- **DINOv2** (verified). M. Oquab et al. TMLR 2024. The planned second matcher for crops and screenshots.

## Imbalanced learning (for the notebook)

All **check**: SMOTE (Chawla et al., JAIR 2002); focal loss (Lin et al., ICCV 2017); the credit-card fraud dataset
(Dal Pozzolo et al. 2015, 0.17% positives); the Elliptic Bitcoin dataset (Weber et al., KDD 2019 workshop, about 2%).

## Synthetic data

The research behind `docs/synthetic_data_proposal.md`, with sources marked opened or not, is in the project's
`research_notes/Synthetic data for manipulation detection/` (on Mohammed's machine; ask for a copy).
