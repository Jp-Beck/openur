__author__ = "Beck Isakov"
__copyright__ = "Beck isakov"
__credits__ = "Martin Huus Bjerge"
__contact__ = "https://github.com/Jp-Beck"
__license__ = "GPL v3"
__version__ = "0.2.4"
__maintainer__ = "Beck Isakov"
__email__ = "jp-beck@outlook.com"
__status__ = "Development"

import socket
import time
import logging
import threading
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class URController:
    def __init__(self, robot_ip, robot_port, pc_ip, pc_port):
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.pc_ip = pc_ip
        self.pc_port = pc_port

        self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_sock.connect((self.robot_ip, self.robot_port))

        self.response_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.response_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.response_sock.bind((self.pc_ip, self.pc_port))
        self.response_sock.listen(1)

    def _send_command(self, command):
        self.command_sock.sendall(command.encode('utf-8'))

    def _get_response(self):
        self.response_sock.settimeout(3)
        try:
            connection, _ = self.response_sock.accept()
            with connection:
                data = connection.recv(1024).decode('utf-8')
                return data.strip()
        except socket.timeout:
            logging.error("Timeout error: No response from robot")
            return None
        except Exception as e:  
            logging.error(f"Error: {e}")
            return None

    # ... rest of your methods ...
    def execute_command_and_get_response(self, user_command):
        script = (
            f"sec OpenUr():\n"
            f"  result = {user_command}()\n"
            f"  textmsg(\"{user_command}:\", result)\n"
            f"  socket_open(\"{self.pc_ip}\", {self.pc_port})\n"
            f"  socket_send_string(result)\n"
            f"  socket_close()\n"
            f"end\n"
        )
        self._send_command(script)
        return self._get_response()

    # Desired modular function
    @classmethod
    def desired_function(cls, command, pc_ip, pc_port, robot_ip, robot_port=30003):
        if not hasattr(cls, "_instance"):
            cls._instance = cls(robot_ip, robot_port, pc_ip, pc_port)
        return cls._instance.execute_command_and_get_response(command)

    def close(self):
        self.command_sock.close()
        self.response_sock.close()
        logging.info("Robot socket closed to PC at {} on port: {}".format(self.pc_ip, self.pc_port))

class URClient:

    def __init__(self, ip_address, port=30003, pc_ip = None, pc_port = None, max_retries=5):
        self.ip_address = ip_address
        self.port = port
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self._controller = None
        self.sock = None
        self.max_retries = max_retries
        self.exit_flag = threading.Event()
        self.lock = threading.Lock()
        self.connect()
    
    @property
    def controller(self):
        if not self._controller:
            self._controller = URController(self.ip_address, self.port, self.pc_ip, self.pc_port)
        return self._controller

    def desired_function(self, command, pc_ip, pc_port):
        # this uses lazy loaded URCOntroller instance
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        return self.controller.execute_command_and_get_response(command)

    @staticmethod
    def format_script(commands):
        program = "def OpenUr():\n"
        for command in commands:
            program += f"  {command}\n"
        program += "end\n"
        return program

    @staticmethod
    def format_program(commands):
        program = "def OpenUr():\n"
        indentation = 2
        for command in commands:
            if command == "end":
                indentation -= 2
            program += ' ' * indentation + command.lstrip() + "\n"
            if command.endswith(":") or command.lstrip().startswith("def "):
                indentation += 2
        program += "end\n"
        return program

    def connect(self):
        retries = 0
        while retries < self.max_retries and not self.exit_flag.is_set():
            try:
                with self.lock:
                    if self.sock:
                        self.sock.close()
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    self.sock.settimeout(1.0)
                    self.sock.connect((self.ip_address, self.port))
                    logging.info(f"URClient connected to robot: {self.ip_address}:{self.port}")
                break
            except Exception as e:
                logging.error(f"URClient connection error: {e}")
                retries += 1
                time.sleep(min(retries * 2, 30)) # Exponential backoff with a maximum wait time of 30s.
                
        if retries == self.max_retries:
            logging.error("URClient failed to connect after maximum retries.")

    def send_script(self, script):
        if not self.sock:
            logging.error("URClient socket is not connected.")
            return
        try:
            with self.lock:
                self.sock.sendall(script.encode('utf-8'))
        except socket.error as e:
            logging.error(f"URClient failed to send script: {e}")
            self.connect() # Try to reconnect if sending fails

    def close(self):
        with self.lock:
            if self.sock:
                self.sock.close()
                self.sock = None
            if self._controller:
                self._controller.close()
                self._controller = None
            logging.info(f"URClient disconnected from robot: {self.ip_address}:{self.port}")


    def stop_script_connection(self):
        '''Stop the script connection and close the socket'''
        self.exit_flag.set()
        self.close()
    
    def __del__(self):
        if hasattr(self, 'sock') and self.sock:
            self.stop_script_connection()

    def send_script(self, program):
        '''Send a URScript program as a list of strings, preferably the single lines'''
        if not self.sock:
            raise ConnectionError("URClient not connected to robot")
        program_string = self.format_script(program)
        self.sock.send(program_string.encode())

    def send_raw_program(self, program):
        '''Send a URScript program as a list of strings'''
        if not self.sock:
            raise ConnectionError("URClient not connected to robot")
        program_string = self.format_program(program)
        self.sock.send(program_string.encode())
    
    def send_txt_program(self, filename):
        '''Send a URScript program from a text file'''
        if not self.sock:
            raise ConnectionError("Not connected to robot")
        with open(filename, 'r') as file:
            program = file.read()
        program_string = self.format_program(program.split('\n'))
        self.sock.send(program_string.encode())
        time.sleep(0.1)
    

    # Module Internals URScript commands:
    def force_mode(self, task_frame=[], selection_vector=[], wrench=[], f_type=2, limits=[]):
        '''Parameters:
            task_frame: A pose vector that defines the force frame relative to the base frame.
            selection_vector: A 6d vector of 0s and 1s. 1 means that the robot will be compliant in the
            corresponding axis of the task frame.
            wrench: The forces/torques the robot will apply to its environment. The robot adjusts its position
            along/about compliant axis in order to achieve the specified force/torque. Values have no effect
            for non-compliant axes.'''
        
        # Validate task_frame
        if not (
            isinstance(task_frame, list)
            and len(task_frame) == 6
            and all(isinstance(p, (int, float)) for p in task_frame)
        ):
            raise ValueError("task_frame must be a list of 6 integers or floats")
        
        # Validate selection_vector
        if not (
            isinstance(selection_vector, list)
            and len(selection_vector) == 6
            and all(isinstance(s, int) for s in selection_vector)
            and all(s in [0, 1] for s in selection_vector)
        ):
            raise ValueError("selection_vector must be a list of 6 integers either 0 or 1")
        
        # Validate wrench
        if not (
            isinstance(wrench, list)
            and len(wrench) == 6
            and all(isinstance(w, (int, float)) for w in wrench)
        ):
            raise ValueError("wrench must be a list of 6 integers or floats")
        
        # Validate f_type
        if not (
            isinstance(f_type, int)
            and f_type in [1, 2]
        ):
            raise ValueError("f_type must be either 1 or 2")
        
        # Validate limits
        if not (
            isinstance(limits, list)
            and len(limits) == 6
            and all(isinstance(l, (int, float)) for l in limits)
        ):
            raise ValueError("limits must be a list of 6 integers or floats")
        
        # Create and send the command
        task_frame_str = ",".join(map(str, task_frame))
        selection_vector_str = ",".join(map(str, selection_vector))
        wrench_str = ",".join(map(str, wrench))
        limits_str = ",".join(map(str, limits))
        command = f"force_mode(p[{task_frame_str}], [{selection_vector_str}], [{wrench_str}], {f_type}, [{limits_str}])"
        self.send_script([command])
    
    def end_force_mode(self):
        command = f"end_force_mode()"
        self.send_script([command])




    # Frequentlsy used URScript commands
    def stop_command(self):
        self.send_script(stop_command)

    def set_digital_out(self, pin, value:bool):
        if value in [True, False]:
            command = f"set_digital_out({pin}, {value})"
            self.send_script([command])
        else:
            raise ValueError('Value shall be either True or False')

    def movej(self, joints, a=1.4, v=1.05, t=0, r=0):
        if not (
            isinstance(joints, list)
            and len(joints) == 6
            and all(isinstance(j, (int, float)) for j in joints)
        ):
            raise ValueError("joints must be a list of 6 integers or floats")
        
        command = f"movej({joints}, a={a}, v={v}, t={t}, r={r})"
        self.send_script([command])
    
    def movel(self, pose, a=1.2, v=0.25, t=0, r=0):
        if not (
            isinstance(pose, list)
            and len(pose) == 6
            and all(isinstance(p, (int, float)) for p in pose)
        ):
            raise ValueError("pose must be a list of 6 integers or floats")
        command = f"movel({pose}, a={a}, v={v}, t={t}, r={r})"
        self.send_script([command])
    
    def movep(self, pose, a=1.2, v=0.25, t=0, r=0):
        command = f"movep({pose}, a={a}, v={v}, t={t}, r={r})"
        self.send_script([command])
    
    def movec(self, pose_via, pose_to, a=1.2, v=0.25, r=0):
        command = f"movec({pose_via}, {pose_to}, a={a}, v={v}, r={r})"
        self.send_script([command])
    
    def stopj(self, a=1):
        command = f"stopj({a})"
        self.send_script([command])
    
    def stopl(self, a=1):
        command = f"stopl({a})"
        self.send_script([command])
    
    def sleep(self, t):
        command = f"sleep({t})"
        self.send_script([command])
    
    def set_tcp(self, pose):
        command = f"set_tcp(p{pose})"
        self.send_script([command])
    
    def end_freedrive_mode(self):
        command = f"end_freedrive_mode()"
        self.send_script([command])
    
    def end_screw_driving(self):
        command = f"end_screw_driving()"
        self.send_script([command])
    
    def end_teach_mode(self):
        command = f"end_teach_mode"
        self.send_script([command])
    
    def force_mode_set_damping(self, damping):
        if 0 <= damping <= 1:
            command = f"force_mode_set_damping({damping})"
            self.send_script([command])
        else:
            raise ValueError('Damping value should be between 0 and 1 inclusive.')
    
    def force_mode_set_gain_scaling(self, scaling=1):
        if 0 <= scaling <= 2:
            command = f"force_mode_set_gain_scaling({scaling})"
            self.send_script([command])
        else:
            raise ValueError('Scaling value should be between 1 and 2 inclusive')
    
    def freedrive_mode(self, freeAxes=[1, 1, 1, 1, 1, 1], feature=[0, 0, 0, 0, 0, 0]):
        '''Set the robot in freedrive mode. The robot can be moved by hand.
        
        Args:
            freeAxes (list): A list of 6 integers either 0 or 1. 0 means that the axis is locked and 1 means that the axis is free.
            feature (list): A list of 6 integers or floats. The feature vector is used to set the speed of the robot in the corresponding direction.
        '''
        # validate which axes to set free
        if not (
            isinstance(freeAxes, list)
            and len(freeAxes) == 6
            and all(isinstance(ax, int) for ax in freeAxes)
            and all(ax in [0, 1] for ax in freeAxes)
        ):
            raise ValueError("freeAxes must be a list of 6 integers either 0 or 1.")

        # validate feature
        if not (
            isinstance(feature, list)
            and len(feature) == 6
            and all(isinstance(feat, (int, float)) for feat in feature)
        ):
            raise ValueError("Feature must be a list of 6 integers or floats")
        
        # Create and send the command
        freeAxes_str = ",".join(map(str, freeAxes))
        feature_str = ",".join(map(str,feature))
        command = f"freedrive_mode([{freeAxes_str}], p[{feature_str}])"
        print(command)
        self.send_script(command)

                    


commands = [
    "set_digital_out(0, True)",
    "initial_pose = get_actual_tcp_pose()",
    "while (True):",
        "def random_distance(lower_bound, upper_bound):",
            "return lower_bound + (upper_bound - lower_bound)*random()",
        "end",


        "def random_movement(x_bounds=[], y_bounds=[], z_bounds=[], rx_bounds=[], ry_bounds=[], rz_bounds=[]):",
            "pose_offset = p[0, 0, 0, 0, 0, 0]",

        "if (x_bounds != []):",
                "pose_offset[0] = random_distance(x_bounds[0], x_bounds[1])",
            "end",

            "if (y_bounds != []):",
                "pose_offset[1] = random_distance(y_bounds[0], y_bounds[1])",
            "end",

        "if (z_bounds != []):",
                "pose_offset[2] = random_distance(z_bounds[0], z_bounds[1])",
            "end",

            "if (rx_bounds != []):",
                "rx_bounds_rad = [rx_bounds[0]*3.14159/180, rx_bounds[1]*3.14159/180]",
                "pose_offset[3] = random_distance(rx_bounds_rad[0], rx_bounds_rad[1])",
            "end",

            "if (ry_bounds != []):",
                "ry_bounds_rad = [ry_bounds[0]*3.14159/180, ry_bounds[1]*3.14159/180]",
                "pose_offset[4] = random_distance(ry_bounds_rad[0], ry_bounds_rad[1])",
            "end",

            "if (rz_bounds != []):",
                "rz_bounds_rad = [rz_bounds[0]*3.14159/180, rz_bounds[1]*3.14159/180]",
                "pose_offset[5] = random_distance(rz_bounds_rad[0], rz_bounds_rad[1])",
            "end",

            "target_pose = pose_add(initial_pose, pose_offset)",


            "movel(target_pose, a=1.0, v=0.1)",
        "end",

        "random_movement(x_bounds=[0,0.05])",
    "end",
]

stop_command = [
    "sleep(1)",
]

