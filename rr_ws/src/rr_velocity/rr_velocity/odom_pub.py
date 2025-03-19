#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

class OdomPublisher(Node):
    def __init__(self):
        super().__init__('base_node')
        # Declare parameters
        self.declare_parameter("wheelbase", 0.25)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_footprint_frame", "base_footprint")
        self.declare_parameter("linear_scale_x", 1.0)
        self.declare_parameter("linear_scale_y", 1.0)
        self.declare_parameter("pub_odom_tf", True)

        # Retrieve parameters
        self.wheelbase = self.get_parameter("wheelbase").get_parameter_value().double_value
        self.odom_frame = self.get_parameter("odom_frame").get_parameter_value().string_value
        self.base_footprint_frame = self.get_parameter("base_footprint_frame").get_parameter_value().string_value
        self.linear_scale_x = self.get_parameter("linear_scale_x").get_parameter_value().double_value
        self.linear_scale_y = self.get_parameter("linear_scale_y").get_parameter_value().double_value
        self.pub_odom_tf = self.get_parameter("pub_odom_tf").get_parameter_value().bool_value

        # Create TF broadcaster if needed
        if self.pub_odom_tf:
            self.tf_broadcaster = TransformBroadcaster(self)

        # Create subscription to velocity messages on "vel_raw"
        self.subscription = self.create_subscription(
            Twist,
            "vel_raw",
            self.handle_vel,
            50
        )
        # Create publisher for odometry messages on "/odom"
        self.odom_publisher = self.create_publisher(Odometry, "/odom", 50)

        # Initialize state variables
        self.x_pos = 0.0
        self.y_pos = 0.0
        self.heading = 0.0
        self.last_vel_time = self.get_clock().now()

    def handle_vel(self, msg):
        current_time = self.get_clock().now()
        # Compute time delta in seconds
        dt = (current_time - self.last_vel_time).nanoseconds / 1e9
        self.last_vel_time = current_time

        # Scale the linear velocities from the message
        linear_velocity_x = msg.linear.x * self.linear_scale_x
        linear_velocity_y = msg.linear.y * self.linear_scale_y
        angular_velocity_z = msg.angular.z

        # Calculate changes based on current heading
        delta_heading = angular_velocity_z * dt
        delta_x = (linear_velocity_x * math.cos(self.heading) - linear_velocity_y * math.sin(self.heading)) * dt
        delta_y = (linear_velocity_x * math.sin(self.heading) + linear_velocity_y * math.cos(self.heading)) * dt

        # Update the robot's position and heading
        self.x_pos += delta_x
        self.y_pos += delta_y
        self.heading += delta_heading

        # Create a quaternion from the heading (yaw only)
        qz = math.sin(self.heading / 2.0)
        qw = math.cos(self.heading / 2.0)
        odom_quat = Quaternion(x=0.0, y=0.0, z=qz, w=qw)

        # Construct the Odometry message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_footprint_frame

        # Set the pose of the robot
        odom.pose.pose.position.x = self.x_pos
        odom.pose.pose.position.y = self.y_pos
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = odom_quat
        # Set pose covariance (example values)
        odom.pose.covariance[0] = 0.001
        odom.pose.covariance[7] = 0.001
        odom.pose.covariance[35] = 0.001

        # Set the twist (velocity) of the robot
        odom.twist.twist.linear.x = linear_velocity_x

        odom.twist.twist.linear.y = 0.0
        odom.twist.twist.linear.z = 0.0
        odom.twist.twist.angular.x = 0.0
        odom.twist.twist.angular.y = 0.0
        odom.twist.twist.angular.z = angular_velocity_z
        # Set twist covariance (example values)
        odom.twist.covariance[0] = 0.0001
        odom.twist.covariance[7] = 0.0001
        odom.twist.covariance[35] = 0.0001

        # Publish the Odometry message
        self.odom_publisher.publish(odom)

        # If parameter is enabled, broadcast the transform
        if self.pub_odom_tf:
            t = TransformStamped()
            t.header.stamp = current_time.to_msg()
            t.header.frame_id = self.odom_frame
            t.child_frame_id = self.base_footprint_frame
            t.transform.translation.x = self.x_pos
            t.transform.translation.y = self.y_pos
            t.transform.translation.z = 0.0
            t.transform.rotation = odom_quat
            self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = OdomPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()


# import rclpy
# from rclpy.node import Node
# from nav_msgs.msg import Odometry
# from geometry_msgs.msg import Twist, Quaternion
# from tf_transformations import quaternion_from_euler
# from rclpy.time import Time
# import math

# class OdomPublisher(Node):
#     def __init__(self):
#         super().__init__('odom_publisher')
        
#         # Initialize parameters
#         self.linear_scale_x = self.declare_parameter("linear_scale_x", 1.0).value
#         self.linear_scale_y = self.declare_parameter("linear_scale_y", 1.0).value
#         self.odom_frame = self.declare_parameter("odom_frame", "odom").value
#         self.base_footprint_frame = self.declare_parameter("base_footprint_frame", "base_footprint").value
        
#         # Initialize variables
#         self.linear_velocity_x = 0.0
#         self.linear_velocity_y = 0.0
#         self.angular_velocity_z = 0.0
#         self.last_vel_time = self.get_clock().now()
#         self.vel_dt = 0.0
#         self.x_pos = 0.0
#         self.y_pos = 0.0
#         self.heading = 0.0

#         # Create subscriber and publisher
#         self.velocity_subscriber = self.create_subscription(
#             Twist, '/vel_raw', self.vel_callback, 50)
#         self.odom_publisher = self.create_publisher(
#             Odometry, '/odom_raw', 50)

#     def vel_callback(self, twist):
#         current_time = self.get_clock().now()
#         self.vel_dt = (current_time - self.last_vel_time).nanoseconds / 1e9  # Convert to seconds
#         self.last_vel_time = current_time

#         # Apply scaling to velocities
#         self.linear_velocity_x = twist.linear.x * self.linear_scale_x
#         self.linear_velocity_y = twist.linear.y * self.linear_scale_y
#         self.angular_velocity_z = twist.angular.z

#         # Compute odometry
#         delta_heading = self.angular_velocity_z * self.vel_dt
#         delta_x = (self.linear_velocity_x * math.cos(self.heading) - self.linear_velocity_y * math.sin(self.heading)) * self.vel_dt
#         delta_y = (self.linear_velocity_x * math.sin(self.heading) + self.linear_velocity_y * math.cos(self.heading)) * self.vel_dt

#         # Update position
#         self.x_pos += delta_x
#         self.y_pos += delta_y
#         self.heading += delta_heading

#         # Create quaternion for heading
#         odom_quat = Quaternion()
#         q = quaternion_from_euler(0, 0, self.heading)
#         odom_quat.x, odom_quat.y, odom_quat.z, odom_quat.w = q

#         # Populate and publish odometry message
#         odom = Odometry()
#         odom.header.stamp = current_time.to_msg()
#         odom.header.frame_id = self.odom_frame
#         odom.child_frame_id = self.base_footprint_frame

#         # Set position and orientation
#         odom.pose.pose.position.x = self.x_pos
#         odom.pose.pose.position.y = self.y_pos
#         odom.pose.pose.position.z = 0.0
#         odom.pose.pose.orientation = odom_quat
#         odom.pose.covariance[0] = 0.001
#         odom.pose.covariance[7] = 0.001
#         odom.pose.covariance[35] = 0.001

#         # Set linear and angular velocities
#         odom.twist.twist.linear.x = self.linear_velocity_x
#         odom.twist.twist.linear.y = self.linear_velocity_y
#         odom.twist.twist.linear.z = 0.0
#         odom.twist.twist.angular.x = 0.0
#         odom.twist.twist.angular.y = 0.0
#         odom.twist.twist.angular.z = self.angular_velocity_z
#         odom.twist.covariance[0] = 0.0001
#         odom.twist.covariance[7] = 0.0001
#         odom.twist.covariance[35] = 0.0001

#         # Publish odometry message
#         self.odom_publisher.publish(odom)


# def main(args=None):
#     rclpy.init(args=args)
#     node = OdomPublisher()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

