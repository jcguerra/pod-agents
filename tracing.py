"""
tracing.py — Per-node and per-tool tracing using Strands hooks.
"""

import time
from strands.hooks import (
    HookProvider, HookRegistry,
    BeforeNodeCallEvent, AfterNodeCallEvent,
    BeforeToolCallEvent, AfterToolCallEvent,
)


class Tracer(HookProvider):
    """Times nodes and logs every tool call. Hooks into the graph (node events)
    and into each agent (tool events)."""

    def __init__(self):
        self._node_t0 = {}
        self._tool_t0 = {}

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeNodeCallEvent, self._before_node)
        registry.add_callback(AfterNodeCallEvent, self._after_node)
        registry.add_callback(BeforeToolCallEvent, self._before_tool)
        registry.add_callback(AfterToolCallEvent, self._after_tool)

    def _before_node(self, event: BeforeNodeCallEvent) -> None:
        self._node_t0[event.node_id] = time.perf_counter()
        print(f"▶  {event.node_id:<14} │ start")

    def _after_node(self, event: AfterNodeCallEvent) -> None:
        t0 = self._node_t0.pop(event.node_id, None)
        dt = f"{time.perf_counter() - t0:6.2f}s" if t0 else "   ?  "
        print(f"✔  {event.node_id:<14} │ end{'':>36}{dt}")

    @staticmethod
    def _tool_info(event):
        tu = getattr(event, "tool_use", None)
        if isinstance(tu, dict):
            name = tu.get("name", "?")
            tid = tu.get("toolUseId", name)
            args = tu.get("input", {})
        else:
            name = getattr(getattr(event, "selected_tool", None), "tool_name", "?")
            tid, args = name, {}
        arg_str = ", ".join(f"{k}={v!r}" for k, v in list(args.items())[:2])
        if len(arg_str) > 48:
            arg_str = arg_str[:45] + "..."
        return name, tid, arg_str

    def _before_tool(self, event: BeforeToolCallEvent) -> None:
        _, tid, _ = self._tool_info(event)
        self._tool_t0[tid] = time.perf_counter()

    def _after_tool(self, event: AfterToolCallEvent) -> None:
        name, tid, arg_str = self._tool_info(event)
        t0 = self._tool_t0.pop(tid, None)
        dt = f"{time.perf_counter() - t0:5.2f}s" if t0 else "  ?  "
        status = "ERR" if getattr(event, "exception", None) else "ok "
        label = f"   ↳ tool {name}({arg_str})"
        print(f"{label:<58} {status} {dt}")
