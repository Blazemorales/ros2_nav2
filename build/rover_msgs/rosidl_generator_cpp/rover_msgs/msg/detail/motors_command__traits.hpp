// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from rover_msgs:msg/MotorsCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "rover_msgs/msg/motors_command.hpp"


#ifndef ROVER_MSGS__MSG__DETAIL__MOTORS_COMMAND__TRAITS_HPP_
#define ROVER_MSGS__MSG__DETAIL__MOTORS_COMMAND__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "rover_msgs/msg/detail/motors_command__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace rover_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const MotorsCommand & msg,
  std::ostream & out)
{
  out << "{";
  // member: drive_motor
  {
    if (msg.drive_motor.size() == 0) {
      out << "drive_motor: []";
    } else {
      out << "drive_motor: [";
      size_t pending_items = msg.drive_motor.size();
      for (auto item : msg.drive_motor) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: corner_motor
  {
    if (msg.corner_motor.size() == 0) {
      out << "corner_motor: []";
    } else {
      out << "corner_motor: [";
      size_t pending_items = msg.corner_motor.size();
      for (auto item : msg.corner_motor) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const MotorsCommand & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: drive_motor
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.drive_motor.size() == 0) {
      out << "drive_motor: []\n";
    } else {
      out << "drive_motor:\n";
      for (auto item : msg.drive_motor) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: corner_motor
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.corner_motor.size() == 0) {
      out << "corner_motor: []\n";
    } else {
      out << "corner_motor:\n";
      for (auto item : msg.corner_motor) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const MotorsCommand & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace rover_msgs

namespace rosidl_generator_traits
{

[[deprecated("use rover_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const rover_msgs::msg::MotorsCommand & msg,
  std::ostream & out, size_t indentation = 0)
{
  rover_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use rover_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const rover_msgs::msg::MotorsCommand & msg)
{
  return rover_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<rover_msgs::msg::MotorsCommand>()
{
  return "rover_msgs::msg::MotorsCommand";
}

template<>
inline const char * name<rover_msgs::msg::MotorsCommand>()
{
  return "rover_msgs/msg/MotorsCommand";
}

template<>
struct has_fixed_size<rover_msgs::msg::MotorsCommand>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<rover_msgs::msg::MotorsCommand>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<rover_msgs::msg::MotorsCommand>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROVER_MSGS__MSG__DETAIL__MOTORS_COMMAND__TRAITS_HPP_
