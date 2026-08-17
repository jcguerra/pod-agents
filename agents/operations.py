"""operations.py — OPERATIONS agent (publishing with human gate)."""
from strands import Agent
from config import LOCAL, brand_context
from tools.pod_tools import publish_etsy_listing

ROLE = """
ROLE: Operations / publishing.

OBJECTIVE: Leave the listing as DRAFT and summarize what is pending approval.

INPUTS: the title and price defined by Marketing.

PROCESS:
1. Call 'publish_etsy_listing' with the title and price (stays as DRAFT).
2. Do NOT publish definitively: that requires human approval.

OUTPUT FORMAT:
- Listing status (DRAFT):
- Pending human approval:
"""


def build(tracer) -> Agent:
    return Agent(
        name="operations",
        model=LOCAL,
        system_prompt=brand_context() + ROLE,
        tools=[publish_etsy_listing],
        hooks=[tracer],
    )
