"""Settings. The class run and the paper run differ only here."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / os.environ.get("MOZAR_DATA", "data")   # MOZAR_DATA=sample_data reads the small sample in the repo
MODELS = ROOT / "models"
RESULTS = ROOT / "results"

SUBREDDITS = [
    "pics", "OldSchoolCool",                                                # kept from before
    "interestingasfuck", "Damnthatsinteresting", "nextfuckinglevel",        # viral images
    "PoliticalHumor", "conspiracy", "Conservative", "PropagandaPosters",     # political
    "Fauxmoi", "popculturechat",                                            # celebrity
    "shittymoviedetails", "marvelstudios",                                  # movies
    "aww", "food",                                                          # calm controls
]
AFTER = os.environ.get("MOZAR_AFTER", "2026-10-08")    # inclusive, UTC
BEFORE = os.environ.get("MOZAR_BEFORE", "2026-11-08")  # exclusive, UTC

# Archive client
ARCHIVE = "https://arctic-shift.photon-reddit.com"
ARCHIVE_GAP = 1.5       # seconds between archive requests
IMAGE_WORKERS = 4       # parallel image downloads (Reddit's image host, not the archive)

# Pair finding and pixel comparison (starting values, to be tuned)
HASH_MAX_BITS = 10      # look-alike if perceptual hashes differ in at most this many of 64 bits
REPOST_MAX = 0.005      # under 0.5% of pixels changed: repost
EDIT_MAX = 0.40         # over 40% changed: unrelated

# Labeling model (runs on the GPU node from the local copy in MODELS)
JUDGE_MODEL = os.environ.get("MOZAR_JUDGE", "Qwen/Qwen3-VL-32B-Instruct")  # needs an 80 GB GPU (H100); the 8B was too inconsistent

# Histories
HISTORY_DAYS = 180
FRESH_PER_MANIPULATED = 3
