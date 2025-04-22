import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/beto/ROS_PROJECTS/scout/install/gaurd_bot'
