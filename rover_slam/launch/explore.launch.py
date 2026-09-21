import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("rover_slam")
    params_file = os.path.join(pkg_dir, "config", "explore_params.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time")
    use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true",
    )

    # remap fully qualified tf names to relative so a namespace could be prepended
    remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]

    explore_cmd = Node(
        package="explore_lite",
        executable="explore",
        name="explore_node",
        output="screen",
        parameters=[params_file, {"use_sim_time": use_sim_time}],
        remappings=remappings,
    )

    ld = LaunchDescription()
    ld.add_action(use_sim_time_cmd)
    ld.add_action(explore_cmd)
    return ld
