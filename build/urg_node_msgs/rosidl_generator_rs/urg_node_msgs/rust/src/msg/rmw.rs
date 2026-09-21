#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "urg_node_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__urg_node_msgs__msg__Status() -> *const std::ffi::c_void;
}

#[link(name = "urg_node_msgs__rosidl_generator_c")]
extern "C" {
    fn urg_node_msgs__msg__Status__init(msg: *mut Status) -> bool;
    fn urg_node_msgs__msg__Status__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Status>, size: usize) -> bool;
    fn urg_node_msgs__msg__Status__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Status>);
    fn urg_node_msgs__msg__Status__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Status>, out_seq: *mut rosidl_runtime_rs::Sequence<Status>) -> bool;
}

// Corresponds to urg_node_msgs__msg__Status
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Normal vs setting in the UAM manual.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Status {

    // This member is not documented.
    #[allow(missing_docs)]
    pub operating_mode: u16,

    /// The configured area number the stop occurred in.
    pub area_number: u16,

    /// If the laser is reporting an error or not.
    pub error_status: bool,

    /// The error code the laser is reporting.
    pub error_code: u16,

    /// Does the laser report that it is locked out.
    pub lockout_status: bool,

    /// State of the different warning and safety zones
    pub ossd_1: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ossd_2: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub warning_1: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub warning_2: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ossd_3: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ossd_4: bool,

    /// Distance in mm the stop was reported at.
    pub distance: u16,

    /// The reported angle of the stop in deg.
    pub angle: f32,

}

impl Status {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const NORMAL: u16 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SETTING: u16 = 1;

}


impl Default for Status {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !urg_node_msgs__msg__Status__init(&mut msg as *mut _) {
        panic!("Call to urg_node_msgs__msg__Status__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Status {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { urg_node_msgs__msg__Status__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { urg_node_msgs__msg__Status__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { urg_node_msgs__msg__Status__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Status {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Status where Self: Sized {
  const TYPE_NAME: &'static str = "urg_node_msgs/msg/Status";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__urg_node_msgs__msg__Status() }
  }
}


