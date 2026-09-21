# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target rover_msgs::rover_msgs
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${rover_msgs_TARGETS}.
if(rover_msgs_TARGETS AND NOT TARGET rover_msgs::rover_msgs)
  add_library(rover_msgs::rover_msgs INTERFACE IMPORTED)
  set_target_properties(rover_msgs::rover_msgs PROPERTIES
    INTERFACE_LINK_LIBRARIES "${rover_msgs_TARGETS}")
endif()
