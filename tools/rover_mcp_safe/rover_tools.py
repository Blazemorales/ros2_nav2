"""High-level rover operations over rosbridge, exposed as dedicated MCP tools.

Why these exist (see the LLM test in hugoplate/content/english/pages/ros-mcp.md):
  - the generic send_action_goal returns "success": true even when Nav2 ABORTED
    the goal, so the model claimed it had arrived;
  - explore_lite kept sending its own goals and preempted the model's;
  - the model confused the /explore/resume *topic* with an action.

Each tool here does the whole job and answers in plain words the model cannot
misread: ARRIVED / ABORTED / CANCELED / TIMEOUT, with the final position.

Every call opens its own short-lived rosbridge connection, so a long
navigate_to() never blocks a concurrent stop_navigation().
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import time
import uuid

import websocket  # websocket-client (already a ros-mcp dependency)

NAV_ACTION = "/navigate_to_pose"
NAV_ACTION_TYPE = "nav2_msgs/action/NavigateToPose"
CANCEL_SERVICES = ("/navigate_to_pose/_action/cancel_goal",
                   "/navigate_through_poses/_action/cancel_goal")
EXPLORE_TOPIC = "/explore/resume"

# action_msgs/msg/GoalStatus
STATUS_TEXT = {0: "UNKNOWN", 1: "ACCEPTED", 2: "EXECUTING", 3: "CANCELING",
               4: "SUCCEEDED", 5: "CANCELED", 6: "ABORTED"}

MAX_GOAL_DISTANCE_M = float(os.getenv("ROVER_MCP_MAX_GOAL_DISTANCE", "30"))
DEFAULT_NAV_TIMEOUT_S = float(os.getenv("ROVER_MCP_NAV_TIMEOUT", "300"))


def _url() -> str:
    return f"ws://{os.getenv('ROSBRIDGE_IP', '127.0.0.1')}:{os.getenv('ROSBRIDGE_PORT', '9090')}"


class _Bridge:
    """Minimal synchronous rosbridge client (one connection per operation)."""

    def __init__(self, timeout: float = 5.0):
        self.ws = websocket.create_connection(_url(), timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001
            pass

    def send(self, msg: dict) -> None:
        self.ws.send(json.dumps(msg))

    def recv(self, timeout: float) -> dict | None:
        self.ws.settimeout(max(timeout, 0.05))
        try:
            raw = self.ws.recv()
        except websocket.WebSocketTimeoutException:
            return None
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def wait_for(self, pred, timeout: float) -> dict | None:
        end = time.monotonic() + timeout
        while (left := end - time.monotonic()) > 0:
            m = self.recv(left)
            if m is not None and pred(m):
                return m
        return None

    def call_service(self, name: str, type_: str, args: dict, timeout: float = 5.0) -> dict | None:
        cid = f"svc_{uuid.uuid4().hex[:8]}"
        self.send({"op": "call_service", "id": cid, "service": name, "type": type_, "args": args})
        return self.wait_for(lambda m: m.get("op") == "service_response" and m.get("id") == cid,
                             timeout)

    def read_once(self, topic: str, type_: str, timeout: float = 3.0) -> dict | None:
        sid = f"sub_{uuid.uuid4().hex[:8]}"
        self.send({"op": "subscribe", "id": sid, "topic": topic, "type": type_, "queue_length": 1})
        m = self.wait_for(lambda m: m.get("op") == "publish" and m.get("topic") == topic, timeout)
        self.send({"op": "unsubscribe", "id": sid, "topic": topic})
        return m.get("msg") if m else None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _yaw_from_quat(q: dict) -> float:
    x, y, z, w = (q.get(k, 0.0) for k in ("x", "y", "z", "w"))
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def _tf_pose(b: _Bridge, timeout: float = 3.0) -> dict | None:
    """map->base_link composed from /tf (map->odom by SLAM/AMCL, odom->base_link by EKF).

    /pose from slam_toolbox only updates while the rover moves, so it can stay
    silent for minutes; /tf is republished continuously."""
    sid = f"tf_{uuid.uuid4().hex[:8]}"
    b.send({"op": "subscribe", "id": sid, "topic": "/tf", "type": "tf2_msgs/msg/TFMessage"})
    found: dict[tuple[str, str], dict] = {}
    want = {("map", "odom"), ("odom", "base_link")}
    end = time.monotonic() + timeout
    try:
        while not want <= found.keys() and (left := end - time.monotonic()) > 0:
            m = b.recv(left)
            if not m or m.get("op") != "publish" or m.get("topic") != "/tf":
                continue
            for tr in m["msg"].get("transforms", []):
                key = (tr["header"]["frame_id"].lstrip("/"), tr["child_frame_id"].lstrip("/"))
                if key in want:
                    found[key] = tr["transform"]
    finally:
        b.send({"op": "unsubscribe", "id": sid, "topic": "/tf"})
    if not want <= found.keys():
        return None
    mo, ob = found[("map", "odom")], found[("odom", "base_link")]
    y1, y2 = _yaw_from_quat(mo["rotation"]), _yaw_from_quat(ob["rotation"])
    ox, oy = ob["translation"]["x"], ob["translation"]["y"]
    x = mo["translation"]["x"] + math.cos(y1) * ox - math.sin(y1) * oy
    y = mo["translation"]["y"] + math.sin(y1) * ox + math.cos(y1) * oy
    yaw = math.atan2(math.sin(y1 + y2), math.cos(y1 + y2))
    return {"x": round(x, 2), "y": round(y, 2), "yaw_deg": round(math.degrees(yaw), 1),
            "frame": "map", "source": "/tf"}


def _pose_sync(b: _Bridge) -> dict | None:
    p = _tf_pose(b)
    if p:
        return p
    msg = b.read_once("/odom", "nav_msgs/msg/Odometry", timeout=4.0)
    if msg:
        p = msg["pose"]["pose"]
        return {"x": round(p["position"]["x"], 2), "y": round(p["position"]["y"], 2),
                "yaw_deg": round(math.degrees(_yaw_from_quat(p["orientation"])), 1),
                "frame": "odom", "source": "/odom"}
    return None


def _fmt_pose(p: dict | None) -> str:
    if not p:
        return "unknown (no pose topic answered)"
    return f"x={p['x']:.2f} m, y={p['y']:.2f} m, heading={p['yaw_deg']:.0f} deg ({p['frame']} frame)"


def _set_exploration_sync(b: _Bridge, enabled: bool) -> None:
    b.send({"op": "advertise", "topic": EXPLORE_TOPIC, "type": "std_msgs/msg/Bool"})
    time.sleep(1.0)  # let DDS match the new publisher with explore_lite before publishing
    for _ in range(3):
        b.send({"op": "publish", "topic": EXPLORE_TOPIC, "msg": {"data": bool(enabled)}})
        time.sleep(0.2)
    b.send({"op": "unadvertise", "topic": EXPLORE_TOPIC})


def _cancel_all_sync(b: _Bridge) -> list[str]:
    # A zero goal UUID with a zero stamp cancels every goal on that action server
    # (action_msgs/srv/CancelGoal semantics), including explore_lite's own goals.
    req = {"goal_info": {"goal_id": {"uuid": [0] * 16}, "stamp": {"sec": 0, "nanosec": 0}}}
    out = []
    for srv in CANCEL_SERVICES:
        r = b.call_service(srv, "action_msgs/srv/CancelGoal", req)
        if r is None:
            out.append(f"{srv}: no answer")
        elif not r.get("result", False):
            out.append(f"{srv}: call failed")
        else:
            n = len((r.get("values") or {}).get("goals_canceling", []) or [])
            out.append(f"{srv}: {n} goal(s) canceling")
    return out


# --------------------------------------------------------------------------- #
# Tool bodies (sync; the async wrappers below run them in a thread)
# --------------------------------------------------------------------------- #

def get_robot_pose_sync() -> str:
    with _Bridge() as b:
        p = _pose_sync(b)
    return f"Rover position: {_fmt_pose(p)}."


def set_exploration_sync(enabled: bool) -> str:
    with _Bridge() as b:
        _set_exploration_sync(b, enabled)
    return ("Autonomous exploration RESUMED: explore_lite will now pick its own goals."
            if enabled else
            "Autonomous exploration PAUSED: the rover only moves when you call navigate_to.")


def stop_navigation_sync() -> str:
    with _Bridge() as b:
        _set_exploration_sync(b, False)
        details = _cancel_all_sync(b)
        time.sleep(1.0)
        p = _pose_sync(b)
    return ("STOPPED: exploration paused and all Nav2 goals canceled "
            f"({'; '.join(details)}). Rover is at {_fmt_pose(p)}.")


def navigate_to_sync(x: float, y: float, yaw_deg: float, timeout_s: float) -> str:
    with _Bridge() as b:
        start = _pose_sync(b)
        if start and start["frame"] == "map":
            dist = math.hypot(x - start["x"], y - start["y"])
            if dist > MAX_GOAL_DISTANCE_M:
                return (f"REFUSED: target is {dist:.1f} m away; the limit per goal is "
                        f"{MAX_GOAL_DISTANCE_M:.0f} m. Pick a closer intermediate point.")
        # explore_lite would preempt this goal with its own, so pause it first.
        _set_exploration_sync(b, False)

        yaw = math.radians(yaw_deg)
        gid = f"nav_{uuid.uuid4().hex[:8]}"
        b.send({
            "op": "send_action_goal", "id": gid, "action": NAV_ACTION,
            "action_type": NAV_ACTION_TYPE, "feedback": False,
            "args": {"pose": {"header": {"frame_id": "map"},
                              "pose": {"position": {"x": float(x), "y": float(y), "z": 0.0},
                                       "orientation": {"x": 0.0, "y": 0.0,
                                                       "z": math.sin(yaw / 2),
                                                       "w": math.cos(yaw / 2)}}}},
        })

        res = b.wait_for(
            lambda m: (m.get("op") == "action_result" and m.get("id") == gid)
            or (m.get("op") == "status" and m.get("level") == "error"),
            timeout_s)

        if res is None:
            b.send({"op": "cancel_action_goal", "id": gid, "action": NAV_ACTION})
            time.sleep(1.0)
            end = _pose_sync(b)
            return (f"TIMEOUT: the rover did not reach ({x:.2f}, {y:.2f}) within {timeout_s:.0f} s; "
                    f"the goal was canceled. Rover is now at {_fmt_pose(end)}. "
                    "Exploration stays paused.")
        if res.get("op") == "status":
            return f"ERROR: rosbridge refused the goal: {res.get('msg')}"

        status = res.get("status")
        text = STATUS_TEXT.get(status, str(status)) if isinstance(status, int) else str(status)
        end = _pose_sync(b)

    miss = (math.hypot(x - end["x"], y - end["y"])
            if end and end["frame"] == "map" else None)
    miss_txt = f" ({miss:.2f} m from the target)" if miss is not None else ""
    if text == "SUCCEEDED":
        head = f"ARRIVED at ({x:.2f}, {y:.2f})"
    elif text == "ABORTED":
        head = (f"ABORTED: Nav2 could not reach ({x:.2f}, {y:.2f}) - the path may be blocked "
                "or the point is outside the known map. The rover did NOT arrive")
    elif text == "CANCELED":
        head = f"CANCELED: the goal to ({x:.2f}, {y:.2f}) was canceled before arrival"
    else:
        head = f"FINISHED with status {text}; the rover may NOT be at ({x:.2f}, {y:.2f})"
    return f"{head}. Rover is now at {_fmt_pose(end)}{miss_txt}. Exploration stays paused."


# --------------------------------------------------------------------------- #
# MCP registration
# --------------------------------------------------------------------------- #

DEDICATED_TOOLS = ("navigate_to", "stop_navigation", "set_exploration", "get_robot_pose")


def register(mcp) -> None:
    @mcp.tool
    async def navigate_to(x: float, y: float, yaw_deg: float = 0.0,
                          timeout_s: float = DEFAULT_NAV_TIMEOUT_S) -> str:
        """Drive the rover to a point in the map frame using Nav2 and WAIT until it
        finishes. Pauses autonomous exploration first. Returns ARRIVED, ABORTED,
        CANCELED or TIMEOUT plus the final position - only ARRIVED means it got there.

        Args:
            x: target x in metres, map frame (the start point is near 0,0).
            y: target y in metres, map frame.
            yaw_deg: final heading in degrees (0 = +x, 90 = +y).
            timeout_s: give up and cancel after this many seconds (the simulation runs
                slower than real time, so allow a few minutes for a few metres).
        """
        return await asyncio.to_thread(navigate_to_sync, x, y, yaw_deg,
                                       min(max(timeout_s, 10.0), 900.0))

    @mcp.tool
    async def stop_navigation() -> str:
        """Stop the rover now: pause autonomous exploration and cancel every Nav2 goal.
        Use whenever the user says stop / halt / pare."""
        return await asyncio.to_thread(stop_navigation_sync)

    @mcp.tool
    async def set_exploration(enabled: bool) -> str:
        """Turn autonomous frontier exploration (explore_lite) on (true) or off (false).
        While it is on, the rover chooses its own destinations to map the area."""
        return await asyncio.to_thread(set_exploration_sync, enabled)

    @mcp.tool
    async def get_robot_pose() -> str:
        """Return the rover's current position (x, y in metres) and heading in the map frame."""
        return await asyncio.to_thread(get_robot_pose_sync)
