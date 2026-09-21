// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from urg_node_msgs:msg/Status.idl
// generated code does not contain a copyright notice

#include "urg_node_msgs/msg/detail/status__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_urg_node_msgs
const rosidl_type_hash_t *
urg_node_msgs__msg__Status__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x7a, 0x25, 0x57, 0xa5, 0x49, 0xfd, 0x63, 0xef,
      0x39, 0x37, 0xf1, 0xc7, 0x7d, 0x5b, 0xed, 0xae,
      0x78, 0x95, 0x88, 0xf8, 0x6f, 0xab, 0xbe, 0xe5,
      0x30, 0x7b, 0xb5, 0x28, 0x82, 0x0e, 0xc2, 0x04,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char urg_node_msgs__msg__Status__TYPE_NAME[] = "urg_node_msgs/msg/Status";

// Define type names, field names, and default values
static char urg_node_msgs__msg__Status__FIELD_NAME__operating_mode[] = "operating_mode";
static char urg_node_msgs__msg__Status__FIELD_NAME__area_number[] = "area_number";
static char urg_node_msgs__msg__Status__FIELD_NAME__error_status[] = "error_status";
static char urg_node_msgs__msg__Status__FIELD_NAME__error_code[] = "error_code";
static char urg_node_msgs__msg__Status__FIELD_NAME__lockout_status[] = "lockout_status";
static char urg_node_msgs__msg__Status__FIELD_NAME__ossd_1[] = "ossd_1";
static char urg_node_msgs__msg__Status__FIELD_NAME__ossd_2[] = "ossd_2";
static char urg_node_msgs__msg__Status__FIELD_NAME__warning_1[] = "warning_1";
static char urg_node_msgs__msg__Status__FIELD_NAME__warning_2[] = "warning_2";
static char urg_node_msgs__msg__Status__FIELD_NAME__ossd_3[] = "ossd_3";
static char urg_node_msgs__msg__Status__FIELD_NAME__ossd_4[] = "ossd_4";
static char urg_node_msgs__msg__Status__FIELD_NAME__distance[] = "distance";
static char urg_node_msgs__msg__Status__FIELD_NAME__angle[] = "angle";

static rosidl_runtime_c__type_description__Field urg_node_msgs__msg__Status__FIELDS[] = {
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__operating_mode, 14, 14},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__area_number, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__error_status, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__error_code, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__lockout_status, 14, 14},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__ossd_1, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__ossd_2, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__warning_1, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__warning_2, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__ossd_3, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__ossd_4, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__distance, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {urg_node_msgs__msg__Status__FIELD_NAME__angle, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
urg_node_msgs__msg__Status__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {urg_node_msgs__msg__Status__TYPE_NAME, 24, 24},
      {urg_node_msgs__msg__Status__FIELDS, 13, 13},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "# Normal vs setting in the UAM manual.\n"
  "uint16 NORMAL=0\n"
  "uint16 SETTING=1\n"
  "uint16 operating_mode\n"
  "\n"
  "# The configured area number the stop occurred in.\n"
  "uint16 area_number\n"
  "# If the laser is reporting an error or not.\n"
  "bool error_status\n"
  "# The error code the laser is reporting.\n"
  "uint16 error_code\n"
  "# Does the laser report that it is locked out.\n"
  "bool lockout_status\n"
  "# State of the different warning and safety zones\n"
  "bool ossd_1\n"
  "bool ossd_2\n"
  "bool warning_1\n"
  "bool warning_2\n"
  "bool ossd_3\n"
  "bool ossd_4\n"
  "# Distance in mm the stop was reported at.\n"
  "uint16 distance\n"
  "# The reported angle of the stop in deg.\n"
  "float32 angle";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
urg_node_msgs__msg__Status__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {urg_node_msgs__msg__Status__TYPE_NAME, 24, 24},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 596, 596},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
urg_node_msgs__msg__Status__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *urg_node_msgs__msg__Status__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
