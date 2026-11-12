#!/usr/bin/env python3
"""rover_web: public chat page that commands the simulated rover through an LLM.

Runs on Render (or any host). The rover's PC is behind a NAT, so it is the PC
that dials in: tools/rover_web/agent.py opens an outbound WebSocket to /agent,
announces its MCP tools, and executes tool calls locally through the restricted
rover_mcp_safe proxy. No port of the PC is exposed to the internet.

  browser --ws /chat--> server.py --HTTPS--> LLM API (Groq, OpenAI-compatible)
                            |
                            +--ws /agent--> agent.py (PC) -> rover_mcp_safe -> rosbridge -> ROS 2

Environment:
  LLM_API_KEY      key of the OpenAI-compatible provider (required)
  LLM_BASE_URL     default https://api.groq.com/openai/v1
  LLM_MODEL        default llama-3.3-70b-versatile
  AGENT_TOKEN      shared secret the PC agent must present (required)
  CHAT_PASSWORD    password the browser must send (required)
  PORT             listen port (Render sets it)
"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import pathlib
import time
import uuid

import httpx
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
AGENT_TOKEN = os.getenv("AGENT_TOKEN", "")
CHAT_PASSWORD = os.getenv("CHAT_PASSWORD", "")
MAX_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "6"))
MAX_HISTORY = 20  # messages kept per browser session (keeps free-tier token use low)

HERE = pathlib.Path(__file__).parent


def _same(a: str, b: str) -> bool:
    return bool(a) and bool(b) and hmac.compare_digest(a.encode(), b.encode())


# --------------------------------------------------------------------------- #
# Agent link (exactly one PC agent at a time)
# --------------------------------------------------------------------------- #


class AgentLink:
    def __init__(self):
        self.ws: WebSocket | None = None
        self.tools: list[dict] = []
        self.instructions = ""
        self.pending: dict[str, asyncio.Future] = {}
        self.since = 0.0

    @property
    def online(self) -> bool:
        return self.ws is not None

    async def call(self, name: str, args: dict, timeout: float = 3600.0) -> str:
        if not self.ws:
            return "ERROR: the rover is offline (the agent on the PC is not connected)."
        cid = uuid.uuid4().hex
        fut = asyncio.get_running_loop().create_future()
        self.pending[cid] = fut
        try:
            await self.ws.send_json(
                {"type": "call", "id": cid, "name": name, "args": args}
            )
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            return f"ERROR: tool {name} did not answer within {timeout:.0f} s."
        except Exception as e:  # noqa: BLE001 - agent dropped mid-call
            return f"ERROR: lost the rover connection during {name}: {e}"
        finally:
            self.pending.pop(cid, None)

    def drop(self):
        self.ws = None
        for fut in self.pending.values():
            if not fut.done():
                fut.set_result("ERROR: the rover agent disconnected.")
        self.pending.clear()


agent = AgentLink()


async def agent_ws(ws: WebSocket):
    # Token in a header, never in the URL: uvicorn/Render access logs record
    # the full path including the query string.
    auth = ws.headers.get("authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else ""
    if not _same(token, AGENT_TOKEN):
        await ws.close(code=4401)
        return
    await ws.accept()
    hello = await ws.receive_json()
    if agent.ws is not None:  # a newer agent replaces a stale one
        try:
            await agent.ws.close(code=4000)
        except Exception:  # noqa: BLE001
            pass
        agent.drop()
    agent.ws, agent.since = ws, time.time()
    agent.tools = hello.get("tools", [])
    agent.instructions = hello.get("instructions", "")
    print(f"agent connected with {len(agent.tools)} tools", flush=True)
    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "result":
                fut = agent.pending.get(msg.get("id"))
                if fut and not fut.done():
                    fut.set_result(str(msg.get("content", "")))
    except WebSocketDisconnect:
        pass
    finally:
        if agent.ws is ws:
            agent.drop()
            print("agent disconnected", flush=True)


# --------------------------------------------------------------------------- #
# LLM loop
# --------------------------------------------------------------------------- #


def _openai_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", "")[:1000],
                "parameters": t.get("inputSchema")
                or {"type": "object", "properties": {}},
            },
        }
        for t in agent.tools
    ]


async def _llm(http: httpx.AsyncClient, messages: list[dict]) -> dict:
    r = await http.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={
            "model": LLM_MODEL,
            "messages": messages,
            "tools": _openai_tools(),
            "tool_choice": "auto",
            "temperature": 0.1,
        },
    )
    if r.status_code == 429:
        raise RuntimeError(
            "the free LLM quota is exhausted for now; wait a minute and retry"
        )
    if r.status_code >= 400:
        raise RuntimeError(f"LLM API error {r.status_code}: {r.text[:300]}")
    return r.json()["choices"][0]["message"]


async def run_turn(
    ws: WebSocket, http: httpx.AsyncClient, history: list[dict], text: str
):
    history.append({"role": "user", "content": text})
    system = {"role": "system", "content": agent.instructions or "You control a rover."}
    for _ in range(MAX_ROUNDS):
        msg = await _llm(http, [system] + history[-MAX_HISTORY:])
        calls = msg.get("tool_calls") or []
        history.append(
            {
                "role": "assistant",
                "content": msg.get("content") or "",
                **({"tool_calls": calls} if calls else {}),
            }
        )
        if not calls:
            await ws.send_json(
                {"type": "reply", "text": msg.get("content") or "(sem resposta)"}
            )
            return
        for c in calls:
            fn = c["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                args = {}
            await ws.send_json({"type": "tool", "name": fn["name"], "args": args})
            out = await agent.call(fn["name"], args)
            await ws.send_json({"type": "tool_result", "name": fn["name"], "text": out})
            history.append({"role": "tool", "tool_call_id": c["id"], "content": out})
    await ws.send_json(
        {"type": "reply", "text": "(parei: muitas chamadas de ferramenta seguidas)"}
    )


async def chat_ws(ws: WebSocket):
    await ws.accept()
    try:
        auth = await ws.receive_json()
        if not _same(auth.get("password", ""), CHAT_PASSWORD):
            await ws.send_json({"type": "error", "text": "senha incorreta"})
            await ws.close(code=4401)
            return
        await ws.send_json({"type": "status", "online": agent.online})
        history: list[dict] = []
        busy: asyncio.Task | None = None
        async with httpx.AsyncClient(timeout=120) as http:
            while True:
                msg = await ws.receive_json()
                if msg.get("type") == "stop":
                    # Emergency stop: straight to the agent, not through the LLM, and
                    # allowed while a navigate_to is still running.
                    await ws.send_json(
                        {"type": "tool", "name": "stop_navigation", "args": {}}
                    )
                    out = await agent.call("stop_navigation", {}, timeout=30)
                    await ws.send_json(
                        {"type": "tool_result", "name": "stop_navigation", "text": out}
                    )
                elif msg.get("type") == "status":
                    await ws.send_json({"type": "status", "online": agent.online})
                elif msg.get("type") == "chat":
                    if busy and not busy.done():
                        await ws.send_json(
                            {
                                "type": "error",
                                "text": "ainda estou executando o pedido anterior",
                            }
                        )
                        continue
                    if not agent.online:
                        await ws.send_json(
                            {
                                "type": "error",
                                "text": "rover offline: rode o "
                                "agent.py no PC com a simulação",
                            }
                        )
                        continue

                    async def turn(text=str(msg.get("text", ""))[:2000]):
                        try:
                            await run_turn(ws, http, history, text)
                        except Exception as e:  # noqa: BLE001
                            await ws.send_json({"type": "error", "text": str(e)})

                    busy = asyncio.create_task(turn())
    except WebSocketDisconnect:
        pass


# --------------------------------------------------------------------------- #


async def index(_):
    return FileResponse(HERE / "index.html")


async def health(_):
    return JSONResponse({"ok": True, "agent_online": agent.online, "model": LLM_MODEL})


app = Starlette(
    routes=[
        Route("/", index),
        Route("/health", health),
        WebSocketRoute("/agent", agent_ws),
        WebSocketRoute("/chat", chat_ws),
    ]
)

if __name__ == "__main__":
    import uvicorn

    missing = [
        k for k in ("LLM_API_KEY", "AGENT_TOKEN", "CHAT_PASSWORD") if not os.getenv(k)
    ]
    if missing:
        print(f"warning: missing env {', '.join(missing)}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
