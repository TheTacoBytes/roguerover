# # Use the official ROS Humble Desktop Full image
# FROM osrf/ros:humble-desktop-full

# # Install necessary dependencies including CAN utilities
# RUN apt-get update && apt-get install -y \
#     can-utils \
#     python3-pip \
#     git \
#     cmake \
#     build-essential \
#     libasio-dev \
#     iproute2 \
#     ros-humble-tf2-geometry-msgs \
#     && rm -rf /var/lib/apt/lists/*

# # Create workspace and clone the repositories
# RUN mkdir -p /workspace/scout_ws/src && \
#     cd /workspace/scout_ws/src && \
#     git clone https://github.com/agilexrobotics/ugv_sdk.git && \
#     git clone --branch humble https://github.com/agilexrobotics/scout_ros2.git

# # Set environment variables for GUI support
# ENV DISPLAY=:0
# ENV QT_X11_NO_MITSHM=1

# WORKDIR /workspace
# # Bring up the CAN interface with a bitrate of 500000 when the container starts
# CMD ["/bin/bash", "-c", "ip link set can0 up type can bitrate 500000 && bash"]


# ORIGINAL ###################

# Use the official ROS Humble Desktop Full image
FROM osrf/ros:humble-desktop-full

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    git \
    cmake \
    build-essential \
    libasio-dev \
    ros-humble-tf2-geometry-msgs \
    && rm -rf /var/lib/apt/lists/*

# Create workspace and clone the repositories
RUN mkdir -p /workspace/scout_ws/src && \
    cd /workspace/scout_ws/src && \
    git clone https://github.com/agilexrobotics/ugv_sdk.git && \
    git clone --branch humble https://github.com/agilexrobotics/scout_ros2.git 

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && \
    cd /workspace/scout_ws && \
    colcon build"

RUN apt-get update && apt-get install -y \
    iproute2 \
    can-utils 

# Set environment variables for GUI support
ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1

# # Build the ROS2 workspace
# WORKDIR /workspace/scout_ws
# RUN . /opt/ros/humble/setup.sh && \
#     rosdep update && \
#     rosdep install --from-paths src --ignore-src -r -y && \
#     colcon build --symlink-install

# Set up entry point
WORKDIR /workspace
CMD ["bash"]

