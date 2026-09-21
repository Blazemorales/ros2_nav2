// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from rover_msgs:msg/MotorsCommand.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "rover_msgs/msg/detail/motors_command__rosidl_typesupport_introspection_c.h"
#include "rover_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "rover_msgs/msg/detail/motors_command__functions.h"
#include "rover_msgs/msg/detail/motors_command__struct.h"


// Include directives for member types
// Member `drive_motor`
// Member `corner_motor`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  rover_msgs__msg__MotorsCommand__init(message_memory);
}

void rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_fini_function(void * message_memory)
{
  rover_msgs__msg__MotorsCommand__fini(message_memory);
}

size_t rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__size_function__MotorsCommand__drive_motor(
  const void * untyped_member)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return member->size;
}

const void * rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_const_function__MotorsCommand__drive_motor(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void * rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_function__MotorsCommand__drive_motor(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__fetch_function__MotorsCommand__drive_motor(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const int32_t * item =
    ((const int32_t *)
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_const_function__MotorsCommand__drive_motor(untyped_member, index));
  int32_t * value =
    (int32_t *)(untyped_value);
  *value = *item;
}

void rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__assign_function__MotorsCommand__drive_motor(
  void * untyped_member, size_t index, const void * untyped_value)
{
  int32_t * item =
    ((int32_t *)
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_function__MotorsCommand__drive_motor(untyped_member, index));
  const int32_t * value =
    (const int32_t *)(untyped_value);
  *item = *value;
}

bool rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__resize_function__MotorsCommand__drive_motor(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  rosidl_runtime_c__int32__Sequence__fini(member);
  return rosidl_runtime_c__int32__Sequence__init(member, size);
}

size_t rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__size_function__MotorsCommand__corner_motor(
  const void * untyped_member)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return member->size;
}

const void * rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_const_function__MotorsCommand__corner_motor(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void * rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_function__MotorsCommand__corner_motor(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__fetch_function__MotorsCommand__corner_motor(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const int32_t * item =
    ((const int32_t *)
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_const_function__MotorsCommand__corner_motor(untyped_member, index));
  int32_t * value =
    (int32_t *)(untyped_value);
  *value = *item;
}

void rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__assign_function__MotorsCommand__corner_motor(
  void * untyped_member, size_t index, const void * untyped_value)
{
  int32_t * item =
    ((int32_t *)
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_function__MotorsCommand__corner_motor(untyped_member, index));
  const int32_t * value =
    (const int32_t *)(untyped_value);
  *item = *value;
}

bool rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__resize_function__MotorsCommand__corner_motor(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  rosidl_runtime_c__int32__Sequence__fini(member);
  return rosidl_runtime_c__int32__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_member_array[2] = {
  {
    "drive_motor",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(rover_msgs__msg__MotorsCommand, drive_motor),  // bytes offset in struct
    NULL,  // default value
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__size_function__MotorsCommand__drive_motor,  // size() function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_const_function__MotorsCommand__drive_motor,  // get_const(index) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_function__MotorsCommand__drive_motor,  // get(index) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__fetch_function__MotorsCommand__drive_motor,  // fetch(index, &value) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__assign_function__MotorsCommand__drive_motor,  // assign(index, value) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__resize_function__MotorsCommand__drive_motor  // resize(index) function pointer
  },
  {
    "corner_motor",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(rover_msgs__msg__MotorsCommand, corner_motor),  // bytes offset in struct
    NULL,  // default value
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__size_function__MotorsCommand__corner_motor,  // size() function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_const_function__MotorsCommand__corner_motor,  // get_const(index) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__get_function__MotorsCommand__corner_motor,  // get(index) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__fetch_function__MotorsCommand__corner_motor,  // fetch(index, &value) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__assign_function__MotorsCommand__corner_motor,  // assign(index, value) function pointer
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__resize_function__MotorsCommand__corner_motor  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_members = {
  "rover_msgs__msg",  // message namespace
  "MotorsCommand",  // message name
  2,  // number of fields
  sizeof(rover_msgs__msg__MotorsCommand),
  false,  // has_any_key_member_
  rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_member_array,  // message members
  rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_init_function,  // function to initialize message memory (memory has to be allocated)
  rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_type_support_handle = {
  0,
  &rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_members,
  get_message_typesupport_handle_function,
  &rover_msgs__msg__MotorsCommand__get_type_hash,
  &rover_msgs__msg__MotorsCommand__get_type_description,
  &rover_msgs__msg__MotorsCommand__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_rover_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, rover_msgs, msg, MotorsCommand)() {
  if (!rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_type_support_handle.typesupport_identifier) {
    rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &rover_msgs__msg__MotorsCommand__rosidl_typesupport_introspection_c__MotorsCommand_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
