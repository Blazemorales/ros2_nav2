# MIT License
#
# rosbridge WebSocket server (+ rosapi) for ros-mcp-server.
# Usable both in simulation (included by rover_mcp_sim.launch.py) and on the
# real robot (Raspberry Pi):
#
#   ros2 launch rover_bringup rosbridge.launch.py
#
# Safety, server side (second layer, independent of the MCP proxy in
# tools/rover_mcp_safe): rosbridge itself only lets WebSocket clients
#   - publish on topics matching `topics_pub_glob` (default: /explore/resume
#     only -> no /cmd_vel from any rosbridge client);
#   - send goals to actions matching `actions_glob` (default: Nav2
#     navigate_to_pose / navigate_through_poses).
# Pass topics_pub_glob:='' / actions_glob:='' to lift the restriction.
#
# NOTE: rosbridge serialises every message to JSON. Never keep a continuous
# subscription to /scan, camera or point-cloud topics through it -- on a
# Raspberry Pi 3 that starves Nav2. See docs/ros-mcp.md.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    port = LaunchConfiguration("port")
    address = LaunchConfiguration("address")
    use_sim_time = LaunchConfiguration("use_sim_time")
    topics_pub_glob = LaunchConfiguration("topics_pub_glob")
    actions_glob = LaunchConfiguration("actions_glob")

    args = [
        DeclareLaunchArgument(
            "port", default_value="9090", description="rosbridge WebSocket port"
        ),
        DeclareLaunchArgument(
            "address",
            default_value="",
            description="Address to bind (empty = all interfaces)",
        ),
        DeclareLaunchArgument(
            "use_sim_time", default_value="False", description="Use /clock time"
        ),
        DeclareLaunchArgument(
            "topics_pub_glob",
            default_value="['/explore/resume']",
            description="Topics rosbridge clients may publish on "
            "(rosbridge glob list syntax; '' = no restriction)",
        ),
        DeclareLaunchArgument(
            "actions_glob",
            default_value="['/navigate_to_pose', '/navigate_through_poses']",
            description="Actions rosbridge clients may send goals to "
            "('' = no restriction)",
        ),
    ]

    rosbridge_cmd = Node(
        package="rosbridge_server",
        executable="rosbridge_websocket",
        name="rosbridge_websocket",
        output="screen",
        parameters=[
            {
                "port": ParameterValue(port, value_type=int),
                "address": address,
                "use_sim_time": ParameterValue(use_sim_time, value_type=bool),
                # Long-running Nav2 goals must not block other requests
                # (e.g. subscribe_once on /odom while navigating).
                "call_services_in_new_thread": True,
                "send_action_goals_in_new_thread": True,
                "topics_pub_glob": ParameterValue(topics_pub_glob, value_type=str),
                "actions_glob": ParameterValue(actions_glob, value_type=str),
            }
        ],
    )

    # rosapi backs the discovery tools (get_topics, get_actions, ...).
    # No globs here: they would filter the listings, not the permissions.
    rosapi_cmd = Node(
        package="rosapi",
        executable="rosapi_node",
        name="rosapi",
        parameters=[{"use_sim_time": ParameterValue(use_sim_time, value_type=bool)}],
    )

    ld = LaunchDescription()
    for a in args:
        ld.add_action(a)
    ld.add_action(rosbridge_cmd)
    ld.add_action(rosapi_cmd)
    return ld
