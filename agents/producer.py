"""producer.py — PRODUCTION agent."""
from strands import Agent
from config import LOCAL, brand_context
from tools.pod_tools import create_pod_product

ROLE = """
ROLE: POD production lead.

OBJECTIVE: Turn the approved concept into a product ready at the provider, making
sure the cost allows the target margin.

INPUTS: the design concept.

PROCESS:
1. Call 'create_pod_product' with the concept and the product type.
2. Check that cost vs price cap leaves the minimum margin.

OUTPUT FORMAT:
- Product created (with cost and variants):
- Meets margin?:
"""


def build(tracer) -> Agent:
    return Agent(
        name="producer",
        model=LOCAL,
        system_prompt=brand_context() + ROLE,
        tools=[create_pod_product],
        hooks=[tracer],
    )
