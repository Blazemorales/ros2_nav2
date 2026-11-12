#!/usr/bin/env python3
"""PC-side agent for rover_web: dials OUT to the chat server and runs tool calls.

Runs on the PC with the simulation (outside the container), with the pipx venv
that already has ros-mcp/fastmcp:

  ~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_web/agent.py \
      --server wss://SEU-APP.onrender.com --token "$AGENT_TOKEN"

It builds the restricted rover_mcp_safe server in-process (profile "minimal":
navigate_to, run_mission, stop_navigation, set_exploration, get_robot_pose) and only ever
executes those. The safety policy stays on the PC, so a compromised web server
still cannot reach /cmd_vel or any other ROS interface.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import httpx
import websockets

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rover_mcp_safe"))

from fastmcp import Client  # noqa: E402

import rover_mcp_safe as safe  # noqa: E402


def _text(res) -> str:
    parts = [getattr(c, "text", "") for c in (getattr(res, "content", None) or [])]
    return "\n".join(p for p in parts if p)[:4000] or str(res)[:4000]


async def handle(ws, client: Client, allowed: set[str], msg: dict):
    name, args = msg.get("name", ""), msg.get("args") or {}
    print(f">>> {name}({args})", flush=True)
    if name not in allowed:
        out = f"ERROR: tool {name} is not available on this rover."
    else:
        try:
            out = _text(await client.call_tool(name, args))
        except Exception as e:  # noqa: BLE001 - ToolError, rosbridge down, ...
            out = f"ERROR: {e}"
    print(f"<<< {out[:200]}", flush=True)
    await ws.send(json.dumps({"type": "result", "id": msg.get("id"), "content": out}))


async def keep_awake(http_url: str):
    # Render's free plan sleeps after ~15 min without HTTP requests.
    async with httpx.AsyncClient(timeout=30) as http:
        while True:
            await asyncio.sleep(600)
            try:
                await http.get(f"{http_url}/health")
            except httpx.HTTPError:
                pass


async def session(server: str, token: str, profile: str):
    async with Client(safe.build_server(profile)) as client:
        tools = await client.list_tools()
        allowed = {t.name for t in tools}
        hello = {
            "type": "hello",
            "instructions": safe.INSTRUCTIONS,
            "tools": [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "inputSchema": t.inputSchema,
                }
                for t in tools
            ],
        }
        url = f"{server.rstrip('/')}/agent"
        # header, not ?token=: query strings end up in the server's access logs
        async with websockets.connect(
            url,
            additional_headers={"Authorization": f"Bearer {token}"},
            ping_interval=20,
            ping_timeout=60,
            max_size=2**20,
        ) as ws:
            await ws.send(json.dumps(hello))
            print(
                f"connected to {server} with tools: {', '.join(sorted(allowed))}",
                flush=True,
            )
            tasks = set()
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "call":
                    # concurrent: stop_navigation must run while navigate_to waits
                    t = asyncio.create_task(handle(ws, client, allowed, msg))
                    tasks.add(t)
                    t.add_done_callback(tasks.discard)


async def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--server",
        default=os.getenv("ROVER_WEB_SERVER", "ws://127.0.0.1:8000"),
        help="wss://<app>.onrender.com (ws:// for a local test)",
    )
    p.add_argument("--token", default=os.getenv("AGENT_TOKEN", ""))
    p.add_argument("--profile", default="minimal", choices=sorted(safe.PROFILES))
    a = p.parse_args()
    if not a.token:
        sys.exit("missing --token / AGENT_TOKEN")

    http_url = (
        a.server.replace("wss://", "https://").replace("ws://", "http://").rstrip("/")
    )
    asyncio.create_task(keep_awake(http_url))
    delay = 2
    while True:
        try:
            await session(a.server, a.token, a.profile)
            delay = 2
        except websockets.InvalidStatus as e:
            code = e.response.status_code
            print(f"server refused the agent (HTTP {code}); wrong token?", flush=True)
            if code in (401, 403):
                sys.exit(1)
        except (OSError, websockets.WebSocketException) as e:
            print(f"connection lost: {e}", flush=True)
        # Render free instances take ~1 min to wake up: back off, then retry.
        print(f"reconnecting in {delay} s ...", flush=True)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
