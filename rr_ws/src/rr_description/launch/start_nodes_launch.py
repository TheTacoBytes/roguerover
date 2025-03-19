from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
import os
import subprocess

def generate_launch_description():
    urdf_file = os.path.join(
        os.getenv('HOME'), 'rr_ws/rr_ws/src/rr_description/urdf/RogueRover.urdf')

    # # Use v4l2-ctl to set exposure and focus with correct parameters
    # subprocess.run(['v4l2-ctl', '-d', '/dev/video0', '--set-ctrl', 'auto_exposure=3'])
    # subprocess.run(['v4l2-ctl', '-d', '/dev/video0', '--set-ctrl', 'focus_automatic_continuous=1'])

    return LaunchDescription([
        # Velocity publisher
        Node(
            package='rr_velocity',
            executable='vel_raw_pub',
            name='vel_raw_pub',
            output='screen'
        ),
        # Odometry publisher
        Node(
            package='rr_velocity',
            executable='odom_pub',
            name='odom_pub',
            output='screen'
        ),
        # Node(
        #     package='usb_cam',
        #     executable='usb_cam_node_exe',
        #     name='usb_cam',
        #     output='screen',
        #     parameters=[
        #         {'video_device': '/dev/video0'},
        #         {'image_width': 640},
        #         {'image_height': 480},
        #         {'pixel_format': 'yuyv'},
        #         {'camera_frame_id': 'camera'},
        #         {'framerate': 15.0},
        #         {'brightness': 128},
        #         {'contrast': 128},
        #         {'sharpness': 255},
        #         {'saturation': 128},
        #         {'white_balance_automatic': 1},
        #         {'gain': 50},    
        #     ]
        # ),
        # LIDAR node
        IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('sllidar_ros2'), '/launch/sllidar_c1_launch.py'
        ])
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': open(urdf_file).read()}]
        ),
        # OLED display node
        # Node(
        #     package='rr_display',
        #     executable='display',
        #     name='rr_display',
        #     output='screen'
        # ),
    ])
