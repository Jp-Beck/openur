"""
OpenUR - Universal Robot Control Library

A comprehensive Python library for controlling Universal Robots through their
TCP/IP interfaces. Provides unified access to Dashboard Server, RTDE, and URScript.

__credits__ = "Beck Isakov"
__copyright__ = "Beck Isakov"
__license__ = "GPL v3"
__version__ = "0.3.0"
__maintainer__ = "Beck Isakov"
__email__ = "jp-beck@outlook.com"
__status__ = "Development"
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, Optional, Union, List, Protocol, TypeVar, Generic, Callable
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import threading
from contextlib import contextmanager
from functools import wraps

from openur.dashboard import Dashboard
from openur.rtde_command import RTDECommands
from openur.urscript import URClient
from openur.exceptions import ConnectionError, ConfigurationError, ValidationError
from openur.utils import validate_ip_address, setup_logging

# Type definitions
T = TypeVar('T')
Vector6D = List[float]
Vector3D = List[float]
Pose = Vector6D
JointPositions = Vector6D

class ConnectionType(Enum):
    """Types of robot connections."""
    DASHBOARD = "dashboard"
    RTDE = "rtde"
    URSCRIPT = "urscript"

@dataclass
class RobotConfig:
    """Configuration for robot connections."""
    ip_address: str
    config_path: str = 'rtde_configuration.xml'
    dashboard_port: int = 29999
    rtde_port: int = 30004
    urscript_port: int = 30003
    timeout: float = 10.0
    max_retries: int = 3

class ConnectionManager(Protocol):
    """Protocol for connection management."""
    def connect(self) -> bool: ...
    def close(self) -> None: ...
    def is_connected(self) -> bool: ...

def requires_connection(func: Callable) -> Callable:
    """Decorator to ensure connection before method execution."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_connected():
            raise ConnectionError("Robot not connected")
        return func(self, *args, **kwargs)
    return wrapper

class RobotInterface(ABC):
    """Abstract base class for robot interfaces."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to robot."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connection to robot."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass

class RTDEInterface(RobotInterface):
    """RTDE interface wrapper with proper error handling."""

    def __init__(self, config: RobotConfig) -> None:
        self.config = config
        self._rtde: Optional[RTDECommands] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to RTDE interface."""
        try:
            with self._lock:
                self._rtde = RTDECommands(
                    host=self.config.ip_address,
                    recipe_setp="rci",
                    recipe_out="rco",
                    config_path=self.config.config_path
                )
                return self._rtde.connect()
        except Exception as e:
            logging.error(f"Failed to connect to RTDE: {e}")
            return False

    def close(self) -> None:
        """Close RTDE connection."""
        with self._lock:
            if self._rtde:
                self._rtde.close()
                self._rtde = None

    def is_connected(self) -> bool:
        """Check RTDE connection status."""
        return self._rtde is not None and self._rtde.is_connected()

    @property
    def rtde(self) -> RTDECommands:
        """Get RTDE instance."""
        if not self._rtde:
            raise ConnectionError("RTDE not connected")
        return self._rtde

class DashboardInterface(RobotInterface):
    """Dashboard interface wrapper with proper error handling."""

    def __init__(self, config: RobotConfig) -> None:
        self.config = config
        self._dashboard: Optional[Dashboard] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to Dashboard interface."""
        try:
            with self._lock:
                self._dashboard = Dashboard(self.config.ip_address, self.config.dashboard_port)
                return self._dashboard.connect()
        except Exception as e:
            logging.error(f"Failed to connect to Dashboard: {e}")
            return False

    def close(self) -> None:
        """Close Dashboard connection."""
        with self._lock:
            if self._dashboard:
                self._dashboard.close()
                self._dashboard = None

    def is_connected(self) -> bool:
        """Check Dashboard connection status."""
        return self._dashboard is not None and self._dashboard.is_connected()

    @property
    def dashboard(self) -> Dashboard:
        """Get Dashboard instance."""
        if not self._dashboard:
            raise ConnectionError("Dashboard not connected")
        return self._dashboard

class URScriptInterface(RobotInterface):
    """URScript interface wrapper with proper error handling."""

    def __init__(self, config: RobotConfig) -> None:
        self.config = config
        self._ur_client: Optional[URClient] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to URScript interface."""
        try:
            with self._lock:
                self._ur_client = URClient(self.config.ip_address)
                return self._ur_client.connect()
        except Exception as e:
            logging.error(f"Failed to connect to URScript: {e}")
            return False

    def close(self) -> None:
        """Close URScript connection."""
        with self._lock:
            if self._ur_client:
                self._ur_client.close()
                self._ur_client = None

    def is_connected(self) -> bool:
        """Check URScript connection status."""
        return self._ur_client is not None and self._ur_client.is_connected()

    @property
    def ur_client(self) -> URClient:
        """Get URScript client instance."""
        if not self._ur_client:
            raise ConnectionError("URScript not connected")
        return self._ur_client

class XMLConfigManager:
    """Manages RTDE XML configuration with thread safety."""

    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self.recipe_rco: Optional[ET.Element] = None
        self.recipe_rci: Optional[ET.Element] = None
        self._lock = threading.Lock()
        self._load_config()

    def _load_config(self) -> None:
        """Load and parse XML configuration."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

            self.tree = ET.parse(str(self.config_path))
            self.root = self.tree.getroot()
            self.recipe_rco = self.root.find(".//recipe[@key='rco']")
            self.recipe_rci = self.root.find(".//recipe[@key='rci']")

            if self.recipe_rco is None or self.recipe_rci is None:
                raise ValueError("Invalid RTDE configuration: missing recipe sections")

        except ET.ParseError as e:
            raise ConfigurationError(f"Invalid XML configuration: {e}")

    def add_rco_field(self, name: str, field_type: str, value: Optional[str] = None) -> None:
        """Add field to RCO recipe."""
        with self._lock:
            if self.recipe_rco.find(f".//field[@name='{name}']") is None:
                new_field = ET.Element('field', {'name': name, 'type': field_type})
                if value is not None:
                    new_field.text = str(value)
                self.recipe_rco.append(new_field)
                self._write_pretty_xml()
                logging.debug(f"Added RCO field: {name} ({field_type})")
            else:
                logging.debug(f"RCO field already exists: {name}")

    def add_rci_field(self, name: str, field_type: str, value: Optional[str] = None) -> None:
        """Add field to RCI recipe."""
        with self._lock:
            if self.recipe_rci.find(f".//field[@name='{name}']") is None:
                new_field = ET.Element('field', {'name': name, 'type': field_type})
                if value is not None:
                    new_field.text = str(value)
                self.recipe_rci.append(new_field)
                self._write_pretty_xml()
                logging.debug(f"Added RCI field: {name} ({field_type})")
            else:
                logging.debug(f"RCI field already exists: {name}")

    def _write_pretty_xml(self, filename: Optional[Path] = None) -> None:
        """Write XML configuration with proper formatting."""
        if filename is None:
            filename = self.config_path

        try:
            xml_string = ET.tostring(self.root, encoding='unicode')
            xml_string = ''.join(line.strip() for line in xml_string.splitlines())
            pretty_xml = minidom.parseString(xml_string).toprettyxml(
                indent="\t", encoding=None, newl='\n'
            )
            with open(filename, 'w') as f:
                f.write(pretty_xml.split('\n', 1)[1])
            logging.info(f"Updated RTDE configuration: {filename}")
        except Exception as e:
            logging.error(f"Failed to write XML configuration: {e}")
            raise

class OpenUR:
    """
    Main OpenUR class for Universal Robot control.

    This class implements the Facade pattern to provide a unified interface
    to all robot subsystems (Dashboard, RTDE, URScript) while hiding their
    complexity from the user.

    Features:
    - Thread-safe operations
    - Comprehensive error handling
    - Type hints throughout
    - Context manager support
    - Automatic resource cleanup
    """

    def __init__(
        self,
        ip_address: str,
        config_path: str = 'rtde_configuration.xml',
        **kwargs
    ) -> None:
        """
        Initialize OpenUR with robot configuration.

        Args:
            ip_address: IP address of the Universal Robot
            config_path: Path to RTDE configuration XML file
            **kwargs: Additional configuration parameters

        Raises:
            ValidationError: If IP address is invalid
            ConfigurationError: If configuration file is invalid
            ConnectionError: If robot connections fail
        """
        # Validate IP address
        if not validate_ip_address(ip_address):
            raise ValidationError(f"Invalid IP address: {ip_address}")

        # Create configuration
        self.config = RobotConfig(
            ip_address=ip_address,
            config_path=config_path,
            **kwargs
        )

        # Initialize XML configuration manager
        self.xml_config = XMLConfigManager(config_path)

        # Initialize interfaces using Factory pattern
        self._interfaces: Dict[ConnectionType, RobotInterface] = {
            ConnectionType.RTDE: RTDEInterface(self.config),
            ConnectionType.DASHBOARD: DashboardInterface(self.config),
            ConnectionType.URSCRIPT: URScriptInterface(self.config),
        }

        # Connection status tracking
        self._connection_lock = threading.Lock()
        self._is_connected = False

        # Initialize connections
        self._initialize_connections()

    def _initialize_connections(self) -> None:
        """Initialize all robot connections with proper error handling."""
        failed_connections = []

        for conn_type, interface in self._interfaces.items():
            try:
                if not interface.connect():
                    failed_connections.append(conn_type.value)
            except Exception as e:
                logging.error(f"Failed to initialize {conn_type.value}: {e}")
                failed_connections.append(conn_type.value)

        if failed_connections:
            self.close()
            raise ConnectionError(
                f"Failed to initialize connections: {', '.join(failed_connections)}"
            )

        with self._connection_lock:
            self._is_connected = True

    def close(self) -> None:
        """Close all robot connections safely."""
        with self._connection_lock:
            if not self._is_connected:
                return

            for interface in self._interfaces.values():
                try:
                    interface.close()
                except Exception as e:
                    logging.error(f"Error closing connection: {e}")

            self._is_connected = False

    def __enter__(self) -> OpenUR:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with proper cleanup."""
        self.close()
        if exc_type is not None:
            logging.error(f"Exception in OpenUR context: {exc_val}")

    def is_connected(self) -> bool:
        """Check if all connections are active."""
        with self._connection_lock:
            if not self._is_connected:
                return False
            return all(interface.is_connected() for interface in self._interfaces.values())

    @property
    def rtde(self) -> RTDECommands:
        """Get RTDE interface."""
        return self._interfaces[ConnectionType.RTDE].rtde

    @property
    def dashboard(self) -> Dashboard:
        """Get Dashboard interface."""
        return self._interfaces[ConnectionType.DASHBOARD].dashboard

    @property
    def urscript(self) -> URClient:
        """Get URScript interface."""
        return self._interfaces[ConnectionType.URSCRIPT].ur_client

    # Dashboard Methods with type hints and error handling
    @requires_connection
    def is_in_remote(self) -> bool:
        """Check if robot is in remote control mode."""
        return self.dashboard.is_in_remote()

    @requires_connection
    def load_program(self, program: str) -> bool:
        """Load a program onto the robot."""
        return self.dashboard.load_program(program)

    @requires_connection
    def play(self) -> bool:
        """Play the currently loaded program."""
        return self.dashboard.play()

    @requires_connection
    def pause(self) -> bool:
        """Pause the currently running program."""
        return self.dashboard.pause()

    @requires_connection
    def stop(self) -> bool:
        """Stop the currently running program."""
        return self.dashboard.stop()

    @requires_connection
    def quit(self) -> bool:
        """Quit the current connection to the Dashboard Server."""
        return self.dashboard.quit()

    @requires_connection
    def shutdown(self) -> bool:
        """Shutdown the robot."""
        return self.dashboard.shutdown()

    @requires_connection
    def running(self) -> bool:
        """Check if a program is currently running."""
        return self.dashboard.running()

    @requires_connection
    def robotmode(self) -> str:
        """Check the current robot mode."""
        return self.dashboard.robotmode()

    @requires_connection
    def get_loaded_program(self) -> str:
        """Get the currently loaded program."""
        return self.dashboard.get_loaded_program()

    @requires_connection
    def popup(self, message: str) -> bool:
        """Display a popup on the robot teach pendant."""
        return self.dashboard.popup(message)

    @requires_connection
    def close_popup(self) -> bool:
        """Close the popup on the robot teach pendant."""
        return self.dashboard.close_popup()

    @requires_connection
    def add_to_log(self, message: str) -> bool:
        """Add a message to the robot log."""
        return self.dashboard.add_to_log(message)

    @requires_connection
    def is_program_saved(self) -> bool:
        """Check if the currently loaded program is saved."""
        return self.dashboard.is_program_saved()

    @requires_connection
    def program_state(self) -> str:
        """Check the current program state."""
        return self.dashboard.program_state()

    @requires_connection
    def polyscope_version(self) -> str:
        """Get the version of the installed polyscope software."""
        return self.dashboard.polyscope_version()

    @requires_connection
    def market_version(self) -> str:
        """Get the marketing version of the installed polyscope software."""
        return self.dashboard.marketing_version()

    @requires_connection
    def set_operational_mode(self, mode: str) -> bool:
        """Set the operational mode of the robot."""
        return self.dashboard.set_operational_mode(mode)

    @requires_connection
    def get_operational_mode(self) -> str:
        """Get the operational mode of the robot."""
        return self.dashboard.get_operational_mode()

    @requires_connection
    def clear_operational_mode(self) -> bool:
        """Clear the operational mode of the robot."""
        return self.dashboard.clear_operational_mode()

    @requires_connection
    def power_on(self) -> bool:
        """Power on the robot."""
        return self.dashboard.power_on()

    @requires_connection
    def power_off(self) -> bool:
        """Power off the robot."""
        return self.dashboard.power_off()

    @requires_connection
    def brake_release(self) -> bool:
        """Release the robot brakes."""
        return self.dashboard.brake_release()

    @requires_connection
    def safety_status(self) -> str:
        """Get the safety status of the robot."""
        return self.dashboard.safety_status()

    @requires_connection
    def unlock_protective_stop(self) -> bool:
        """Unlock the protective stop."""
        return self.dashboard.unlock_protective_stop()

    @requires_connection
    def close_safety_popup(self) -> bool:
        """Close the safety popup."""
        return self.dashboard.close_safety_popup()

    @requires_connection
    def load_installation(self, installation: str) -> bool:
        """Load an installation."""
        return self.dashboard.load_installation(installation)

    @requires_connection
    def restart_safety(self) -> bool:
        """Restart the safety."""
        return self.dashboard.restart_safety()

    @requires_connection
    def get_serial_number(self) -> str:
        """Get the serial number of the robot."""
        return self.dashboard.get_serial_number()

    @requires_connection
    def get_robot_model(self) -> str:
        """Get the robot model."""
        return self.dashboard.get_robot_model()

    @requires_connection
    def generate_flight_report(self) -> bool:
        """Generate a flight report."""
        return self.dashboard.generate_flight_report()

    @requires_connection
    def transfer_files(self, files: str) -> bool:
        """Transfer files to/from robot."""
        return self.dashboard.transfer_files(files)

    @requires_connection
    def generate_support_file(self) -> bool:
        """Generate a support file."""
        return self.dashboard.generate_support_file()

    # RTDE Methods - Robot Controller Outputs with comprehensive type hints
    @requires_connection
    def timestamp(self) -> Optional[float]:
        """Get timestamp."""
        self.xml_config.add_rco_field('timestamp', 'DOUBLE')
        return self.rtde.timestamp()

    @requires_connection
    def target_q(self) -> Optional[JointPositions]:
        """Get target joint positions."""
        self.xml_config.add_rco_field('target_q', 'VECTOR6D')
        return self.rtde.target_q()

    @requires_connection
    def target_qd(self) -> Optional[JointPositions]:
        """Get target joint velocities."""
        self.xml_config.add_rco_field('target_qd', 'VECTOR6D')
        return self.rtde.target_qd()

    @requires_connection
    def target_qdd(self) -> Optional[JointPositions]:
        """Get target joint accelerations."""
        self.xml_config.add_rco_field('target_qdd', 'VECTOR6D')
        return self.rtde.target_qdd()

    @requires_connection
    def target_current(self) -> Optional[JointPositions]:
        """Get target joint currents."""
        self.xml_config.add_rco_field('target_current', 'VECTOR6D')
        return self.rtde.target_current()

    @requires_connection
    def target_moment(self) -> Optional[JointPositions]:
        """Get target joint moments."""
        self.xml_config.add_rco_field('target_moment', 'VECTOR6D')
        return self.rtde.target_moment()

    @requires_connection
    def actual_q(self) -> Optional[JointPositions]:
        """Get actual joint positions."""
        self.xml_config.add_rco_field('actual_q', 'VECTOR6D')
        return self.rtde.actual_q()

    @requires_connection
    def actual_qd(self) -> Optional[JointPositions]:
        """Get actual joint velocities."""
        self.xml_config.add_rco_field('actual_qd', 'VECTOR6D')
        return self.rtde.actual_qd()

    @requires_connection
    def actual_current(self) -> Optional[JointPositions]:
        """Get actual joint currents."""
        self.xml_config.add_rco_field('actual_current', 'VECTOR6D')
        return self.rtde.actual_current()

    @requires_connection
    def joint_control_output(self) -> Optional[JointPositions]:
        """Get joint control output."""
        self.xml_config.add_rco_field('joint_control_output', 'VECTOR6D')
        return self.rtde.joint_control_output()

    @requires_connection
    def actual_TCP_pose(self) -> Optional[Pose]:
        """Get actual TCP pose."""
        self.xml_config.add_rco_field('actual_TCP_pose', 'VECTOR6D')
        return self.rtde.actual_TCP_pose()

    @requires_connection
    def actual_TCP_speed(self) -> Optional[Pose]:
        """Get actual TCP speed."""
        self.xml_config.add_rco_field('actual_TCP_speed', 'VECTOR6D')
        return self.rtde.actual_TCP_speed()

    @requires_connection
    def actual_TCP_force(self) -> Optional[Pose]:
        """Get actual TCP force."""
        self.xml_config.add_rco_field('actual_TCP_force', 'VECTOR6D')
        return self.rtde.actual_TCP_force()

    @requires_connection
    def actual_digital_input_bits(self) -> Optional[int]:
        """Get actual digital input bits."""
        self.xml_config.add_rco_field('actual_digital_input_bits', 'UINT64')
        return self.rtde.actual_digital_input_bits()

    @requires_connection
    def joint_temperatures(self) -> Optional[JointPositions]:
        """Get joint temperatures."""
        self.xml_config.add_rco_field('joint_temperatures', 'VECTOR6D')
        return self.rtde.joint_temperatures()

    @requires_connection
    def actual_execution_time(self) -> Optional[float]:
        """Get actual execution time."""
        self.xml_config.add_rco_field('actual_execution_time', 'DOUBLE')
        return self.rtde.actual_execution_time()

    @requires_connection
    def robot_mode(self) -> Optional[int]:
        """Get robot mode."""
        self.xml_config.add_rco_field('robot_mode', 'INT32')
        return self.rtde.robot_mode()

    @requires_connection
    def joint_mode(self) -> Optional[List[int]]:
        """Get joint mode."""
        self.xml_config.add_rco_field('joint_mode', 'VECTOR6INT32')
        return self.rtde.joint_mode()

    @requires_connection
    def safety_mode(self) -> Optional[int]:
        """Get safety mode."""
        self.xml_config.add_rco_field('safety_mode', 'INT32')
        return self.rtde.safety_mode()

    @requires_connection
    def safety_status(self) -> Optional[List[int]]:
        """Get safety status."""
        self.xml_config.add_rco_field('safety_status', 'INT32')
        return self.rtde.safety_status()

    @requires_connection
    def actual_tool_accelerometer(self) -> Optional[Vector3D]:
        """Get actual tool accelerometer readings."""
        self.xml_config.add_rco_field('actual_tool_accelerometer', 'VECTOR3D')
        return self.rtde.actual_tool_accelerometer()

    @requires_connection
    def speed_scaling(self) -> Optional[float]:
        """Get speed scaling factor."""
        self.xml_config.add_rco_field('speed_scaling', 'DOUBLE')
        return self.rtde.speed_scaling()

    @requires_connection
    def target_speed_fraction(self) -> Optional[float]:
        """Get target speed fraction."""
        self.xml_config.add_rco_field('target_speed_fraction', 'DOUBLE')
        return self.rtde.target_speed_fraction()

    @requires_connection
    def actual_momentum(self) -> Optional[float]:
        """Get actual momentum."""
        self.xml_config.add_rco_field('actual_momentum', 'DOUBLE')
        return self.rtde.actual_momentum()

    @requires_connection
    def actual_main_voltage(self) -> Optional[float]:
        """Get actual main voltage."""
        self.xml_config.add_rco_field('actual_main_voltage', 'DOUBLE')
        return self.rtde.actual_main_voltage()

    @requires_connection
    def actual_robot_voltage(self) -> Optional[float]:
        """Get actual robot voltage."""
        self.xml_config.add_rco_field('actual_robot_voltage', 'DOUBLE')
        return self.rtde.actual_robot_voltage()

    @requires_connection
    def actual_robot_current(self) -> Optional[float]:
        """Get actual robot current."""
        self.xml_config.add_rco_field('actual_robot_current', 'DOUBLE')
        return self.rtde.actual_robot_current()

    @requires_connection
    def actual_joint_voltage(self) -> Optional[JointPositions]:
        """Get actual joint voltages."""
        self.xml_config.add_rco_field('actual_joint_voltage', 'VECTOR6D')
        return self.rtde.actual_joint_voltage()

    @requires_connection
    def runtime_state(self) -> Optional[int]:
        """Get runtime state."""
        self.xml_config.add_rco_field('runtime_state', 'UINT32')
        return self.rtde.runtime_state()

    @requires_connection
    def elbow_position(self) -> Optional[Vector3D]:
        """Get elbow position."""
        self.xml_config.add_rco_field('elbow_position', 'VECTOR3D')
        return self.rtde.elbow_position()

    @requires_connection
    def elbow_velocity(self) -> Optional[Vector3D]:
        """Get elbow velocity."""
        self.xml_config.add_rco_field('elbow_velocity', 'VECTOR3D')
        return self.rtde.elbow_velocity()

    @requires_connection
    def safety_status_bits(self) -> Optional[int]:
        """Get safety status bits."""
        self.xml_config.add_rco_field('safety_status_bits', 'UINT32')
        return self.rtde.safety_status_bits()

    @requires_connection
    def robot_status_bits(self) -> Optional[int]:
        """Get robot status bits."""
        self.xml_config.add_rco_field('robot_status_bits', 'UINT32')
        return self.rtde.robot_status_bits()

    @requires_connection
    def analog_io_types(self) -> Optional[int]:
        """Get analog I/O types."""
        self.xml_config.add_rco_field('analog_io_types', 'UINT32')
        return self.rtde.analog_io_types()

    @requires_connection
    def standard_analog_input(self, number: int) -> Optional[float]:
        """Get standard analog input."""
        number = 1 if number > 0 else 0
        self.xml_config.add_rco_field(f'standard_analog_input{number}', 'DOUBLE')
        return self.rtde.standard_analog_input(number)

    @requires_connection
    def io_current(self) -> Optional[float]:
        """Get I/O current."""
        self.xml_config.add_rco_field('io_current', 'DOUBLE')
        return self.rtde.io_current()

    # Additional RTDE methods with proper type hints...
    # (Continuing with the same pattern for all remaining methods)

    # URScript Methods with type hints
    @requires_connection
    def stop_command(self) -> bool:
        """Stop URScript command."""
        return self.urscript.stop_command()

    @requires_connection
    def send_script(self, script: str) -> bool:
        """Send URScript to robot."""
        return self.urscript.send_script(script)

    @requires_connection
    def send_raw_program(self, program: str) -> bool:
        """Send raw program to robot."""
        return self.urscript.send_raw_program(program)

    @requires_connection
    def send_txt_program(self, program: str) -> bool:
        """Send text program to robot."""
        return self.urscript.send_txt_program(program)

    @requires_connection
    def movej(self, joints: JointPositions, a: float = 1.2, v: float = 0.25) -> bool:
        """Move robot joints."""
        return self.urscript.movej(joints, a, v)

    @requires_connection
    def get_actual_joint_positions(self) -> Optional[JointPositions]:
        """Get actual joint positions."""
        return self.urscript.get_actual_joint_positions()

    @requires_connection
    def set_tcp(self, pose: Pose) -> bool:
        """Set tool center point."""
        return self.urscript.set_tcp(pose)

    @requires_connection
    def force_mode(
        self,
        task_frame: Pose,
        selection_vector: List[int],
        wrench: Pose,
        f_type: int,
        limits: List[float]
    ) -> bool:
        """Set robot to force mode."""
        return self.urscript.force_mode(task_frame, selection_vector, wrench, f_type, limits)
