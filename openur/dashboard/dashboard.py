__all__ = ['Dashboard']

__author__ = "Beck Isakov"
__copyright__ = "Beck isakov"
__contact__ = "https://github.com/Jp-Beck"
__license__ = "GPL v3"
__version__ = "0.2.0"
__maintainer__ = "Beck Isakov"
__email__ = "jp-beck@outlook.com"
__status__ = "Development"

import socket
import time
import logging
import threading
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DashboardClient:
    def __init__(self, host, port, max_retries=10):
        self.host = host
        self.port = port
        self.conn = None
        self.max_retries = max_retries
        self.exit_flag = threading.Event()
        self.lock = threading.Lock()

    def connect(self):
        retries = 0
        while not self.exit_flag.is_set() and retries < self.max_retries:
            try:
                with self.lock:
                    if self.conn:
                        self.conn.close()
                    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.conn.connect((self.host, self.port))
                    data = self.conn.recv(1024).decode('utf8') # Do not delete this as it is needed to discard the greeting message from robot.
                logging.info('Dashboard Connection Established with {}:{}'.format(self.host, self.port))
                break 
            except (socket.error, Exception) as e:
                logging.error(f"Error connecting to {self.host}:{self.port}: {e}")
                retries += 1
                time.sleep(5 ** retries)

    def close(self):
        try:
            if self.conn:
                self.conn.close()
                logging.info('Dashboard Connection Closed with {}:{}'.format(self.host, self.port))
        except (socket.error, Exception) as e:
            logging.error(f"Error closing Dashboard connection to {self.host}:{self.port}: {e}")

    def stop_dashboard_connection(self):
        """Stop any ongoing connection attempts or operations."""
        self.exit_flag.set()
        self.close()

    def __del__(self): 
        self.stop_dashboard_connection()

    
class Dashboard(DashboardClient):
    """A remote control client for Universal Robots.

    This client connects to a remote UR dashboard server and provides an interface for checking the
    remote control status of the robot.
    """
    def __init__(self, host, port=29999, max_retries=10):
        """Initialize the Dashboard client."""
        super().__init__(host, port, max_retries)
        self.robot_model = None
        self.robot_model_lock = threading.Lock()
        self.program_state = None
        self.program_state_lock = threading.Lock()
        self.speed_slider_fraction = None
        self.speed_slider_fraction_lock = threading.Lock()
        self.speed_slider_mask = None
    
        # Dashboard Commands
    def is_in_remote(self):
        """Check if the robot is in remote control mode."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"is in remote control\n")
                    data = self.conn.recv(1024)
                if data == b'false\n':
                    return False
                elif data == b'true\n':
                    return True
                else:
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def load_program(self, filename):
        """Load a program onto the robot."""
        # Validate filename
        if not filename:
            raise ValueError("Filename cannot be empty.")
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(("load {}\n".format(filename)).encode('utf-8'))
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"loading program:"):
                    logging.info("Loading program: {}".format(filename))
                    return True
                elif data.lower().startswith(b"no program"):
                    logging.error("No program loaded: {}".format(filename))
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return False
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def play(self):
        """Play the currently loaded program."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"play\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"starting program"):
                    logging.info("Starting program")
                    return True
                elif data.lower().startswith(b'failed to execute: play\n'):
                    logging.error("Failed to execute play command")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def stop(self):
        """Stop the currently running program."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"stop\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"stopped"):
                    logging.info("Stopped program")
                    return True
                elif data.lower().startswith(b"no program"):
                    logging.error("No program loaded")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def pause(self):
        """Pause the currently running program."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"pause\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"pausing program"):
                    logging.info("Pausing program")
                    return True
                elif data.lower().startswith(b"Failed to execute:pause"):
                    logging.error("Failed to execute:pause")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def quit(self):
        """Quit the current connetion to the Dashboard Server."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"quit\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"Disconnected"):
                    logging.info("Disconnected")
                    return True
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def shutdown(self):
        """Shutdown the robot"""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"shutdown\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b'Shutting down\n'):
                    logging.info("Shutting down")
                    return True
                else:
                    logging.error("unexpected response: {}".format(data))
                    return False
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port: {e}}")
                self.connect()

    def running(self):
        """Check if a program is currently running."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"running\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"program running: true"):
                    logging.info("Program running")
                    return True
                elif data.lower().startswith(b"program running: false"):
                    logging.info("Program not running")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def robotmode(self):
        """Check the current robot mode."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"robotmode\n")
                    data = self.conn.recv(1024)
                    print(data)
                if data.lower().startswith(b"robotmode: no_controller"):
                    logging.info("Robot has no controller")
                    return "no_controller"
                elif data.lower().startswith(b"robotmode: disconnected"):
                    logging.info("Dashboard is disconnected")
                    return "disconnected"
                elif data.lower().startswith(b"robotmode: confirm_safety"):
                    logging.info("Robot is confirming safety")
                    return "confirm_safety"
                elif data.lower().startswith(b"robotmode: booting"):
                    logging.info("Robot is booting")
                    return "booting"
                elif data.lower().startswith(b"robotmode: power_off"):
                    logging.info("Robot is powered off")
                    return "power_off"
                elif data.lower().startswith(b"robotmode: power_on"):
                    logging.info("Robot is powered on")
                    return "power_on"
                elif data.lower().startswith(b"robotmode: idle"):
                    logging.info("Robot is idle")
                    return "idle"
                elif data.lower().startswith(b"robotmode: backdrive"):
                    logging.info("Robot is backdriving")
                    return "backdrive"
                elif data.lower().startswith(b"robotmode: running"):
                    logging.info("Robot is running")
                    return "running"
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def get_loaded_program(self):
        """Get the currently loaded program."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"get loaded program\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"loaded program:"):
                    logging.info("Loaded program: {}".format(data[16:].decode('utf-8').rstrip('\n')))
                    return data[16:].decode().rstrip('\n')
                elif data.lower().startswith(b"Failed to execute:get loaded program"):
                    logging.error("Failed to execute:get loaded program")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def popup(self, msg=""):
        """Display a popup on the robot teach pendant."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    if msg:
                        self.conn.send("popup {}\n".format(msg).encode('utf-8'))
                    else:
                        self.conn.send("popup .\n".encode('utf-8'))
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"showing popup"):
                    logging.info("Showing popup:" + msg)
                    return True
                elif data.lower().startswith(b"popup executed"):
                    logging.info("Popup executed")
                    return True
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def close_popup(self):
        """Close the popup on the robot teach pendant."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"close popup\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"closing popup"):
                    logging.info("Popup closed")
                    return True
                elif data.lower().startswith(b"popup closed"):
                    logging.info("Popup closed")
                    return True
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def add_to_log(self, msg):
        """Add a message to the robot log."""
        # validate msg exists
        if not msg:
            raise ValueError("No message to log provided")
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send("addToLog {}\n".format(msg).encode('utf-8'))
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"added log message"):
                    logging.info("Log added")
                    return True
                elif data.lower().startswith(b"no log message to add"):
                    logging.info("No log added")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def is_program_saved(self):
        """Check if the currently loaded program is saved."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"isProgramSaved\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"true"):
                    logging.info("Program saved")
                    return True
                elif data.lower().startswith(b"false"):
                    logging.info("Program not saved")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def program_state(self):
        """Check the current program state."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"programState\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"stopped"):
                    logging.info("Program stopped")
                    return "stopped"
                elif data.lower().startswith(b"playing"):
                    logging.info("Program playing")
                    return "playing"
                elif data.lower().startswith(b"no program running"):
                    logging.info("No program running")
                    return "no program running"
                elif data.lower().startswith(b"program running"):
                    logging.info("Program running")
                    return "program running"
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def polyscope_version(self):
        """Get the version of the installed polyscope software."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"polyscopeVersion\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"polyscope version"):
                    logging.info("Polyscope version: {}".format(data[19:].decode().rstrip('\n')))
                    return data[19:].decode().rstrip('\n')
                elif data.lower().startswith(b"failed to execute:polyscopeversion"):
                    logging.error("Failed to execute:polyscopeVersion")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def marketing_version(self):
        """Get the marketing version of the installed polyscope software."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"marketingVersion\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"marketing version"):
                    logging.info("Marketing version: {}".format(data[19:].decode().rstrip('\n')))
                    return data[19:].decode().rstrip('\n')
                elif data.lower().startswith(b"failed to execute:marketingversion"):
                    logging.error("Failed to execute:marketingVersion")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def set_operational_mode(self, mode='none'):
        """Set the operational mode of the robot."""
        # validate mode
        if mode not in ["manual", "automatic", "none"]:
            raise ValueError("Invalid mode provided")
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send("set operational mode {}\n".format(mode).encode('utf-8'))
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"setting operational mode"):
                    logging.info("Operational mode set to: {}".format(data[21:].decode().rstrip('\n')))
                    return True
                elif data.lower().startswith(b"failed setting operational mode"):
                    logging.error("Failed to set operational mode")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def get_operational_mode(self):
        """Get the operational mode of the robot."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"get operational mode\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"manual"):
                    logging.info("Operational mode: manual")
                    return "manual"
                elif data.lower().startswith(b"automatic"):
                    logging.info("Operational mode: automatic")
                    return "automatic"
                elif data.lower().startswith(b"none"):
                    logging.info("Operational mode: none")
                    return "none"
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def clear_operational_mode(self):
        """Clear the operational mode of the robot."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"clear operational mode\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"operational mode is no longer controlled by dashboard server"):
                    logging.info("Operational mode cleared")
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to clear operational mode")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def power_on(self):
        """Power on the robot."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"power on\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"powering on"):
                    logging.info("Robot powered on")
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to power on robot")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def power_off(self):
        """Power off the robot."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"power off\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"powering off"):
                    logging.info("Robot powered off")
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to power off robot")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def brake_release(self):
        """Release the robot brakes."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"brake release\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"brake releasing\n"):
                    logging.info("Brakes releasing")
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to release brakes")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def safety_status(self):
        """Get the safety status of the robot."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"safetystatus\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"safetystatus: normal"):
                    logging.info("Safety status: normal")
                    return "NORMAL"
                elif data.lower().startswith(b"safetystatus: reduced protective_stop"):
                    logging.warning("Safety status: reduced protective_stop")
                    return "REDUCED PROTECTIVE_STOP"
                elif data.lower().startswith(b"safetystatus: recovery safetyguard_stop"):
                    logging.warning("Safety status: recovery safetyguard_stop")
                    return "RECOVERY SAFETYGUARD_STOP"
                elif data.lower().startswith(b"safetystatus: recovery protective_stop"):
                    logging.warning("Safety status: recovery protective_stop")
                    return "RECOVERY PROTECTIVE_STOP"
                elif data.lower().startswith(b"safetystatus: system_emergency_stop"):
                    logging.warning("Safety status: system_emergency_stop")
                    return "SYSTEM_EMERGENCY_STOP"
                elif data.lower().startswith(b"safetystatus: robot_emergency_stop"):
                    logging.warning("Safety status: robot_emergency_stop")
                    return "ROBOT_EMERGENCY_STOP"
                elif data.lower().startswith(b"safetystatus: violation"):
                    logging.warning("Safety status: violation")
                    return "VIOLATION"
                elif data.lower().startswith(b"safetystatus: fault"):
                    logging.warning("Safety status: fault")
                    return "FAULT"
                elif data.lower().startswith(b"safetystatus: automatic_mode_safeguard_stop"):
                    logging.warning("Safety status: automatic_mode_safeguard_stop")
                    return "AUTOMATIC_MODE_SAFEGUARD_STOP"
                elif data.lower().startswith(b"safetystatus: system_three_position_enabling_stop"):
                    logging.warning("Safety status: system_three_position_enabling_stop")
                    return "SYSTEM_THREE_POSITION_ENABLING_STOP"
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to get safety status")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def unlock_protective_stop(self):
        """Unlock the protective stop."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"unlock protective stop\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"protective stop releasing"):
                    logging.info("Protective stop releasing")
                    return True
                elif data.lower().startswith(b"protective stop released"):
                    logging.info("Protective stop released")
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to unlock protective stop")
                    return False
                elif data.lower().startswith(b"cannot unlock protective stop until 5s after occurrence. always inspect cause of protective stop before unlocking"):
                    logging.error("Cannot unlock protective stop until 5s after occurrence. Always inspect cause of protective stop before unlocking")
                    return False
                elif data.lower().startswith(b"can not unlock protective stop"):
                    logging.error("Can not unlock protective stop")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def close_safety_popup(self):
        """Close the safety popup."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"close safety popup\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"closing safety popup"):
                    logging.info("Closing safety popup")
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to close safety popup")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def load_installation(self, installation):
        """Load an installation."""
        # validate installation exists
        if not installation:
            raise ValueError("Installation must be specified")
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(("load installation {}\n".format(installation)).encode('utf-8'))
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"loading installation"):
                    logging.info("Loading installation: {}".format(installation))
                    return True
                elif data.lower().startswith(b"failed to load installation:"):
                    logging.error("Failed to load installation")
                    return False
                elif data.lower().startswith(b"file not found"):
                    logging.error("Installation not found")
                    return False
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()
    
    def restart_safety(self):
        """Restart the safety."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"restart safety\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"true"):
                    logging.info("Restarting safety")
                    return True
                elif data.lower().startswith(b"false"):
                    logging.info("Could not restart safety")
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to restart safety")
                    return None
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return None
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def get_serial_number(self):    
        """Get the serial number of the robot."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"get serial number\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to get serial number")
                    return None
                else:
                    logging.info("Serial number: {}".format(data.decode('utf-8').rstrip('\n')))
                    return data.decode('utf-8').rstrip('\n')
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()  
    
    def get_robot_model(self):
        """Get the robot model."""
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(b"get robot model\n")
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to get robot model")
                    return None
                else:
                    logging.info("Robot model: {}".format(data.decode('utf-8').rstrip('\n')))
                    return data.decode('utf-8').rstrip('\n')
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    def generate_flight_report(self, type="robot"):
        """Generate a flight report."""
        # validate type
        if type not in ["controller", "robot", "system"]:
            raise ValueError("Report type must be 'controller' or 'robot'")
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(("generate flight report {}\n".format(type)).encode('utf-8'))
                    data = self.conn.recv(1024)
                if data.lower().startswith(b"flight report generated with id:"):
                    logging.info("Flight Report generated with id:{}".format(data.decode('utf-8').rstrip('\n').split(":")[1]))
                    return True
                elif data.lower().startswith(b"failed to execute:"):
                    logging.error("Failed to generate flight report")
                    return None
                else:
                    logging.error("Unexpected response: {}".format(data))
                    return False
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

    """def transfer_files_ssh(self, remote_path="/flightreports/", local_path="."):
        import paramiko
        # Transfer .zip files from remote to local.
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username='root', password='password')  # replace 'password' with the actual password
        
        sftp = ssh.open_sftp()
        files = sftp.listdir(remote_path)
        for file in files:
            if file.endswith('.zip'):
                sftp.get(os.path.join(remote_path, file), os.path.join(local_path, file))
        sftp.close()
        ssh.close()"""

    def transfer_files(self, remote_path="flightreports/", local_path="."):
        """Copy .zip flight reports (aka backup) from remote to local.
        calling out this function assumes that the user has already add the public key of the robot 
        to the local machine. If this is not the case, please use the above function, transfer_files_ssh."""
        try:
            os.mkdir("flightreports")
            t = threading.Thread(target=os.system, args=(f"scp root@{self.host}:{remote_path}/*.zip {local_path}/flightreports",))
            t.start()
            return "File transfer started..."
        except (FileExistsError, Exception) as e:
            logging.error(f"Error transferring files: {e}")
            return False

    def generate_support_file(self, path='/programs/'):
        """Generate a support file."""
        # validate path
        if not path:
            logging.info("Path not specified, using default path: /programs/")
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.conn:
                        self.connect()
                    self.conn.send(("generate support file {}\n".format(path)).encode('utf-8'))
                    data = self.conn.recv(1024)
                    print(data)
                if data.lower().startswith(b"completed successfully:"):
                    logging.info("Support file generated with id:{}".format(data.decode('utf-8').rstrip('\n').split(":")[1]))
                    return True
                elif data.lower().startswith(b"error: failed to create support report file  invalid target location"):
                    logging.error("{}".format(data.decode('utf-8').rstrip('\n')))
                    return None
                else:
                    logging.error("Unexpected response: {}".format(data.decode('utf-8').rstrip('\n')))
                    return False
            except (socket.error, Exception) as e:
                logging.error(f"Error communicating with {self.host}:{self.port}: {e}")
                self.connect()

if __name__ == '__main__':
    print("This is a library, not a script")
    exit(1)