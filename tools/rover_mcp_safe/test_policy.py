#!/usr/bin/env python3
"""Offline policy test for rover_mcp_safe (no ROS / rosbridge needed).

  ~/.local/share/pipx/venvs/ros-mcp/bin/python -I tools/rover_mcp_safe/test_policy.py
"""
import asyncio
import os
import sys

os.environ.setdefault("ROSBRIDGE_IP", "127.0.0.1")
os.environ.setdefault("ROSBRIDGE_PORT", "9")  # nothing listens: allowed calls fail at transport, not policy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import Client  # noqa: E402

import rover_mcp_safe as safe  # noqa: E402

REFUSED = "REFUSED"


async def call(c, name, args):
    try:
        await c.call_tool(name, args)
        return "OK"
    except Exception as e:  # ToolError surfaces as ToolError / McpError
        msg = str(e)
        return REFUSED if ("Refused" in msg or "disabled" in msg or "Unknown tool" in msg
                           or "not found" in msg.lower()) else f"PASSED-POLICY ({msg[:60]})"


async def main():
    fails = 0
    # Profile exposure: generic writes only in "full"; "minimal" = the 4 dedicated tools.
    for prof, must_have, must_not in (
        ("minimal", safe.DEDICATED_TOOLS, safe.READ_ONLY_TOOLS | safe.GENERIC_WRITE_TOOLS),
        ("nav", safe.DEDICATED_TOOLS | safe.READ_ONLY_TOOLS, safe.GENERIC_WRITE_TOOLS),
        ("full", safe.PROFILES["full"], set()),
    ):
        async with Client(safe.build_server(prof)) as c:
            names = {t.name for t in await c.list_tools()}
        ok = must_have <= names and not (must_not & names)
        fails += not ok
        print(f"[{'ok' if ok else 'FAIL'}] profile {prof:8s} exposes {len(names)} tools")
    async with Client(safe.build_server("nav")) as c:
        r = await call(c, "publish_once", {"topic": "/explore/resume", "msg_type": "std_msgs/msg/Bool",
                                           "msg": {"data": False}})
        ok = r == REFUSED
        fails += not ok
        print(f"[{'ok' if ok else 'FAIL'}] profile nav    refuses publish_once -> {r}")

    mcp = safe.build_server("full")
    async with Client(mcp) as c:
        names = {t.name for t in await c.list_tools()}
        for bad in ("publish_for_durations", "set_parameter", "delete_parameter", "connect_to_robot"):
            ok = bad not in names
            fails += not ok
            print(f"[{'ok' if ok else 'FAIL'}] {bad} hidden from list_tools")
        print(f"     exposed tools: {len(names)}")

        cases = [
            ("publish_once", {"topic": "/cmd_vel", "msg_type": "geometry_msgs/msg/Twist",
                              "msg": {"linear": {"x": 1.0}}}, True),
            ("publish_once", {"topic": "cmd_vel_stamped", "msg_type": "std_msgs/msg/Bool",
                              "msg": {"data": True}}, True),
            ("publish_once", {"topic": "/explore/resume", "msg_type": "geometry_msgs/msg/TwistStamped",
                              "msg": {}}, True),
            ("publish_once", {"topic": "/some/other", "msg_type": "std_msgs/msg/String",
                              "msg": {"data": "x"}}, True),
            ("publish_for_durations", {"topic": "/cmd_vel", "msg_type": "geometry_msgs/msg/Twist",
                                       "messages": [{}], "durations": [1.0]}, True),
            ("set_parameter", {"name": "/controller_server:FollowPath.desired_linear_vel",
                               "value": "5.0"}, True),
            ("send_action_goal", {"action_name": "/spin", "action_type": "nav2_msgs/action/Spin",
                                  "goal": {}}, True),
            ("send_action_goal", {"action_name": "/drive_on_heading",
                                  "action_type": "nav2_msgs/action/DriveOnHeading", "goal": {}}, True),
            ("call_service", {"service_name": "/navigate_to_pose/_action/send_goal",
                              "service_type": "x", "request": {}}, True),
            ("call_service", {"service_name": "/controller_server/set_parameters",
                              "service_type": "rcl_interfaces/srv/SetParameters", "request": {}}, True),
            ("call_service", {"service_name": "/lifecycle_manager_navigation/manage_nodes",
                              "service_type": "nav2_msgs/srv/ManageLifecycleNodes", "request": {}}, True),
            ("subscribe_once", {"topic": "/camera/points", "msg_type": "sensor_msgs/msg/PointCloud2"}, True),
            # allowed by policy (will fail later at transport since no rosbridge)
            ("publish_once", {"topic": "/explore/resume", "msg_type": "std_msgs/msg/Bool",
                              "msg": {"data": False}}, False),
            ("send_action_goal", {"action_name": "/navigate_to_pose",
                                  "action_type": "nav2_msgs/action/NavigateToPose", "goal": {},
                                  "timeout": 1.0}, False),
            ("subscribe_once", {"topic": "/odom", "msg_type": "nav_msgs/msg/Odometry", "timeout": 1.0},
             False),
        ]
        for name, args, expect_refused in cases:
            r = await call(c, name, args)
            ok = (r == REFUSED) == expect_refused
            fails += not ok
            tgt = args.get("topic") or args.get("action_name") or args.get("service_name") or args.get("name")
            print(f"[{'ok' if ok else 'FAIL'}] {name:22s} {tgt:45s} -> {r}")
    print("ALL PASS" if not fails else f"{fails} FAILURE(S)")
    sys.exit(1 if fails else 0)


asyncio.run(main())
