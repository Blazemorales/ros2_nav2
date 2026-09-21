// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from rover_msgs:msg/MotorsCommand.idl
// generated code does not contain a copyright notice

#include "rover_msgs/msg/detail/motors_command__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_rover_msgs
const rosidl_type_hash_t *
rover_msgs__msg__MotorsCommand__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x98, 0xbf, 0x53, 0x3a, 0x84, 0x8d, 0x69, 0xae,
      0x21, 0x8d, 0x92, 0x47, 0x0c, 0xea, 0xa3, 0xd7,
      0xec, 0xdc, 0x7f, 0x7b, 0x92, 0x0d, 0x9f, 0x84,
      0x50, 0x7d, 0x30, 0xcf, 0x73, 0x49, 0x39, 0x54,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char rover_msgs__msg__MotorsCommand__TYPE_NAME[] = "rover_msgs/msg/MotorsCommand";

// Define type names, field names, and default values
static char rover_msgs__msg__MotorsCommand__FIELD_NAME__drive_motor[] = "drive_motor";
static char rover_msgs__msg__MotorsCommand__FIELD_NAME__corner_motor[] = "corner_motor";

static rosidl_runtime_c__type_description__Field rover_msgs__msg__MotorsCommand__FIELDS[] = {
  {
    {rover_msgs__msg__MotorsCommand__FIELD_NAME__drive_motor, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {rover_msgs__msg__MotorsCommand__FIELD_NAME__corner_motor, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
rover_msgs__msg__MotorsCommand__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {rover_msgs__msg__MotorsCommand__TYPE_NAME, 28, 28},
      {rover_msgs__msg__MotorsCommand__FIELDS, 2, 2},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "int32[] drive_motor\n"
  "int32[] corner_motor";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
rover_msgs__msg__MotorsCommand__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {rover_msgs__msg__MotorsCommand__TYPE_NAME, 28, 28},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 40, 40},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
rover_msgs__msg__MotorsCommand__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *rover_msgs__msg__MotorsCommand__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
