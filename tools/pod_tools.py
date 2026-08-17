"""
pod_tools.py — POD flow tools (trademark, design, production, publishing).
Mocked: each one marks where the real integration goes.
"""

from strands import tool
from config import STORE_CONFIG


# Pure logic (testable without a model and reusable by the deterministic verdict).
def trademark_risk(phrase: str):
    """Return (has_risk: bool, message: str) checking the trademark blocklist."""
    # >>> REAL INTEGRATION: USPTO TESS / EUIPO / a trademark screening service.
    phrase_low = (phrase or "").lower()
    for brand in STORE_CONFIG["trademark_blocklist"]:
        if brand in phrase_low:
            return True, f"HIGH RISK: contains a protected trademark ('{brand}'). Do not use."
    return False, "OK: no match in the blocklist. (Manual review if in doubt.)"


@tool
def check_trademark(phrase: str) -> str:
    """Check whether a phrase/design brushes against a registered trademark. CRITICAL in POD.

    Args:
        phrase: the design text or concept to verify
    """
    _, message = trademark_risk(phrase)
    return f"'{phrase}': {message}"


@tool
def generate_design_concept(brief: str) -> str:
    """Generate a visual concept (prompt + description) from a brief.

    Args:
        brief: description of the desired design (style, elements, text)
    """
    # >>> REAL INTEGRATION: image generator (Ideogram, SDXL, etc.)
    return (f"Concept for '{brief}': minimalist vector illustration, 2-color palette, "
            f"geometric sans. File: concept_v1.svg (300 DPI, 4500x5400px).")


@tool
def create_pod_product(concept: str, product_type: str = "t-shirt") -> str:
    """Create the product at the POD provider (mockup + variants + cost).

    Args:
        concept: the approved design concept
        product_type: t-shirt, mug, poster, etc.
    """
    # >>> REAL INTEGRATION: Printify / Printful API
    return (f"POD product created at {STORE_CONFIG['pod_provider']}: {product_type} with "
            f"'{concept}'. Base cost $12.50 · Mockups: 3 · Variants: S-XXL, 4 colors.")


@tool
def publish_etsy_listing(title: str, price: float) -> str:
    """Leave the listing as DRAFT on Etsy. Publishing is IRREVERSIBLE: needs human approval.

    Args:
        title: listing title
        price: sale price in USD
    """
    # >>> REAL INTEGRATION: Etsy API (createDraftListing). Do not publish without approval.
    return f"[DRAFT created, pending human approval] '{title}' at ${price:.2f}."
