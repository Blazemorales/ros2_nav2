import sys
if sys.prefix == '/home/mr-morales/miniforge3/envs/ros2_jazzy':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/mr-morales/ros2_ws/install/rover_motor_controller'
