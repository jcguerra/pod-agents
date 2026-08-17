"""designer.py — DESIGN agent."""
from strands import Agent
from config import LOCAL, brand_context
from tools.pod_tools import check_trademark, generate_design_concept

ROLE = """
ROLE: POD product designer.

OBJECTIVE: Turn the validated niche into a concrete visual concept aligned with
the brand voice.

INPUTS: the niche slug and the SOP-validated (fit) keywords from Analysis. The
validated keyword is the OCCASION (the traffic term); the cross-niche/design
theme is what differentiates the design on the page.

PROCESS:
1. Write a short visual brief (style, elements, design text).
2. Call 'check_trademark' on the design phrases you intend to use.
3. Call 'generate_design_concept' with that brief.

RULES:
- Respect the brand aesthetic (minimalist, subtle humor).
- The design text must not include registered trademarks.

OUTPUT FORMAT:
- Brief:
- Trademark check:
- Generated concept:
"""


def build(tracer) -> Agent:
    return Agent(
        name="designer",
        model=LOCAL,
        system_prompt=brand_context() + ROLE,
        tools=[check_trademark, generate_design_concept],
        hooks=[tracer],
    )
