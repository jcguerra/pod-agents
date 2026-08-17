"""
config.py — Central project configuration.
==========================================
Single place for: store data, models (local/hosted), the database URL and the
brand context shared by every agent.
"""

import os

from dotenv import load_dotenv
from strands.models.ollama import OllamaModel

load_dotenv()  # read .env from the project root


# ---------------------------------------------------------------------------
# Store data (business shared state — not embedded inside the prompts)
# ---------------------------------------------------------------------------
STORE_CONFIG = {
    "brand": "Oruga Digital",
    "brand_voice": "friendly, with subtle humor, minimalist aesthetic",
    "pod_provider": "Printify",
    "target_margin": 0.40,
    "max_price": 35.0,
    "trademark_blocklist": ["disney", "nike", "taylor swift", "star wars", "pokemon"],
}


# ---------------------------------------------------------------------------
# Planning lead times (business rule)
# ---------------------------------------------------------------------------
# Seasonal work must run ahead of the holiday: research/suggest niches ~90 days
# out, publish ~60 days out, because Etsy's algorithm takes ~30 days to pick up
# and rank a new listing. Niche suggestions are anchored on the holidays that
# fall `suggest_lead_days` ahead of today.
PLANNING = {
    "suggest_lead_days": 90,   # research/suggest niches this far before the holiday
    "publish_lead_days": 60,   # publish this far before the holiday
    "algo_pickup_days": 30,    # ~time Etsy needs to recognize/rank a new listing
}


# ---------------------------------------------------------------------------
# Database (persistent state — the "bases" from the operations manual)
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://pod:pod_local_dev@localhost:5432/pod_agents"
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
# LOCAL: your qwen3.5:9b via Ollama. Wide max_tokens so it does not get cut off.
# IMPORTANT: think=False disables qwen3's "thinking". With thinking on, the model
# dumps everything into an internal reasoning field (content stays empty) and
# exhausts max_tokens before answering -> MaxTokensReachedException. Disabling it
# is also much faster (seconds vs. ~100s per node on 16GB).
LOCAL = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen3.5:9b",
    temperature=0.3,
    keep_alive="30m",
    max_tokens=8192,   # headroom: a rambling node can still exceed this -> MaxTokensReached
    additional_args={"think": False},
)

# HOSTED: for real use, put VALIDATION on a hosted model (more reliable at
# following instructions). Defaults to LOCAL so everything runs without an API key.
# To enable: uncomment these two lines, comment HOSTED = LOCAL, and export
# ANTHROPIC_API_KEY.
# from strands.models.anthropic import AnthropicModel
# HOSTED = AnthropicModel(model_id="claude-sonnet-4-5", max_tokens=1024)
HOSTED = LOCAL


# ---------------------------------------------------------------------------
# Brand context — prepended to every agent's role
# ---------------------------------------------------------------------------
def brand_context() -> str:
    c = STORE_CONFIG
    return (
        "BRAND CONTEXT:\n"
        f"- POD store: '{c['brand']}' on Etsy.\n"
        f"- Brand voice: {c['brand_voice']}.\n"
        f"- Print provider: {c['pod_provider']}.\n"
        f"- Minimum acceptable margin: {int(c['target_margin'] * 100)}%.\n"
        f"- Max price per product: ${c['max_price']}.\n"
    )
