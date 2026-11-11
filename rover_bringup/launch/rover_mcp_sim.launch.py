# MIT License
#
# Single entry point for "rover + natural-language control via MCP" in
# simulation, modelled on ros-mcp-server's examples/10_tugbot launch:
#
#   ros2 launch rover_bringup rover_mcp_sim.launch.py slam:=true explore:=true
#
# It does NOT duplicate any Nav2 / SLAM configuration. The simulation stack
# is reused as-is from rover_gazebo/launch/gazebo.launch.py, which already
# brings up, in this order of dependency:
#   1. Gazebo Harmonic (ros_gz_sim) + ros_gz_bridge + rover spawn/controllers
#   2. rover_localization: rgbd_odometry + EKF (rtabmap mapping is skipped so
#      it does not fight slam_toolbox for map->odom)
#   3. rover_slam: slam_toolbox (slam:=true) or map_server+AMCL (slam:=false)
#   4. rover_navigation: Nav2
#   5. rover_slam: explore_lite (explore:=true, only while slam:=true)
# and this file adds:
#   6. rosbridge_server (+ rosapi) on ws://<host>:9090 (rosbridge:=true)
#
# rover_gazebo is resolved at runtime only (no package.xml dependency) so that
# rover_bringup does not drag Gazebo onto the Raspberry Pi.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    pkg_bringup = get_package_share_directory("rover_bringup")
    pkg_gazebo = get_package_share_directory("rover_gazebo")

    ### ARGS ###
    slam = LaunchConfiguration("slam")
    explore = LaunchConfiguration("explore")
    rosbridge = LaunchConfiguration("rosbridge")
    rosbridge_port = LaunchConfiguration("rosbridge_port")
    use_sim_time = LaunchConfiguration("use_sim_time")
    world = LaunchConfiguration("world")
    initial_pose_z = LaunchConfiguration("initial_pose_z")
    headless = LaunchConfiguration("headless")
    launch_rviz = LaunchConfiguration("launch_rviz")
    map_yaml = LaunchConfiguration("map")
    nav2_planner = LaunchConfiguration("nav2_planner")
    nav2_controller = LaunchConfiguration("nav2_controller")

    args = [
        DeclareLaunchArgument(
            "slam",
            default_value="True",
            description="slam_toolbox (True) or AMCL on an existing map (False)",
        ),
        DeclareLaunchArgument(
            "explore",
            default_value="False",
            description="Run explore_lite frontier exploration (needs slam:=True)",
        ),
        DeclareLaunchArgument(
            "rosbridge",
            default_value="True",
            description="Start rosbridge_server for ros-mcp-server",
        ),
        DeclareLaunchArgument(
            "rosbridge_port", default_value="9090", description="rosbridge port"
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="True",
            description="Applied to rosbridge/rosapi. The Gazebo stack in "
            "rover_gazebo always uses sim time.",
        ),
        DeclareLaunchArgument(
            "world",
            default_value=os.path.join(pkg_gazebo, "worlds", "moon.world"),
            description="Gazebo world",
        ),
        DeclareLaunchArgument(
            "initial_pose_z",
            default_value="2.11",
            description="Spawn height (2.11 for moon.world, 0.22 for empty.world)",
        ),
        DeclareLaunchArgument(
            "headless", default_value="False", description="Gazebo server only"
        ),
        DeclareLaunchArgument(
            "launch_rviz", default_value="True", description="Launch rviz2"
        ),
        DeclareLaunchArgument(
            "map",
            default_value="",
            description="Map yaml for AMCL, required when slam:=False",
        ),
        DeclareLaunchArgument(
            "nav2_planner",
            default_value="SmacHybrid",
            choices=["SmacHybrid", "SmacLattice"],
            description="Nav2 planner",
        ),
        DeclareLaunchArgument(
            "nav2_controller",
            default_value="RPP",
            choices=["RPP", "TEB"],
            description="Nav2 controller",
        ),
    ]

    ### LAUNCHES ###
    sim_stack_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "world": world,
            "initial_pose_z": initial_pose_z,
            "headless": headless,
            "launch_rviz": launch_rviz,
            "slam": slam,
            "explore": explore,
            "map": map_yaml,
            "nav2_planner": nav2_planner,
            "nav2_controller": nav2_controller,
        }.items(),
    )

    # rosbridge last: give Gazebo/Nav2 a head start so the first MCP
    # get_topics/get_actions already sees the full graph.
    rosbridge_cmd = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_bringup, "launch", "rosbridge.launch.py")
                ),
                launch_arguments={
                    "port": rosbridge_port,
                    "use_sim_time": use_sim_time,
                }.items(),
                condition=IfCondition(rosbridge),
            )
        ],
    )

    ld = LaunchDescription()
    for a in args:
        ld.add_action(a)
    ld.add_action(sim_stack_cmd)
    ld.add_action(rosbridge_cmd)
    return ld
