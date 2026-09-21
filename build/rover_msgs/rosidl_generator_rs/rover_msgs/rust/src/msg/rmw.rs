#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "rover_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__rover_msgs__msg__MotorsCommand() -> *const std::ffi::c_void;
}

#[link(name = "rover_msgs__rosidl_generator_c")]
extern "C" {
    fn rover_msgs__msg__MotorsCommand__init(msg: *mut MotorsCommand) -> bool;
    fn rover_msgs__msg__MotorsCommand__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<MotorsCommand>, size: usize) -> bool;
    fn rover_msgs__msg__MotorsCommand__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<MotorsCommand>);
    fn rover_msgs__msg__MotorsCommand__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<MotorsCommand>, out_seq: *mut rosidl_runtime_rs::Sequence<MotorsCommand>) -> bool;
}

// Corresponds to rover_msgs__msg__MotorsCommand
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MotorsCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub drive_motor: rosidl_runtime_rs::Sequence<i32>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub corner_motor: rosidl_runtime_rs::Sequence<i32>,

}



impl Default for MotorsCommand {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !rover_msgs__msg__MotorsCommand__init(&mut msg as *mut _) {
        panic!("Call to rover_msgs__msg__MotorsCommand__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for MotorsCommand {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { rover_msgs__msg__MotorsCommand__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { rover_msgs__msg__MotorsCommand__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { rover_msgs__msg__MotorsCommand__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for MotorsCommand {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for MotorsCommand where Self: Sized {
  const TYPE_NAME: &'static str = "rover_msgs/msg/MotorsCommand";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__rover_msgs__msg__MotorsCommand() }
  }
}


