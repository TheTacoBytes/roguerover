#!/usr/bin/env python
# encoding: utf-8

import sys
import math
import random
import threading
from math import pi
from time import sleep
from Rosmaster_Lib import Rosmaster

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32, Int32, Bool
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, MagneticField, JointState
from rclpy.clock import Clock

car_type_dic = {
    'R2': 5,
    'X3': 1,
    'NONE': -1
}

class yahboomcar_driver(Node):
    def __init__(self, name):
        super().__init__(name)
        global car_type_dic
        self.RA2DE = 180 / pi
        self.car = Rosmaster()
        self.car.set_car_type(1)
        
        # Get parameters
        self.declare_parameter('car_type', 'X3')
        self.car_type = self.get_parameter('car_type').get_parameter_value().string_value
        self.get_logger().info(f"Car type: {self.car_type}")
        
        self.declare_parameter('imu_link', 'imu_link')
        self.imu_link = self.get_parameter('imu_link').get_parameter_value().string_value
        self.get_logger().info(f"IMU link: {self.imu_link}")
        
        self.declare_parameter('Prefix', "")
        self.Prefix = self.get_parameter('Prefix').get_parameter_value().string_value
        self.get_logger().info(f"Prefix: {self.Prefix}")
        
        self.declare_parameter('xlinear_limit', 1.0)
        self.xlinear_limit = self.get_parameter('xlinear_limit').get_parameter_value().double_value
        self.get_logger().info(f"xlinear_limit: {self.xlinear_limit}")
        
        self.declare_parameter('ylinear_limit', 1.0)
        self.ylinear_limit = self.get_parameter('ylinear_limit').get_parameter_value().double_value
        self.get_logger().info(f"ylinear_limit: {self.ylinear_limit}")
        
        self.declare_parameter('angular_limit', 5.0)
        self.angular_limit = self.get_parameter('angular_limit').get_parameter_value().double_value
        self.get_logger().info(f"angular_limit: {self.angular_limit}")

        # Create subscribers
        self.sub_cmd_vel = self.create_subscription(Twist, "cmd_vel", self.cmd_vel_callback, 1)
        self.sub_RGBLight = self.create_subscription(Int32, "RGBLight", self.RGBLightcallback, 100)
        self.sub_BUzzer = self.create_subscription(Bool, "Buzzer", self.Buzzercallback, 100)

        # Create publishers
        self.EdiPublisher = self.create_publisher(Float32, "edition", 100)
        self.volPublisher = self.create_publisher(Float32, "voltage", 100)
        self.staPublisher = self.create_publisher(JointState, "joint_states", 100)
        self.velPublisher = self.create_publisher(Twist, "vel_raw", 50)
        self.imuPublisher = self.create_publisher(Imu, "imu/data_raw", 100)
        self.magPublisher = self.create_publisher(MagneticField, "imu/mag", 100)

        # Create timer
        self.timer = self.create_timer(0.1, self.pub_data)

        # Initialize variable(s)
        self.edition = Float32()
        self.edition.data = 1.0
        
        # Start thread to receive data from the hardware
        self.car.create_receive_threading()

    # Callback for velocity commands
    def cmd_vel_callback(self, msg):
        self.get_logger().info(f"message type: {msg}")
        
        if msg is None:
            self.get_logger().warn("No message received (None)!")
            self.get_logger().info(f"Received type: {type(msg)}")
            return
        
        if not isinstance(msg, Twist):
            return
        vx = msg.linear.x * 1.0
        vy = msg.linear.y * 1.0
        angular = msg.angular.z * 1.0
        self.car.set_car_motion(vx, vy, angular)

    def RGBLightcallback(self, msg):
        if not isinstance(msg, Int32):
            return
        for i in range(3):
            self.car.set_colorful_effect(msg.data, 6, parm=1)

    def Buzzercallback(self, msg):
        if not isinstance(msg, Bool):
            return
        if msg.data:
            for i in range(3):
                self.car.set_beep(1)
        else:
            for i in range(3):
                self.car.set_beep(0)

    # Timer callback to publish sensor data and joint states
    def pub_data(self):
        time_stamp = Clock().now()
        
        # Prepare sensor messages
        imu = Imu()
        twist = Twist()
        battery = Float32()
        edition = Float32()
        mag = MagneticField()
        
        # Prepare joint state message with 4 joints matching the URDF
        state = JointState()
        state.header.stamp = time_stamp.to_msg()
        state.header.frame_id = "joint_states"
        if len(self.Prefix) == 0:
            state.name = ["back_right_joint", "back_left_joint", "front_right_joint", "front_left_joint"]
        else:
            state.name = [self.Prefix + "back_right_joint", self.Prefix + "back_left_joint", 
                          self.Prefix + "front_right_joint", self.Prefix + "front_left_joint"]
        # Set joint positions to zero (or update with real feedback if available)
        state.position = [0.0 for _ in state.name]
        state.velocity = [0.0 for _ in state.name]
        state.effort = [0.0 for _ in state.name]

        # Get data from hardware
        edition.data = self.car.get_version() * 1.0
        battery.data = self.car.get_battery_voltage() * 1.0
        ax, ay, az = self.car.get_accelerometer_data()
        gx, gy, gz = self.car.get_gyroscope_data()
        mx, my, mz = self.car.get_magnetometer_data()
        vx, vy, angular = self.car.get_motion_data()

        # Populate IMU message
        imu.header.stamp = time_stamp.to_msg()
        imu.header.frame_id = self.imu_link
        imu.linear_acceleration.x = ax * 1.0
        imu.linear_acceleration.y = ay * 1.0
        imu.linear_acceleration.z = az * 1.0
        imu.angular_velocity.x = gx * 1.0
        imu.angular_velocity.y = gy * 1.0
        imu.angular_velocity.z = gz * 1.0

        # Populate magnetometer message
        mag.header.stamp = time_stamp.to_msg()
        mag.header.frame_id = self.imu_link
        mag.magnetic_field.x = mx * 1.0
        mag.magnetic_field.y = my * 1.0
        mag.magnetic_field.z = mz * 1.0

        # Populate Twist message for motion data
        twist.linear.x = vx * 1.0
        twist.linear.y = vy * 1.0
        twist.angular.z = angular * 1.0

        # Publish messages
        self.velPublisher.publish(twist)
        self.imuPublisher.publish(imu)
        self.magPublisher.publish(mag)
        self.volPublisher.publish(battery)
        self.EdiPublisher.publish(edition)
        self.staPublisher.publish(state)

def main():
    rclpy.init()
    driver = yahboomcar_driver('driver_node')
    rclpy.spin(driver)

if __name__ == '__main__':
    main()
