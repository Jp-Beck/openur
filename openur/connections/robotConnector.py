'''
Python 3.x library to control an UR robot through its TCP/IP interfaces
Copyright (C) 2017  Martin Huus Bjerge, Rope Robotics ApS, Denmark

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software 
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies 
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL "Rope Robotics ApS" BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Except as contained in this notice, the name of "Rope Robotics ApS" shall not be used 
in advertising or otherwise to promote the sale, use or other dealings in this Software 
without prior written authorization from "Rope Robotics ApS".
'''
__author__ = "Martin Huus Bjerge"
__copyright__ = "Copyright 2017, Rope Robotics ApS, Denmark"
__license__ = "MIT License"

import openur
# import URplus
from openur.rtde_command import RTDECommands

class RobotConnector:
    """
    Class to hold all connections to the Universal Robot and additional devices.
    """
    def __init__(self, robot_model: RTDECommands, host: str, has_force_torque: bool = False):
        """
        Constructor. Initializes connection with the robot and any additional devices.

        :param robot_model: Instance of RobotModel to be used.
        :param host: IP address of the robot.
        :param has_force_torque: Boolean indicating if a force/torque sensor is present.
        """
        self.robot_model = robot_model
        self.robot_model.ip_address = host
        self.robot_model.has_force_torque_sensor = has_force_torque

        self.real_time_client = .connections.RealTimeClient(self.robot_model)
        self.data_log = URBasic.dataLog.DataLog(self.robot_model)
        self.rtde = URBasic.rtde.RTDE(self.robot_model)
        self.dashboard_client = URBasic.dashboard.DashBoard(self.robot_model)
        self.force_torque = None

        if has_force_torque:
            self.force_torque = URplus.forceTorqueSensor.ForceTorqueSensor(self.robot_model)

        logger = URBasic.dataLogging.DataLogging()
        name = logger.add_event_logging(__name__)
        self.__logger = logger.__dict__[name]
        self.__logger.info('Init done')

    def close(self) -> None:
        """
        Close all connections to the robot and any additional devices.
        """
        self.data_log.close()
        self.rtde.close()
        self.real_time_client.disconnect()
        self.dashboard_client.close()

        if self.force_torque is not None:
            self.force_torque.close()

