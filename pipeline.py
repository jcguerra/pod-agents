"""
pipeline.py — Two-stage flow, split around the human eRank gate.
================================================================
Stage 1 (discovery): the DIRECTOR (LLM) picks the seasonal occasion + niche;
then main.py deterministically generates and stages the 20-keyword block (the
block generation is deterministic by SOP, so it does not depend on a flaky local
tool-call). Ends by handing the human a block to run in eRank's Bulk Tool.

  [human: eRank Bulk Tool -> CSV -> python -m tools.import_erank <csv> <niche>]

Stage 2 (production): design -> production -> marketing -> operations. Runs only
after main.py has confirmed (deterministically) that the niche survived SOP
validation on the imported data.
"""

from strands.multiagent import GraphBuilder

from tracing import Tracer
from agents import (
    designer, producer, marketer, operations,
)


def build_production_graph():
    """Stage 2: turn a validated niche into a published DRAFT listing."""
    tracer = Tracer()
    nodes = {
        "design":     designer.build(tracer),
        "production": producer.build(tracer),
        "marketing":  marketer.build(tracer),
        "operations": operations.build(tracer),
    }
    b = GraphBuilder()
    for node_id, agent in nodes.items():
        b.add_node(agent, node_id)
    b.add_edge("design", "production")
    b.add_edge("production", "marketing")
    b.add_edge("marketing", "operations")
    b.set_entry_point("design")
    b.set_max_node_executions(10)
    b.set_hook_providers([tracer])
    return b.build()
