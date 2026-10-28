"""Shared paths and local-only environment; no third-party dependencies."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/lab.json").read_text())
DEFAULT_STEPS = tuple(CONFIG.get("seed_vc_default_steps", [30]))

def variant_filename(label, mixed=False):
    """Single runs have no version suffix; keep historical comparison filenames."""
    suffix = "" if label == "single" else "_" + label
    return f"seed-vc{suffix}{'_mix' if mixed else ''}_AI.wav"

def local_env(offline=True):
    env = os.environ.copy()
    for key, rel in {
        "UV_CACHE_DIR": ".cache/uv", "PIP_CACHE_DIR": ".cache/pip",
        "HF_HOME": ".cache/huggingface", "TORCH_HOME": ".cache/torch",
        "XDG_CACHE_HOME": ".cache", "NUMBA_CACHE_DIR": ".cache/numba",
        "MPLCONFIGDIR": ".cache/matplotlib",
    }.items():
        env[key] = str(ROOT / rel)
    env.update(HF_HUB_DISABLE_TELEMETRY="1", GRADIO_ANALYTICS_ENABLED="False",
               DO_NOT_TRACK="1", PIP_CONFIG_FILE=os.devnull,
               PIP_INDEX_URL="https://pypi.org/simple", PIP_EXTRA_INDEX_URL="",
               PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONNOUSERSITE="1")
    env.pop("HF_ENDPOINT", None)
    if offline:
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    return env
