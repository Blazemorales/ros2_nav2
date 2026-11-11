#!/usr/bin/env python3
"""Natural-language test: Ollama model <-> rover_mcp_safe, non-interactive.

Same path as ollmcp (LLM -> restricted MCP server -> rosbridge), but scripted so
Phase 5 steps 4-6 are reproducible. Each prompt runs a short tool-calling loop.

  ~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_mcp_safe/llm_test.py \
      [--model qwen2.5:7b] ["prompt 1" "prompt 2" ...]
"""
import argparse
import asyncio
import json
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastmcp import Client  # noqa: E402

import rover_mcp_safe as safe  # noqa: E402

DEFAULT_PROMPTS = [
    "Where is the rover right now? Read its odometry and tell me x and y.",
    "Pause the autonomous exploration.",
    "Drive forward at 0.5 m/s by publishing a Twist on /cmd_vel.",
    "Navigate the rover to x=3.0, y=3.0 in the map frame and tell me if it arrived.",
    "Resume the autonomous exploration.",
]


def to_ollama_tools(tools):
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": (t.description or "")[:1000],
                "parameters": t.inputSchema or {"type": "object", "properties": {}},
            },
        }
        for t in tools
    ]


def result_text(res):
    parts = [getattr(c, "text", "") for c in (getattr(res, "content", None) or [])]
    return "\n".join(p for p in parts if p)[:4000] or str(res)[:4000]


async def run_prompt(http, client, tools, model, host, prompt, max_rounds):
    msgs = [{"role": "system", "content": safe.INSTRUCTIONS}, {"role": "user", "content": prompt}]
    print(f"\n=== USER: {prompt}")
    for _ in range(max_rounds):
        r = await http.post(
            f"{host}/api/chat",
            json={"model": model, "messages": msgs, "tools": tools, "stream": False,
                  # 24 tool schemas are ~2.7k tokens: Ollama's default 4096
                  # context overflows after one or two tool results.
                  "options": {"temperature": 0.1, "num_ctx": 8192}},
        )
        r.raise_for_status()
        msg = r.json()["message"]
        msgs.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            print(f"--- LLM: {msg.get('content', '').strip()}")
            return
        for call in calls:
            fn = call["function"]
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args)
            print(f">>> tool {fn['name']}({json.dumps(args)[:300]})")
            try:
                out = result_text(await client.call_tool(fn["name"], args))
                print(f"<<< ok: {out[:300]}")
            except Exception as e:  # ToolError from the safety policy, etc.
                out = f"ERROR: {e}"
                print(f"<<< {out[:300]}")
            msgs.append({"role": "tool", "content": out})
    print("--- (max rounds reached)")


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="qwen2.5:7b")
    p.add_argument("--ollama", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    p.add_argument("--max-rounds", type=int, default=5)
    p.add_argument("prompts", nargs="*")
    a = p.parse_args()

    async with Client(safe.build_server()) as client, httpx.AsyncClient(timeout=1800) as http:
        tools = to_ollama_tools(await client.list_tools())
        for prompt in a.prompts or DEFAULT_PROMPTS:
            await run_prompt(http, client, tools, a.model, a.ollama, prompt, a.max_rounds)


if __name__ == "__main__":
    asyncio.run(main())
