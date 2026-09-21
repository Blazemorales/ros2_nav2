# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target urg_node_msgs::urg_node_msgs
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${urg_node_msgs_TARGETS}.
if(urg_node_msgs_TARGETS AND NOT TARGET urg_node_msgs::urg_node_msgs)
  add_library(urg_node_msgs::urg_node_msgs INTERFACE IMPORTED)
  set_target_properties(urg_node_msgs::urg_node_msgs PROPERTIES
    INTERFACE_LINK_LIBRARIES "${urg_node_msgs_TARGETS}")
endif()
