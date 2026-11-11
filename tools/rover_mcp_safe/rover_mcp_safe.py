#!/usr/bin/env python3
"""rover-mcp-safe: a restricted MCP front-end for ros-mcp-server.

Architecture rule (hugoplate/content/english/pages/ros-mcp.md): the LLM sends *goals* and reads *state*.
It never drives the motors directly. ros-mcp-server ships ~31 tools, among them
publish_once / publish_for_durations, which would let a model write straight
into /cmd_vel. This server registers the upstream ros-mcp tools in-process and
then:

  1. removes every tool that is not in TOOL_ALLOWLIST (they are not even listed
     to the client, so a model cannot hallucinate its way into them);
  2. guards the arguments of the remaining "write" tools via middleware:
       - publish_once      -> only topics in PUBLISH_TOPIC_ALLOWLIST, never any
                              Twist/TwistStamped/velocity-like type or topic
       - send_action_goal  -> only actions in ACTION_ALLOWLIST (Nav2 goals),
                              not /spin, /backup, /drive_on_heading, ...
       - call_service      -> denies parameter setting, lifecycle control and
                              the hidden /_action/* services (bypass of the
                              action allowlist)
       - subscribe_*       -> denies bulky types (point clouds, raw images),
                              clamps duration / message count

Run it with the interpreter of the pipx venv that has ros-mcp installed:

  ~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_mcp_safe/rover_mcp_safe.py

Environment:
  ROSBRIDGE_IP / ROSBRIDGE_PORT  rosbridge to connect to (127.0.0.1:9090)
  ROVER_MCP_PUBLISH_TOPICS       comma list, overrides PUBLISH_TOPIC_ALLOWLIST
  ROVER_MCP_ACTIONS              comma list, overrides ACTION_ALLOWLIST
"""

from __future__ import annotations

import argparse
import os
import re
import sys

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

from ros_mcp.integration import register as register_ros_mcp


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [_norm(x) for x in raw.split(",") if x.strip()]


def _norm(name: str) -> str:
    name = (name or "").strip()
    return name if name.startswith("/") else "/" + name


# --------------------------------------------------------------------------- #
# Policy
# --------------------------------------------------------------------------- #

TOOL_ALLOWLIST = {
    # discovery / read-only
    "get_topics",
    "get_topic_type",
    "get_topic_details",
    "get_message_details",
    "subscribe_once",
    "subscribe_for_duration",
    "get_actions",
    "get_action_details",
    "get_action_status",
    "get_services",
    "get_service_type",
    "get_service_details",
    "get_nodes",
    "get_node_details",
    "get_parameter",
    "get_parameters",
    "has_parameter",
    "get_parameter_details",
    "detect_ros_version",
    "ping_robots",
    # guarded writes
    "send_action_goal",
    "cancel_action_goal",
    "call_service",
    "publish_once",
}
# Explicitly NOT exposed: publish_for_durations (streams velocity),
# set_parameter / delete_parameter (could retune controller limits),
# connect_to_robot (would let the model re-point the bridge),
# view_saved_image / get_verified_robot_* (irrelevant, reads local files).

PUBLISH_TOPIC_ALLOWLIST = _env_list(
    "ROVER_MCP_PUBLISH_TOPICS",
    [
        "/explore/resume",  # std_msgs/Bool: pause/resume explore_lite
    ],
)

ACTION_ALLOWLIST = _env_list(
    "ROVER_MCP_ACTIONS",
    [
        "/navigate_to_pose",
        "/navigate_through_poses",
    ],
)

# Message types that command motion directly. Rejected for publish_once even if
# someone adds the topic to the allowlist by mistake.
MOTION_TYPE_RE = re.compile(
    r"(Twist|Twist(Stamped|WithCovariance)?|AckermannDrive(Stamped)?|JointTrajectory|"
    r"Float64MultiArray)$",
    re.IGNORECASE,
)
MOTION_TOPIC_RE = re.compile(r"cmd_vel|/velocity_controller/|/position_controller/", re.IGNORECASE)

SERVICE_DENY_RE = re.compile(
    r"(/_action/"  # hidden action services: bypass the action allowlist
    r"|set_parameters|set_parameters_atomically|load_parameter_file"
    r"|/change_state$|/manage_nodes$"  # lifecycle: could shut Nav2 down
    r"|/controller_manager/"  # (un)load / switch ros2_control controllers
    r")",
    re.IGNORECASE,
)

BULKY_TYPE_RE = re.compile(r"(PointCloud2?|/Image$|CompressedImage|OccupancyGrid)$", re.IGNORECASE)
MAX_SUBSCRIBE_DURATION_S = 5.0
MAX_SUBSCRIBE_MESSAGES = 20


# --------------------------------------------------------------------------- #
# Guard middleware
# --------------------------------------------------------------------------- #


class RoverSafetyMiddleware(Middleware):
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        tools = await call_next(context)
        return [t for t in tools if t.name in TOOL_ALLOWLIST]

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        name = context.message.name
        args = dict(context.message.arguments or {})

        if name not in TOOL_ALLOWLIST:
            raise ToolError(f"Tool '{name}' is disabled on this rover (safety policy).")

        if name == "publish_once":
            self._check_publish(args)
        elif name == "send_action_goal":
            self._check_action(args)
        elif name == "call_service":
            self._check_service(args)
        elif name in ("subscribe_once", "subscribe_for_duration"):
            args = self._check_subscribe(name, args)
            context.message.arguments = args

        return await call_next(context)

    # -- individual checks -------------------------------------------------- #
    @staticmethod
    def _check_publish(args: dict) -> None:
        topic = _norm(args.get("topic", ""))
        msg_type = str(args.get("msg_type", ""))
        if MOTION_TOPIC_RE.search(topic) or MOTION_TYPE_RE.search(msg_type):
            raise ToolError(
                f"Refused: publishing {msg_type or '?'} on {topic} would command motion "
                "directly. Send a Nav2 goal with send_action_goal('/navigate_to_pose', "
                "'nav2_msgs/action/NavigateToPose', ...) instead."
            )
        if topic not in PUBLISH_TOPIC_ALLOWLIST:
            raise ToolError(
                f"Refused: publishing on {topic} is not allowed. "
                f"Allowed topics: {', '.join(PUBLISH_TOPIC_ALLOWLIST) or 'none'}."
            )

    @staticmethod
    def _check_action(args: dict) -> None:
        action = _norm(args.get("action_name", ""))
        if action not in ACTION_ALLOWLIST:
            raise ToolError(
                f"Refused: action {action} is not allowed. "
                f"Allowed actions: {', '.join(ACTION_ALLOWLIST)}."
            )

    @staticmethod
    def _check_service(args: dict) -> None:
        service = _norm(args.get("service_name", ""))
        if SERVICE_DENY_RE.search(service):
            raise ToolError(f"Refused: service {service} is blocked by the rover safety policy.")

    @staticmethod
    def _check_subscribe(name: str, args: dict) -> dict:
        msg_type = str(args.get("msg_type", ""))
        if BULKY_TYPE_RE.search(msg_type):
            raise ToolError(
                f"Refused: {msg_type} is too large to stream through rosbridge "
                "(JSON) without starving Nav2. Read /odom, /map metadata or "
                "Nav2 action status instead."
            )
        if name == "subscribe_for_duration":
            try:
                d = float(args.get("duration", MAX_SUBSCRIBE_DURATION_S))
            except (TypeError, ValueError):
                d = MAX_SUBSCRIBE_DURATION_S
            args["duration"] = min(max(d, 0.1), MAX_SUBSCRIBE_DURATION_S)
            try:
                m = int(args.get("max_messages", MAX_SUBSCRIBE_MESSAGES))
            except (TypeError, ValueError):
                m = MAX_SUBSCRIBE_MESSAGES
            args["max_messages"] = min(max(m, 1), MAX_SUBSCRIBE_MESSAGES)
        return args


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #

INSTRUCTIONS = """\
You control a Sawppy-style rover running ROS 2 Jazzy + Nav2.
Rules:
- Never try to drive the motors directly; /cmd_vel is not available to you.
- To move, send a Nav2 goal: send_action_goal(action_name='/navigate_to_pose',
  action_type='nav2_msgs/action/NavigateToPose', goal={'pose': {'header':
  {'frame_id': 'map'}, 'pose': {'position': {'x': X, 'y': Y, 'z': 0.0},
  'orientation': {'w': 1.0}}}}).
- Read state with subscribe_once (e.g. /odom nav_msgs/msg/Odometry).
  Do not subscribe to /scan, cameras or point clouds for more than one message.
- Autonomous exploration is done by explore_lite, not by you. Pause/resume it
  with publish_once(topic='/explore/resume', msg_type='std_msgs/msg/Bool',
  msg={'data': false|true}).
"""


def build_server() -> FastMCP:
    mcp = FastMCP("rover-mcp-safe", instructions=INSTRUCTIONS)
    register_ros_mcp(mcp)  # reads ROSBRIDGE_IP / ROSBRIDGE_PORT from env

    # Defence in depth: physically remove everything not allowlisted, so the
    # policy holds even if the middleware were bypassed.
    registered = list(mcp._tool_manager._tools)  # sync view (fastmcp 2.x)
    for tool_name in registered:
        if tool_name not in TOOL_ALLOWLIST:
            mcp.remove_tool(tool_name)

    mcp.add_middleware(RoverSafetyMiddleware())
    return mcp


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--transport", choices=["stdio", "http", "streamable-http"], default="stdio")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=9000)
    a = p.parse_args()

    mcp = build_server()
    if a.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        print(f"rover-mcp-safe on http://{a.host}:{a.port}", file=sys.stderr)
        mcp.run(transport=a.transport, host=a.host, port=a.port)


if __name__ == "__main__":
    main()
