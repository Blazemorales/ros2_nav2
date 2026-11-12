#!/usr/bin/env python3
"""End-to-end MCP smoke test against a running simulation (no LLM involved).

Exercises exactly the tool calls an LLM would make, through the same
restricted rover_mcp_safe server, over a real rosbridge:

  ros2 launch rover_bringup rover_mcp_sim.launch.py slam:=true headless:=true
  ~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_mcp_safe/smoke_test.py [--dx 2.0]

Steps: list topics/actions -> get_robot_pose -> try /cmd_vel (must be refused)
-> navigate_to dx metres ahead (must answer ARRIVED) -> set_exploration
off/on -> navigate_to far + concurrent stop_navigation (must answer CANCELED).
"""

import argparse
import asyncio
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastmcp import Client  # noqa: E402

import rover_mcp_safe as safe  # noqa: E402


def payload(res):
    """Best-effort extraction of the tool's dict result."""
    if getattr(res, "data", None) is not None:
        return res.data
    for c in getattr(res, "content", []) or []:
        txt = getattr(c, "text", None)
        if txt:
            try:
                return json.loads(txt)
            except ValueError:
                return txt
    return res


def text(res) -> str:
    return "\n".join(
        getattr(c, "text", "") for c in (getattr(res, "content", None) or [])
    )


async def main(dx: float, goal_timeout: float):
    results = {}
    async with Client(safe.build_server("nav")) as c:
        topics = payload(await c.call_tool("get_topics", {}))
        names = set(topics.get("topics", [])) if isinstance(topics, dict) else set()
        need = {"/cmd_vel", "/odom", "/scan", "/map"}
        results["topics"] = need <= names
        print(
            "[1] topics present:", sorted(need & names), "missing:", sorted(need - names)
        )

        actions = payload(await c.call_tool("get_actions", {}))
        results["actions"] = "/navigate_to_pose" in str(actions)
        print("[2] /navigate_to_pose action:", results["actions"])

        pose = text(await c.call_tool("get_robot_pose", {}))
        results["pose"] = "map frame" in pose
        print("[3]", pose)
        m = re.search(r"x=(-?[\d.]+) m, y=(-?[\d.]+) m, heading=(-?[\d.]+)", pose)
        x0, y0, h0 = (float(v) for v in m.groups()) if m else (0.0, 0.0, 0.0)

        try:
            await c.call_tool(
                "publish_once",
                {
                    "topic": "/cmd_vel",
                    "msg_type": "geometry_msgs/msg/Twist",
                    "msg": {"linear": {"x": 0.5}},
                },
            )
            results["cmd_vel_refused"] = False
        except Exception as e:  # noqa: BLE001
            results["cmd_vel_refused"] = True
            print("    refusal:", str(e)[:100])
        print("[4] /cmd_vel refused:", results["cmd_vel_refused"])

        gx, gy = x0 + dx * math.cos(math.radians(h0)), y0 + dx * math.sin(
            math.radians(h0)
        )
        print(f"[5] navigate_to {dx} m ahead -> ({gx:.2f}, {gy:.2f}) ...")
        r = text(
            await c.call_tool(
                "navigate_to",
                {"x": gx, "y": gy, "yaw_deg": h0, "timeout_s": goal_timeout},
            )
        )
        results["arrived"] = r.startswith("ARRIVED")
        print("    ", r)

        r1 = text(await c.call_tool("set_exploration", {"enabled": False}))
        r2 = text(await c.call_tool("set_exploration", {"enabled": True}))
        results["explore_toggle"] = "PAUSED" in r1 and "RESUMED" in r2
        print("[6] set_exploration off/on:", results["explore_toggle"])

        print("[7] navigate_to 10 m ahead, stop_navigation after 15 s ...")
        far = c.call_tool(
            "navigate_to",
            {
                "x": gx + 10 * math.cos(math.radians(h0)),
                "y": gy + 10 * math.sin(math.radians(h0)),
                "timeout_s": goal_timeout,
            },
        )
        nav = asyncio.create_task(far)
        await asyncio.sleep(15)
        print("    ", text(await c.call_tool("stop_navigation", {})))
        r = text(await nav)
        results["stop_cancels"] = r.startswith("CANCELED")
        print("    ", r)

    print("\nSUMMARY", json.dumps(results))
    return all(results.values())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dx", type=float, default=2.0)
    ap.add_argument("--goal-timeout", type=float, default=120.0)
    a = ap.parse_args()
    sys.exit(0 if asyncio.run(main(a.dx, a.goal_timeout)) else 1)
