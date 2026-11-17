#!/usr/bin/env python3
"""Overall bring-up for the Site Safety Patrol hackathon stack.

This launch file starts the three sensor drivers:

1. rslidar_sdk           -> 3D LiDAR (``ros2 launch rslidar_sdk start.py``)
2. xsens_mti_ros2_driver -> IMU (``ros2 launch xsens_mti_ros2_driver xsens_mti_node.launch.py``)
3. realsense2_camera     -> RGB camera, namespace ``camera_depth``, name ``head``
                            (topics on ``/camera_depth/head/...``)

The navigation stack is **not** started here; run these in their own
terminals so their output and lifecycle stay independent::

    # Terminal 2 - MonoNavi (type 4 at the prompt for the external backend)
    python3 ~/RoboTUNN/src/MonoNavi/launch/mononavi_launch.py \
        --middle_line_ratio 0.8 \
        --image_topic /camera_depth/head/color/image_raw \
        --enable_viz --reached_continue --use_imu \
        --lidar_denied_range 0.8 --rotate_search true

    # Terminal 3 - external detections on /mononavi/detections
    python3 ~/RoboTUNN/src/MonoNavi/launch/external_detection_publisher.py

Prerequisites
-------------
The packages live in the RoboTUNN workspace, so source it before launching::

    source /opt/ros/humble/setup.bash
    source ~/RoboTUNN/install/setup.bash

Usage
-----
::

    ros2 launch <path-to-this-repo>/launch/overall_launch_hackathon.launch.py

    # Adjust individual pieces
    ros2 launch ... start_lidar:=false
    ros2 launch ... camera_name:=head

    # List every available argument
    ros2 launch ... --show-args
"""

import os

from ament_index_python.packages import (
    PackageNotFoundError,
    get_package_share_directory,
)
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _share_dir(package: str) -> str:
    """Return a package share directory, with a helpful error if unsourced."""
    try:
        return get_package_share_directory(package)
    except PackageNotFoundError as exc:
        raise RuntimeError(
            f"Cannot find ROS package '{package}'. "
            "Source the RoboTUNN workspace first:\n"
            "    source /opt/ros/humble/setup.bash\n"
            "    source ~/RoboTUNN/install/setup.bash"
        ) from exc


def _launch_file(package: str, filename: str) -> PythonLaunchDescriptionSource:
    """Build a PythonLaunchDescriptionSource for a launch file in a package."""
    return PythonLaunchDescriptionSource(
        os.path.join(_share_dir(package), 'launch', filename)
    )


def generate_launch_description() -> LaunchDescription:
    declared_arguments = [
        # Component switches.
        DeclareLaunchArgument(
            'start_lidar', default_value='true',
            description='Start the rslidar_sdk LiDAR driver.'),
        DeclareLaunchArgument(
            'start_imu', default_value='true',
            description='Start the xsens_mti_ros2_driver IMU node.'),
        DeclareLaunchArgument(
            'start_camera', default_value='true',
            description='Start the realsense2_camera driver.'),

        # Camera parameters.
        DeclareLaunchArgument(
            'camera_namespace', default_value='camera_depth',
            description='realsense2_camera namespace.'),
        DeclareLaunchArgument(
            'camera_name', default_value='head',
            description='realsense2_camera node name '
                        '(topics become /<camera_namespace>/<camera_name>/...).'),
    ]

    lidar = IncludeLaunchDescription(
        _launch_file('rslidar_sdk', 'start.py'),
        condition=IfCondition(LaunchConfiguration('start_lidar')),
    )

    imu = IncludeLaunchDescription(
        _launch_file('xsens_mti_ros2_driver', 'xsens_mti_node.launch.py'),
        condition=IfCondition(LaunchConfiguration('start_imu')),
    )

    camera = IncludeLaunchDescription(
        _launch_file('realsense2_camera', 'rs_launch.py'),
        launch_arguments={
            'camera_namespace': LaunchConfiguration('camera_namespace'),
            'camera_name': LaunchConfiguration('camera_name'),
        }.items(),
        condition=IfCondition(LaunchConfiguration('start_camera')),
    )

    return LaunchDescription(
        declared_arguments + [lidar, imu, camera]
    )
