#!/usr/bin/env python3
"""End-to-end MCP smoke test against a running simulation (no LLM involved).

Exercises exactly the tool calls an LLM would make, through the same
restricted rover_mcp_safe server, over a real rosbridge:

  ros2 launch rover_bringup rover_mcp_sim.launch.py slam:=true headless:=true
  ~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_mcp_safe/smoke_test.py [--dx 2.0]

Steps: list topics/actions -> read /odom -> try /cmd_vel (must be refused)
-> Nav2 goal dx metres ahead in the map frame -> read /odom again
-> pause/resume explore_lite via /explore/resume.
"""
import argparse
import asyncio
import json
import math
import os
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


def find_pose(obj):
    """Find the first {'position': {...}} in a nested result."""
    if isinstance(obj, dict):
        if "position" in obj and isinstance(obj["position"], dict) and "x" in obj["position"]:
            return obj["position"]
        for v in obj.values():
            p = find_pose(v)
            if p:
                return p
    elif isinstance(obj, list):
        for v in obj:
            p = find_pose(v)
            if p:
                return p
    return None


async def odom(c):
    r = payload(await c.call_tool("subscribe_once", {"topic": "/odom",
                                                     "msg_type": "nav_msgs/msg/Odometry",
                                                     "timeout": 5.0}))
    return find_pose(r)


async def main(dx: float, goal_timeout: float):
    results = {}
    async with Client(safe.build_server()) as c:
        topics = payload(await c.call_tool("get_topics", {}))
        names = set(topics.get("topics", [])) if isinstance(topics, dict) else set()
        need = {"/cmd_vel", "/odom", "/scan", "/map"}
        results["topics"] = need <= names
        print("[1] topics present:", sorted(need & names), "missing:", sorted(need - names))

        actions = payload(await c.call_tool("get_actions", {}))
        results["actions"] = "/navigate_to_pose" in str(actions)
        print("[2] /navigate_to_pose action:", results["actions"])

        p0 = await odom(c)
        results["odom"] = p0 is not None
        print("[3] /odom position:", p0)

        try:
            await c.call_tool("publish_once", {"topic": "/cmd_vel",
                                               "msg_type": "geometry_msgs/msg/Twist",
                                               "msg": {"linear": {"x": 0.5}}})
            results["cmd_vel_refused"] = False
        except Exception as e:  # noqa: BLE001
            results["cmd_vel_refused"] = "Refused" in str(e)
        print("[4] /cmd_vel refused:", results["cmd_vel_refused"])

        goal = {"pose": {"header": {"frame_id": "map"},
                         "pose": {"position": {"x": (p0 or {}).get("x", 0.0) + dx,
                                               "y": (p0 or {}).get("y", 0.0), "z": 0.0},
                                  "orientation": {"w": 1.0}}}}
        print(f"[5] navigate_to_pose +{dx} m ...")
        r = payload(await c.call_tool("send_action_goal", {
            "action_name": "/navigate_to_pose",
            "action_type": "nav2_msgs/action/NavigateToPose",
            "goal": goal, "timeout": goal_timeout}))
        print("    result:", str(r)[:300])
        p1 = await odom(c)
        moved = math.dist((p0["x"], p0["y"]), (p1["x"], p1["y"])) if p0 and p1 else 0.0
        results["goal_moved"] = moved > 0.5 * dx
        print(f"    /odom after: {p1}  moved {moved:.2f} m")

        ok = True
        for v in (False, True):
            r = payload(await c.call_tool("publish_once", {"topic": "/explore/resume",
                                                           "msg_type": "std_msgs/msg/Bool",
                                                           "msg": {"data": v}}))
            ok &= "error" not in str(r).lower()
        results["explore_toggle"] = ok
        print("[6] /explore/resume false->true published:", ok)

    print("\nSUMMARY", json.dumps(results))
    return all(results.values())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dx", type=float, default=2.0)
    ap.add_argument("--goal-timeout", type=float, default=120.0)
    a = ap.parse_args()
    sys.exit(0 if asyncio.run(main(a.dx, a.goal_timeout)) else 1)
