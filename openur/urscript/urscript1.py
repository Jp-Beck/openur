__author__ = "Beck Isakov"
__copyright__ = "Beck isakov"
__credits__ = "Martin Huus Bjerge"
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

class URClient:

    def __init__(self, ip_address, port=30003):
        self.ip_address = ip_address
        self.port = port
        self.sock = None
        self.exit_flag = threading.Event()
        self.lock = threading.Lock()
    
    @staticmethod
    def format_script(commands):
        '''Format a list of strings into a URScript program, preferably the single lines'''
        program = "def OpenUr():\n"
        for command in commands:
            program += f"  {command}\n"
        program += "end\n"
        print(program)
        return program
    
    @staticmethod
    def format_program(commands):
        '''Format a list of strings into a URScript program, preferably from the file'''
        program = "def OpenUr():\n"
        indentation = 2
        for command in commands:
            if command == "end":
                indentation -= 2
            program += ' ' * indentation + command.lstrip() + "\n"
            if command.endswith(":") or command.lstrip().startswith("def "):
                indentation += 2
        program += "end\n"
        print(program)
        return program

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(1.0)
            self.sock.connect((self.ip_address, self.port))
            logging.info("URClient to robot: {0}:{1}".format(self.ip_address, self.port))
        except Exception as e:
            logging.error("URClient: {0}".format(e))
            self.sock = None

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        logging.info("URClient disconnected from robot: {0}:{1}".format(self.ip_address, self.port))

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






    # Frequentlsy used URScript commands
    def stop_command(self):
        self.send_script(stop_command)

    def set_digital_out(self, pin, value):
        command = f"set_digital_out({pin}, {value})"
        self.send_script([command])

    def movej(self, joints, a=1.4, v=1.05, t=0, r=0):
        command = f"movej({joints}, a={a}, v={v}, t={t}, r={r})"
        self.send_script([command])
    
    def movel(self, pose, a=1.2, v=0.25, t=0, r=0):
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
    
    def get_actual_joint_positions(self):
        command = f"get_actual_joint_positions()"
        self.send_raw_program([command])

    # Module Internals URScript commands:
    def force_mode(self, task_frame=[], selection_vector=[], wrench=[], f_type=2, limits=[]):
        command = f"while True:,force_mode(p{task_frame}, {selection_vector}, {wrench}, {f_type}, {limits}),sync()"
        while not self.exit_flag.is_set():
            try:
                with self.lock:
                    if not self.sock:
                        logging.warning("URClient is not connected to robot. Attempting to reconnect...")
                        self.connect()
                    self.send_raw_program([command])
                    data = self.sock.recv(1024)
                    return data
            except Exception as e:
                logging.error("URClient: {0}".format(e))
                self.close()
    
    def end_force_mode(self):
        command = f"end_force_mode()"
        self.send_script([command])
    
                    


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


