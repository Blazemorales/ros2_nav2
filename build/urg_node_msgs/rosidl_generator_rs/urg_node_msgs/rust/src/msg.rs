#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to urg_node_msgs__msg__Status
/// Normal vs setting in the UAM manual.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Status::default())
  }
}

impl rosidl_runtime_rs::Message for Status {
  type RmwMsg = super::msg::rmw::Status;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        operating_mode: msg.operating_mode,
        area_number: msg.area_number,
        error_status: msg.error_status,
        error_code: msg.error_code,
        lockout_status: msg.lockout_status,
        ossd_1: msg.ossd_1,
        ossd_2: msg.ossd_2,
        warning_1: msg.warning_1,
        warning_2: msg.warning_2,
        ossd_3: msg.ossd_3,
        ossd_4: msg.ossd_4,
        distance: msg.distance,
        angle: msg.angle,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      operating_mode: msg.operating_mode,
      area_number: msg.area_number,
      error_status: msg.error_status,
      error_code: msg.error_code,
      lockout_status: msg.lockout_status,
      ossd_1: msg.ossd_1,
      ossd_2: msg.ossd_2,
      warning_1: msg.warning_1,
      warning_2: msg.warning_2,
      ossd_3: msg.ossd_3,
      ossd_4: msg.ossd_4,
      distance: msg.distance,
      angle: msg.angle,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      operating_mode: msg.operating_mode,
      area_number: msg.area_number,
      error_status: msg.error_status,
      error_code: msg.error_code,
      lockout_status: msg.lockout_status,
      ossd_1: msg.ossd_1,
      ossd_2: msg.ossd_2,
      warning_1: msg.warning_1,
      warning_2: msg.warning_2,
      ossd_3: msg.ossd_3,
      ossd_4: msg.ossd_4,
      distance: msg.distance,
      angle: msg.angle,
    }
  }
}


