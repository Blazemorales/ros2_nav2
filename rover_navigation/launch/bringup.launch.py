# MIT License

# Copyright (c) 2023 Miguel Ángel González Santamarta

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import yaml
import tempfile
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from nav2_common.launch import RewrittenYaml


def merge_yaml_files(files, patch=None):
    merged_data = {}

    for file_path in files:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                raise ValueError(
                    f"YAML content in {file_path} must be a dictionary at the top level."
                )
            merged_data.update(data)  # keys from later files will overwrite earlier ones

    if patch is not None:
        patch(merged_data)

    # Create a temporary file with .yaml extension
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w")
    yaml.dump(merged_data, temp)
    temp_path = temp.name
    temp.close()

    return temp_path


def use_scan_in_local_costmap(params):
    """Feed the local costmap from /scan instead of /camera/points.

    Used by the simulation's light profile (sim_lite), where the point cloud
    is not bridged. The lidar is 2D (+-1 rad), so a plain ObstacleLayer
    replaces the VoxelLayer; heights are left wide open because the lidar
    sits at base_link height on uneven terrain.
    """
    local = params["local_costmap"]["local_costmap"]["ros__parameters"]
    local["plugins"] = ["obstacle_layer" if p == "voxel_layer" else p for p in local["plugins"]]
    local.pop("voxel_layer", None)
    local["obstacle_layer"] = {
        "plugin": "nav2_costmap_2d::ObstacleLayer",
        "enabled": True,
        "footprint_clearing_enabled": True,
        "observation_sources": "scan",
        "scan": {
            "topic": "/scan",
            "data_type": "LaserScan",
            "max_obstacle_height": 5.0,
            "min_obstacle_height": -5.0,
            "obstacle_max_range": 2.5,
            "obstacle_min_range": 0.0,
            "raytrace_max_range": 3.0,
            "raytrace_min_range": 0.0,
            "clearing": True,
            "marking": True,
        },
    }


def generate_launch_description():
    # Get the launch directory
    pkg_dir = get_package_share_directory("rover_navigation")
    launch_dir = os.path.join(pkg_dir, "launch")

    stdout_linebuf_envvar = SetEnvironmentVariable("RCUTILS_LOGGING_BUFFERED_STREAM", "1")

    def run_nav2(context, planner, controller, obstacle_source):
        planner = str(context.perform_substitution(planner))
        controller = str(context.perform_substitution(controller))
        obstacle_source = str(context.perform_substitution(obstacle_source))

        params_file = merge_yaml_files(
            [
                os.path.join(pkg_dir, "params", "common.yaml"),
                os.path.join(pkg_dir, "params", "costmaps.yaml"),
                os.path.join(pkg_dir, "params", f"{planner}.yaml"),
                os.path.join(pkg_dir, "params", f"{controller}.yaml"),
            ],
            patch=use_scan_in_local_costmap if obstacle_source == "scan" else None,
        )

        param_substitutions = {"use_sim_time": LaunchConfiguration("use_sim_time")}
        configured_params = RewrittenYaml(
            source_file=params_file,
            root_key=LaunchConfiguration("namespace"),
            param_rewrites=param_substitutions,
            convert_types=True,
        )

        # Specify the actions
        return [
            PushRosNamespace(
                condition=IfCondition(LaunchConfiguration("use_namespace")),
                namespace=LaunchConfiguration("namespace"),
            ),
            Node(
                condition=IfCondition(LaunchConfiguration("use_composition")),
                name="nav2_container",
                package="rclcpp_components",
                executable="component_container_isolated",
                parameters=[
                    configured_params,
                    {"autostart": LaunchConfiguration("autostart")},
                ],
                remappings=[
                    ("/tf", "tf"),
                    ("/tf_static", "tf_static"),
                    ("/cmd_vel", LaunchConfiguration("cmd_vel_topic")),
                ],
                output="screen",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(launch_dir, "navigation.launch.py")
                ),
                launch_arguments={
                    "namespace": LaunchConfiguration("namespace"),
                    "cmd_vel_topic": LaunchConfiguration("cmd_vel_topic"),
                    "default_nav_to_pose_bt_xml": LaunchConfiguration(
                        "default_bt_xml_filename"
                    ),
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "autostart": LaunchConfiguration("autostart"),
                    "params_file": params_file,
                    "use_composition": LaunchConfiguration("use_composition"),
                    "use_respawn": LaunchConfiguration("use_respawn"),
                    "container_name": "nav2_container",
                }.items(),
            ),
        ]

    # Create the launch configuration variables
    declare_namespace_cmd = DeclareLaunchArgument(
        "namespace", default_value="", description="Top-level namespace"
    )

    declare_use_namespace_cmd = DeclareLaunchArgument(
        "use_namespace",
        default_value="false",
        description="Whether to apply a namespace to the navigation stack",
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        "autostart",
        default_value="true",
        description="Automatically startup the nav2 stack",
    )

    declare_use_composition_cmd = DeclareLaunchArgument(
        "use_composition",
        default_value="False",
        description="Whether to use composed bringup",
    )

    declare_use_respawn_cmd = DeclareLaunchArgument(
        "use_respawn",
        default_value="False",
        description="Whether to respawn if a node crashes. Applied when composition is disabled.",
    )

    cmd_vel_topic_cmd = DeclareLaunchArgument(
        "cmd_vel_topic",
        default_value="cmd_vel",
        description="cmd_vel topic (for remmaping)",
    )

    declare_bt_xml_cmd = DeclareLaunchArgument(
        "default_bt_xml_filename",
        default_value=os.path.join(pkg_dir, "behavior_trees", "rover_bt.xml"),
        description="Full path to the behavior tree xml file to use",
    )

    planner = LaunchConfiguration("planner")
    planner_cmd = DeclareLaunchArgument(
        "planner",
        default_value="SmacHybrid",
        choices=["SmacHybrid", "SmacLattice"],
        description="Nav2 planner (SmacHybrid or SmacLattice)",
    )

    controller = LaunchConfiguration("controller")
    controller_cmd = DeclareLaunchArgument(
        "controller",
        default_value="RPP",
        choices=["RPP", "TEB"],
        description="Nav2 controller (RPP or TEB)",
    )

    local_obstacle_source = LaunchConfiguration("local_obstacle_source")
    local_obstacle_source_cmd = DeclareLaunchArgument(
        "local_obstacle_source",
        default_value="camera",
        choices=["camera", "scan"],
        description="Local costmap obstacles from /camera/points (camera) or /scan",
    )

    nav2_cmd = OpaqueFunction(
        function=run_nav2, args=[planner, controller, local_obstacle_source]
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Set environment variables
    ld.add_action(stdout_linebuf_envvar)

    # Declare the launch options
    ld.add_action(cmd_vel_topic_cmd)
    ld.add_action(declare_bt_xml_cmd)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_use_composition_cmd)
    ld.add_action(declare_use_respawn_cmd)
    ld.add_action(planner_cmd)
    ld.add_action(controller_cmd)
    ld.add_action(local_obstacle_source_cmd)

    # Add the actions to launch all of the navigation nodes
    ld.add_action(nav2_cmd)

    return ld
