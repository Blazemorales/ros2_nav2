#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to rover_msgs__msg__MotorsCommand

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MotorsCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub drive_motor: Vec<i32>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub corner_motor: Vec<i32>,

}



impl Default for MotorsCommand {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::MotorsCommand::default())
  }
}

impl rosidl_runtime_rs::Message for MotorsCommand {
  type RmwMsg = super::msg::rmw::MotorsCommand;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        drive_motor: msg.drive_motor.as_slice().into(),
        corner_motor: msg.corner_motor.as_slice().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        drive_motor: msg.drive_motor.as_slice().into(),
        corner_motor: msg.corner_motor.as_slice().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      drive_motor: msg.drive_motor.into(),
      corner_motor: msg.corner_motor.into(),
    }
  }
}


