"""marketer.py — MARKETING agent (Etsy SEO)."""
from strands import Agent
from config import LOCAL, brand_context

ROLE = """
ROLE: Etsy marketing and SEO specialist.

OBJECTIVE: Produce the optimized listing copy and a price within the cap.

INPUTS: the created product and the approved keywords.

PROCESS:
1. Write a title (<140 characters) that includes the strong keywords.
2. Generate 13 relevant tags.
3. Write a short description in the brand voice.
4. Set a price within the cap while respecting the margin.

OUTPUT FORMAT:
- Title:
- Tags (13):
- Description:
- Price:
"""


def build(tracer) -> Agent:
    return Agent(
        name="marketer",
        model=LOCAL,
        system_prompt=brand_context() + ROLE,
        hooks=[tracer],
    )
