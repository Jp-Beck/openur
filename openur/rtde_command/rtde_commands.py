__author__ = "Beck Isakov"
__copyright__ = "Beck isakov"
__contact__ = "https://github.com/Jp-Beck"
__license__ = "GPL v3"
__version__ = "0.2.0"
__maintainer__ = "Beck Isakov"
__email__ = "jp-beck@outlook.com"
__status__ = "Development"



from typing import Dict, List, Optional, Union
import logging, argparse, time, sys, time, logging, threading, functools
from contextlib import ExitStack




from openur.rtde import rtde
from openur.rtde import rtde_config



if sys.version_info[0] < 3:
    import xmlrpclib
    from SimpleXMLRPCServer import SimpleXMLRPCServer
else:
    from xmlrpc import client as xmlrpclib
    from xmlrpc.server import SimpleXMLRPCServer


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def retry(exceptions, tries=4, delay=3, backoff=2, logger=None):
    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            with ExitStack() as stack:
                while mtries > 1:
                    try:
                        return f(*args, **kwargs)
                    except exceptions as e:
                        msg = f"{str(e)}, Retrying in {mdelay} seconds..."
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                        stack.enter_context(e)
                return f(*args, **kwargs)
        return f_retry
    return deco_retry


         
class RTDECommands: 
    """Class for controlling the robot using the RTDE interface."""
    stop_running_flag: bool = False

    def __init__(self, host, recipe_setp='rci', recipe_out='rco', config_path='rtde_configuration.xml', max_retries=3):    

        self.ROBOT_HOST = host
        self.ROBOT_PORT = 30004
        self.recipe_setp = recipe_setp
        self.recipe_out = recipe_out

        self.Keep_running = True
        self.max_retries = max_retries
        self.exit_flag = threading.Event()
        self.lock = threading.Lock()
        self.con = None

        self.conf = rtde_config.ConfigFile(config_path)
        self.setp_names, self.setp_types = self.conf.get_recipe(recipe_setp)
        self.output_names, self.output_types = self.conf.get_recipe(recipe_out)  

        self.data_dir: Dict[str, Optional[Union[int, float, str]]] = {
            'timestamp': None,
            'target_q': None,
            'target_qd': None,
            'target_qdd': None,
            'target_current': None,
            'target_moment': None,
            'actual_q': None,
            'actual_qd': None,
            'actual_current': None,
            'joint_control_output': None,
            'actual_TCP_pose': None,
            'actual_TCP_speed': None,
            'actual_TCP_force': None,
            'target_TCP_pose': None,
            'target_TCP_speed': None,
            'actual_digital_input_bits': None,
            'joint_temperatures': None,
            'actual_execution_time': None,
            'robot_mode': None,
            'joint_mode': None,
            'safety_mode': None,
            'safety_status': None,
            'safety_status_bits': None,
            'actual_tool_accelerometer': None,
            'speed_scaling': None,
            'target_speed_fraction': None,
            'actual_momentum': None,
            'actual_main_voltage': None,
            'actual_robot_voltage': None, # expected type: DOUBLE
            'actual_robot_current': None, # expected type: DOUBLE
            'actual_joint_voltage': None, # expected type: VECTOR6D
            'actual_digital_output_bits': None, # expected type: UINT64
            'runtime_state': None, # expected type: UINT32
            'elbow_position': None, # expected type: VECTOR3D
            'elbow_velocity': None, # expected type: VECTOR3D
            'ROBOT_MESSAGE': None, # expected type: STRING
            'robot_status_bits': None, # expected type: UINT32
            'analog_io_types': None, # expected type: UINT32    
            'standard_analog_input0': None, # expected type: DOUBLE
            'standard_analog_input1': None, # expected type: DOUBLE
            'standard_analog_output0': None, # expected type: DOUBLE
            'standard_analog_output1': None, # expected type: DOUBLE
            'io_current': None, # expected type: DOUBLE
            'euromap67_input_bits': None, # expected type: UINT32
            'euromap67_output_bits': None, # expected type: UINT32
            'euromap67_24V_voltage': None, # expected type: DOUBLE
            'euromap67_24V_current': None, # expected type: DOUBLE
            'tool_mode': None, # expected type: UINT32
            'tool_analog_input_types': None, # expected type: UINT32
            'tool_analog_input0': None, # expected type: DOUBLE
            'tool_analog_input1': None, # expected type: DOUBLE
            'tool_output_voltage': None, # expected type: UINT32
            'tool_output_current': None, # expected type: DOUBLE
            'tool_temperature': None, # expected type: DOUBLE
            'tcp_force_scalar': None, # expected type: DOUBLE
            'output_bit_registers0_to_31': None, # expected type: UINT32
            'output_bit_registers32_to_63': None, # expected type: UINT32
            'output_int_register_0': None, # expected type: INT32
            'output_int_register_1': None, # expected type: INT32
            'output_int_register_2': None, # expected type: INT32
            'output_int_register_3': None, # expected type: INT32
            'output_int_register_4': None, # expected type: INT32
            'output_int_register_5': None, # expected type: INT32
            'output_int_register_6': None, # expected type: INT32
            'output_int_register_7': None, # expected type: INT32
            'output_int_register_8': None, # expected type: INT32
            'output_int_register_9': None, # expected type: INT32
            'output_int_register_10': None, # expected type: INT32
            'output_int_register_11': None, # expected type: INT32
            'output_int_register_12': None, # expected type: INT32
            'output_int_register_13': None, # expected type: INT32
            'output_int_register_14': None, # expected type: INT32
            'output_int_register_15': None, # expected type: INT32
            'output_int_register_16': None, # expected type: INT32
            'output_int_register_17': None, # expected type: INT32
            'output_int_register_18': None, # expected type: INT32
            'output_int_register_19': None, # expected type: INT32
            'output_int_register_20': None, # expected type: INT32
            'output_int_register_21': None, # expected type: INT32
            'output_int_register_22': None, # expected type: INT32
            'output_int_register_23': None, # expected type: INT32
            'output_int_register_24': None, # expected type: INT32
            'output_bit_register_88': None, # expected type: BOOL (X = [64,127])
            'output_double_register_X': None, # expected type: DOUBLE (X = [0,47])
            'output_double_register_0': None, # expected type: DOUBLE
            'output_double_register_1': None, # expected type: DOUBLE
            'output_double_register_2': None, # expected type: DOUBLE
            'output_double_register_3': None, # expected type: DOUBLE
            'output_double_register_4': None, # expected type: DOUBLE
            'output_double_register_5': None, # expected type: DOUBLE
            'output_double_register_6': None, # expected type: DOUBLE
            'output_double_register_7': None, # expected type: DOUBLE
            'output_double_register_8': None, # expected type: DOUBLE
            'output_double_register_9': None, # expected type: DOUBLE
            'output_double_register_10': None, # expected type: DOUBLE
            'output_double_register_11': None, # expected type: DOUBLE
            'output_double_register_12': None, # expected type: DOUBLE
            'output_double_register_13': None, # expected type: DOUBLE
            'output_double_register_14': None, # expected type: DOUBLE
            'output_double_register_15': None, # expected type: DOUBLE
            'output_double_register_16': None, # expected type: DOUBLE
            'output_double_register_17': None, # expected type: DOUBLE
            'output_double_register_18': None, # expected type: DOUBLE
            'output_double_register_19': None, # expected type: DOUBLE
            'output_double_register_20': None, # expected type: DOUBLE
            'output_double_register_21': None, # expected type: DOUBLE
            'output_double_register_22': None, # expected type: DOUBLE
            'output_double_register_23': None, # expected type: DOUBLE
            'input_bit_registers0_to_31': None, # expected type: UINT32
            'input_bit_registers32_to_63': None, # expected type: UINT32
            'input_bit_register_X': None, # expected type: BOOL (X = [64,127])
            'input_int_register_X': None, # expected type: INT32 (X = [0,47])
            'input_double_register_X': None, # expected type: DOUBLE (X = [0,48])
            'tool_output_mode': None, # expected type: UINT8
            'tool_digital_output0_mode': None, # expected type: UINT8
            'tool_digital_output1_mode': None, # expected type: UINT8
            'payload': None, # expected type: DOUBLE
            'payload_cog': None, # expected type: VECTOR3D
            'payload_inertia': None, # expected type: vector6d
            'script_control_line': None, # expected type: uint32
            'ft_raw_wrench': None, # expected type: vector6d
            'urPLus_force_torque_sensor': None, # expected type: vector6d
        }
        
        self.rtc_connection_state: Optional[str] = None
        self.rtc_program_running: bool = False
        self.rtc_program_execution_error: bool = False
        self.stop_running_flag: bool = False
        self.force_remote_active_flag: bool = False 
        self.has_force_torque_sensor: bool = False
        self.force_torque: Optional[Union[int, float]] = None
        self.force_torque_sensor_values: Optional[Union[int, float]] = None  


    @retry((Exception), tries=4, delay=3, backoff=2, logger=logging)
    def connect(self):
        retries = 0
        while not self.exit_flag.is_set() and retries < self.max_retries:
            try:
                with self.lock:
                    if self.con:
                        self.con.disconnect()
                    self.con = rtde.RTDE(self.ROBOT_HOST, self.ROBOT_PORT)
                    self.con.connect()
                    self.con.get_controller_version()

                    if not self.con.send_output_setup(self.output_names, self.output_types, frequency=125):
                        logging.error("Unable to configure output")
                        raise Exception("Unable to configure output")

                    self.setp = self.con.send_input_setup(self.setp_names, self.setp_types)
                    
                    if not self.con.send_start():
                        logging.error("Unable to start the data synchronization")
                        raise Exception("Unable to start the data synchronization")
                logging.info('RTDE Connection Established with {}:{}'.format(self.ROBOT_HOST, self.ROBOT_PORT))
                break 
            except (Exception) as e:
                logging.error(f"Error connecting to {self.ROBOT_HOST}:{self.ROBOT_PORT}: {e}")
                retries += 1
                time.sleep(5 ** retries)
    
    def close(self):
        try:
            if self.con:
                self.con.disconnect()
                logging.info('RTDE Connection Closed with {}:{}'.format(self.ROBOT_HOST, self.ROBOT_PORT))
        except (Exception) as e:
            logging.error(f"Error closing connection to {self.ROBOT_HOST}:{self.ROBOT_PORT}: {e}")

    def stop_rtde_connection(self):
        """Stop any ongoing connection attempts or operations."""
        self.exit_flag.set()
        self.close()
    
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
        
    def __del__(self): 
        if self.con is not None:
            self.con.disconnect()

    def receive_buffered(self,data_type):
        self.con.receive_buffered(data_type)

    def receive(self,data_type):
        self.con.receive(data_type)
    
    def setp_input(self, data):
        self.setp.send(data)
        self.con.send(self.setp)
        time.sleep(0.1)

    def set_control_inputs(self, **kwargs):
        """Sets control inputs for the robot.
        Each keyword argument is treated as an input control variable. The method checks whether the input variable 
        is a valid control input (i.e., exists in the setp object), and if so, it updates the control input with the provided value.

        Example:
        >>> set_control_inputs(target_joint_positions=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0], target_velocity=1.0)

        Args:
            kwargs (dict): keyword arguments where each key is the name of a control input and each value is the desired value for that control input.
        """
        # Check that the connection exists
        if not self.con:
            logging.error("No connection to the robot. Please connect first.")
            return

        # Lock the thread while updating setp
        with self.lock:
            # Iterate over the keyword arguments
            for key, value in kwargs.items():
                # Check if the key exists in the setp dictionary (i.e., it is a valid control input)
                if key in self.setp.__dict__:
                    # Check if the value is of correct type (optional)
                    if isinstance(value, type(self.setp.__dict__[key])):
                        # Set the control input to the provided value
                        self.setp.__dict__[key] = value
                    else:
                        logging.error(f"Incorrect type for control input {key}. Expected {type(self.setp.__dict__[key])} but got {type(value)}.")
                else:
                    # If the key does not exist in the setp dictionary, raise a warning
                    logging.error(f"Invalid control input key: {key}. Ignoring this input.")

            # After all the setp variables have been updated, send the new setp to the robot
            success = self.con.send(self.setp)

            if not success:
                logging.error("Failed to send control inputs to the robot.")

            return success
    
        
    def control_loop(self):
        while self.Keep_running:
            try:
                
                data = self.con.receive()
                if data is not None:
                    print(data.actual_q())
                    time.sleep(1)  # changed to 0.5 to increase the responsiveness
                    self.manipulate(self.con, self.setp)
            except rtde.RTDEException as e:
                logging.error(f"RTDE error occurred: {e}")
                # reconnect
                print("Reconnecting.............................................................................")
                self.connect()
            except KeyboardInterrupt:
                logging.info("Interrupted by keyword.")
                self.Keep_running = False
                sys.exit(0)
            except xmlrpclib.Fault as e:
                logging.error(f"XML-RPC fault occurred: {e}")
                time.sleep(0.5)  # changed to 0.5 to reduce wait time before retry
            except Exception as e:
                logging.error(f"Unexpected error occurred with data {data}: {e}")
                time.sleep(0.5)  # changed to 0.5 to reduce wait time before retry

   

        if self.con is None:
            self.connect()
        

        
    # All other methods

    def __getitem__(self, key: str) -> Union[int, float, bool, str, None]:
        return self.data_dir[key]
    
    def __setitem__(self, key: str, value: Union[int, float, bool, str, None]) -> None:
        self.data_dir[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.data_dir
    
    def runtime_state(self) -> str:
        return self.rtc_program_running
    
    def rtc_connection_stat(self) -> str:
        return self.rtc_connection_state
    
    def stop_running_flag(self) -> bool:
        return self.stop_running_flag

    def fetch_data(self, key: str, index: Optional[int] = None):
        try:
            data = self.con.receive()
            if data is not None:
                if index is not None:
                    self.data_dir[f'{key}{index}'] = getattr(data, f'{key}{index}')
                    return self.data_dir[f'{key}{index}']
                else:
                    self.data_dir[key] = getattr(data, key)
                    return self.data_dir[key]
        except Exception as e:
            logging.error(f"Could not get {key}: {e}")
            return None

                                                                    ### RTDE specific methods

    # Robot Controller Outputs
    def timestamp(self):
        return self.fetch_data('timestamp')
    
    def target_q(self) -> Optional[List[float]]:
        return self.fetch_data('target_q')
    
    def target_qd(self) -> Optional[List[float]]:
        return self.fetch_data('target_qd')
    
    def target_qdd(self) -> Optional[List[float]]:
        return self.fetch_data('target_qdd')
    
    def target_current(self) -> Optional[List[float]]:
        return self.fetch_data('target_current')
    
    def target_moment(self) -> Optional[List[float]]:
        return self.fetch_data('target_moment')
    
    def actual_q(self) -> Optional[List[float]]:
        return self.fetch_data('actual_q')
    
    def actual_qd(self) -> Optional[List[float]]:
        return self.fetch_data('actual_qd')
    
    def actual_current(self) -> Optional[List[float]]:
        return self.fetch_data('actual_current')
    
    def joint_control_output(self) -> Optional[List[float]]:
        return self.fetch_data('joint_control_output')
    
    def actual_TCP_pose(self) -> Optional[List[float]]:
        return self.fetch_data('actual_TCP_pose')
    
    def actual_TCP_speed(self) -> Optional[List[float]]:
        return self.fetch_data('actual_TCP_speed')
    
    def actual_TCP_force(self) -> Optional[List[float]]:    
        return self.fetch_data('actual_TCP_force')
    
    def target_TCP_pose(self) -> Optional[List[float]]:
        return self.fetch_data('target_TCP_pose')
    
    def target_TCP_speed(self) -> Optional[List[float]]:    
       return self.fetch_data('target_TCP_speed')
    
    def actual_digital_input_bits(self) -> Optional[int]: # TODO: Check if this is correct
        return self.fetch_data('actual_digital_input_bits')
    
    def joint_temperatures(self) -> Optional[List[float]]:
        return self.fetch_data('joint_temperatures')
    
    def actual_execution_time(self) -> Optional[float]:
        return self.fetch_data('actual_execution_time')
    
    def robot_mode(self) -> Optional[int]:
        return self.fetch_data('robot_mode')
    
    def joint_mode(self) -> Optional[List[int]]:
        return self.fetch_data('joint_mode')
    
    def safety_mode(self) -> Optional[int]:
        return self.fetch_data('safety_mode')
    
    def safety_status(self) -> Optional[List[int]]:
        return self.fetch_data('safety_status')
    
    def actual_tool_accelerometer(self) -> Optional[List[float]]:
        return self.fetch_data('actual_tool_accelerometer')
    
    def speed_scaling(self) -> Optional[float]:
        return self.fetch_data('speed_scaling')
    
    def target_speed_fraction(self) -> Optional[float]: # PolyScope Speed
        return self.fetch_data('target_speed_fraction')
    
    def actual_momentum(self) -> Optional[List[float]]:
        return self.fetch_data('actual_momentum')
    
    def actual_main_voltage(self) -> Optional[float]:
        return self.fetch_data('actual_main_voltage')
    
    def actual_robot_voltage(self) -> Optional[float]:
        return self.fetch_data('actual_robot_voltage')
    
    def actual_robot_current(self) -> Optional[float]:
        return self.fetch_data('actual_robot_current')
    
    def actual_joint_voltage(self) -> Optional[List[float]]:
        return self.fetch_data('actual_joint_voltage')
    
    def runtime_state(self) -> Optional[int]:
        return self.fetch_data('runtime_state')
    
    def elbow_position(self) -> Optional[List[float]]:
        return self.fetch_data('elbow_position')
    
    def elbow_velocity(self) -> Optional[List[float]]:
        return self.fetch_data('elbow_velocity')
    

    def safety_status_bits(self) -> Optional[bool]:
        '''
        SafetyStatusBit class defined in the bottom of this file
        '''
        # Method 1
        result = SafetyStatusBit()
        safety_status_names = [
        "normal_mode", "reduced_mode", "protective_stopped", "recovery_mode",
        "safeguard_stopped", "system_emmergency_stopped", "robot_emergency_stopped",
        "emergency_stopped", "violation", "fault", "stopped_due_to_safety"
        ]
        try:
            data = self.con.receive()

            self.data_dir['safety_status_bits'] = data.safety_status_bits
            safety_status_bits = self.data_dir.get('safety_status_bits', 0)

            for i, name in enumerate(safety_status_names):
                if hasattr(result, name):
                    setattr(result, name, bool(2**i & safety_status_bits))
            # Adjust what you want to return
            return result
            return self.data_dir['safety_status_bits']
            return result.get_true_bits()
        except Exception as e:
            logging.error("Could not get safety_status_bits: {}".format(e))
            return None
        
        # Method 2
        """result = SafetyStatusBit()
        data = self.con.receive()
        self.data_dir['safety_status_bits'] = data.safety_status_bits
        safety_status_bits = self.data_dir.get('safety_status_bits', 0)
        result.normal_mode               = (safety_status_bits & 1) != 0
        result.reduced_mode              = (safety_status_bits & 2) != 0
        result.protective_stopped        = (safety_status_bits & 4) != 0
        result.recovery_mode             = (safety_status_bits & 8) != 0
        result.safeguard_stopped         = (safety_status_bits & 16) != 0
        result.system_emergency_stopped  = (safety_status_bits & 32) != 0
        result.robot_emergency_stopped   = (safety_status_bits & 64) != 0
        result.emergency_stopped         = (safety_status_bits & 128) != 0
        result.violation                 = (safety_status_bits & 256) != 0
        result.fault                     = (safety_status_bits & 512) != 0
        result.stopped_due_to_safety     = (safety_status_bits & 1024) != 0
        return result"""




    def robot_status_bits(self) -> Optional[int]:
        '''
        SafetyStatusBit class defined in the bottom of this file
        '''
        result = RobotStatusBit()
        safety_status_names = ["power_on", "program_running", "teach_button_pressed", "power_button_pressed"]
        safety_status_bits = self.data_dir['robot_status_bits']
        
        try:
            data = self.con.receive()

            self.data_dir['robot_status_bits'] = data.robot_status_bits
            safety_status_bits = self.data_dir.get('robot_status_bits', 0)

            for i, name in enumerate(safety_status_names):
                if hasattr(result, name):
                    setattr(result, name, bool(2**i & safety_status_bits))

            return result
        except Exception as e:
            logging.error("Could not get robot_status_bits: {}".format(e))
            return None
    
    def analog_io_types(self) -> Optional[List[int]]:
        return self.fetch_data('analog_io_types')
    
    def standard_analog_input(self, n: int) -> Union[int, float, None]:
        if n in [0, 1]:
            return self.fetch_data(f'standard_analog_input{n}')
        else:
            raise KeyError('Index out of range')
    
    def io_current(self) -> Optional[List[float]]:
        return self.fetch_data('io_current')
    
    def euromap67_input_bits(self) -> Optional[int]:
        return self.fetch_data('euromap67_input_bits')
    
    def euromap67_output_bits(self) -> Optional[int]:
        return self.fetch_data('euromap67_output_bits')
    
    def euromap67_24V_voltage(self) -> Optional[float]:
        return self.fetch_data('euromap67_24V_voltage')
    
    def euromap67_24V_current(self) -> Optional[float]:
        return self.fetch_data('euromap67_24V_current')
    
    def tool_mode(self) -> Optional[int]:
        return self.fetch_data('tool_mode')
    
    def tool_analog_input_types(self) -> Optional[List[int]]:
        return self.fetch_data('tool_analog_input_types')

    def tool_analog_input(self, n: int) -> Union[int, float]:
        if n in [0, 1]:
            return self.fetch_data(f'tool_analog_input{n}')
        else:
            raise KeyError('Index out of range')
    
    def tool_output_voltage(self) -> Optional[float]:
        return self.fetch_data('tool_output_voltage')
    
    def tool_output_current(self) -> Optional[float]:
        # it returns the current in mA
        return self.fetch_data('tool_output_current')*1000
    
    def tool_temperature(self) -> Optional[float]:
        return self.fetch_data('tool_temperature')
    
    def tcp_force_scalar(self) -> Optional[float]:
        return self.fetch_data('tcp_force_scalar')
    
    def output_bit_registers(self) -> Optional[bool]: # TODO: check this
        data = self.con.receive()
        self.data_dir['output_bit_registers0_to_31'] = data.output_bit_registers0_to_31
        self.data_dir['output_bit_registers32_to_63'] = data.output_bit_registers32_to_63
        result = [None]*64
        for ii in range(64):
            if ii<32 and self.data_dir['output_bit_registers0_to_31'] is not None:
                result[ii] = 2**(ii)&self.data_dir['output_bit_registers0_to_31']==2**(ii)
            elif ii>31 and self.data_dir['output_bit_registers32_to_63'] is not None:
                result[ii] = 2**(ii-32)&self.data_dir['output_bit_registers32_to_63']==2**(ii-32)
        return result
    
    def output_bit_registers0_to_31(self) -> Optional[bool]:
        try:
            data = self.con.receive()
            self.data_dir['output_bit_registers0_to_31'] = data.output_bit_registers0_to_31
            result = [None]*32
            for ii in range(32):
                if self.data_dir['output_bit_registers0_to_31'] is not None:
                    result[ii] = 2**(ii)&self.data_dir['output_bit_registers0_to_31']==2**(ii)
            return result
        except Exception as e:
            logging.error("Could not get output_bit_registers0_to_31: {}".format(e))
            return None
    
    def output_bit_registers32_to_63(self) -> Optional[bool]:
        try:
            data = self.con.receive()
            self.data_dir['output_bit_registers32_to_63'] = data.output_bit_registers32_to_63
            result = [None]*32
            for ii in range(32):
                if self.data_dir['output_bit_registers32_to_63'] is not None:
                    result[ii] = 2**(ii)&self.data_dir['output_bit_registers32_to_63']==2**(ii)
            return result
        except Exception as e:
            logging.error("Could not get output_bit_registers32_to_63: {}".format(e))
            return None
    
    def output_bit_register_x(self, x:int) -> Optional[bool]: # TODO: check this
        result = [None]*128
        data = self.con.receive()
        self.data_dir[f"output_bit_register_{x}"] = getattr(data, f'output_bit_register_{x}') 
        if x in range(64, 128) and self.data_dir[f"output_bit_register_{x}"] is not None:
            result[x] = 2**(x-64)&self.data_dir[f"output_bit_register_{x}"]==2**(x-64)
        return result

    def output_int_register_x(self, x:int) -> Optional[int]: # TODO try to make this work
        if x in range(0, 48):
            return self.fetch_data(f"output_int_register_{x}")

    def output_double_register_x(self, x:int) -> Optional[float]: # TODO try to make this work
        if x in range(0, 48):
            return self.fetch_data(f"output_double_register_{x}")
        
    def tool_output_mode(self) -> Optional[int]:
        return self.fetch_data('tool_output_mode')
    
    def tool_digital_outputX_mode(self, X:int) -> Optional[int]:
        if X in [0, 1]:
            return self.fetch_data(f'tool_digital_output{X}_mode')
        else:
            raise KeyError('Index out of range')

    def payload(self) -> Optional[float]:
        return self.fetch_data('payload')
    
    def payload_cog(self) -> Optional[float]:
        center_of_gravity = self.fetch_data('payload_cog')
        CX = center_of_gravity[0]
        CY = center_of_gravity[1]
        CZ = center_of_gravity[2]
        return [CX*1000, CY*1000, CZ*1000]
    
    def payload_inertia(self) -> Optional[float]:
        '''[Ixx,Iyy,Izz,Ixy,Ixz,Iyz] expressed in kg*m^2'''
        return self.fetch_data('payload_inertia')
    
    def script_control_line(self) -> Optional[int]:
        return self.fetch_data('script_control_line')
    
    def ft_raw_wrench(self) -> Optional[List[float]]:
        return self.fetch_data('ft_raw_wrench')

    def actual_digital_input_bits(self) -> Optional[bool]:
        return self.fetch_data('actual_digital_input_bits')

    def read_standard_digital_inputs(self, n: int) -> Optional[bool]: 
        if 0 <= n < 8:
            n = 2**n
            return bool(n & self.fetch_data('actual_digital_input_bits') == n)
        else:
            logging.error('n must be between 0 and 7')
            return None
    
    # Print only True standard digital inputs
    def read_standard_digital_inputs_true(self) -> Optional[bool]:
        return [ii for ii in range(8) if self.read_standard_digital_inputs(ii)==True]
    
    # Print only False standard digital inputs
    def read_standard_digital_inputs_false(self) -> Optional[bool]:
        return [ii for ii in range(8) if self.read_standard_digital_inputs(ii)==False]
    
    def read_configurable_digital_inputs(self, n: int) -> Optional[bool]: # TODO: check this
        if 8 <= n+8 < 16:
            n = 2**(n+8)
            return bool(n & self.fetch_data('actual_digital_input_bits') == n)
        else:
            logging.error('n must be between 0 and 7')
            return None
    
    def tool_digital_inputs(self, n: int) -> Optional[bool]:
        if 16 <= n+16 < 18:
            n = 2**(n + 16)
            return bool(n & self.fetch_data('actual_digital_input_bits') == n)
        else:
            logging.error('n must be 0 or 1')
            return None

    def actual_digital_output_bits(self) -> Optional[bool]:
        return self.fetch_data('actual_digital_output_bits')
    
    def read_tool_digital_outputs(self, n: int) -> Optional[bool]:   
        if 16 <= n+16 < 18:
            n = 2**(n+16)
            return bool(n & self.fetch_data('actual_digital_output_bits') == n)
        else:
            logging.error("n must be 0 or 1")
            return None
    
    # Print only True tool_digital_outputs
    def read_tool_digital_outputs_true(self) -> Optional[bool]:
        true_outputs = []
        for i in range(2):
            if self.read_tool_digital_outputs(i):
                true_outputs.append(i)
        return true_outputs
    
    # Print only False tool_digital_outputs
    def read_tool_digital_outputs_false(self) -> Optional[bool]:
        false_outputs = []
        for i in range(2):
            if not self.read_tool_digital_outputs(i):
                false_outputs.append(i)
        return false_outputs
    

    # ROBOT CONTROLLER INPUTS

    def speed_slider_mask(self, n: int=0): # TODO: Does this work?
        if n in [0,1]:
            self.fetch_data = n
            return self.data_dir['speed_slider_mask']
        else:
            raise ValueError("n must be 0 or 1")
    
    def speed_slider_fraction(self,value: int=0): # TODO This does not work
        if 0 <= value <= 100:
            self.setp.speed_slider_mask = 1

            self.setp.speed_slider_fraction = value/100
            self.con.send(self.setp)
            return self.target_speed_fraction()
        else:
            raise ValueError("value must be between 0 and 100")
    
    def standard_digital_output_mask(self, n: int=0): # TODO: Does this work?
        if 0 <= n < 8:
            self.setp.standard_digital_output_mask = n
            self.con.send(self.setp)
            return self.standard_digital_output_mask()
        else:
            raise ValueError("n must be between 0 and 7")
    
    def set_standard_digital_output(self, n: int, value: bool):
        if 0 <= n < 8:
            mask = 1 << n
            value_bit = value << n
            
            self.setp.standard_digital_output_mask = mask
            self.setp.standard_digital_output = value_bit
            
            self.con.send(self.setp)
        else:
            raise ValueError("n must be between 0 and 7")
        
    def configurable_digital_output_mask(self, n: int=0): # TODO
        if 0 <= n < 8:
            self.data_dir['configurable_digital_output_mask'] = n
            return self.data_dir['configurable_digital_output_mask']
        else:
            raise ValueError("n must be between 0 and 7")
    
    def read_standard_digital_output(self, n: int) -> Optional[bool]:
        if 0 <= n < 8:
            n = 2**n
            return bool(n & self.fetch_data('actual_digital_output_bits') == n)
        else:
            raise ValueError("n must be between 0 and 7")
    
    # Print out only True starndard digital outputs
    def read_standard_digital_output_true(self) -> Optional[bool]:
        true_outputs = []
        for i in range(8):
            if self.read_standard_digital_output(i):
                # Add all the True standard digital outputs to a list
                true_outputs.append(i)
        return true_outputs
    
    # Print out only False starndard digital outputs
    def read_standard_digital_output_false(self) -> Optional[bool]:
        false_outputs = []
        for i in range(8):
            if not self.read_standard_digital_output(i):
                # Add all the False standard digital outputs to a list
                false_outputs.append(i)
        return false_outputs
    
        
    def read_configurable_digital_output(self, n: int) -> Optional[bool]:
        if 8 <= n < 16:
            n = 2**(n)
            return bool(n & self.fetch_data('actual_digital_output_bits') == n)
        else:
            raise ValueError("n must be between 8 and 15")
    
    def set_configurable_digital_output(self, n: int, value: bool):
        if 8 <= n < 16:
            adjusted_n = n - 8
            mask = 1 << adjusted_n
            value_bit = value << adjusted_n
            
            self.setp.configurable_digital_output_mask = mask
            self.setp.configurable_digital_output = value_bit
            
            self.con.send(self.setp)
        else:
            raise ValueError("n must be between 8 and 15")
            
    # Print out only True configurable digital outputs
    def read_configurable_digital_output_true(self) -> Optional[bool]:
        true_outputs = []
        for i in range(8, 16):
            if self.read_configurable_digital_output(i):
                # Add all the True configurable digital outputs to a list
                true_outputs.append(i-8)
        return true_outputs
    
    # Print out only False configurable digital outputs
    def read_configurable_digital_output_false(self) -> Optional[bool]:
        false_outputs = []
        for i in range(8, 16):
            if not self.read_configurable_digital_output(i):
                # Add all the False configurable digital outputs to a list
                false_outputs.append(i-8)
        return false_outputs
    
    def standard_analog_output_mask(self, n: int=0):
        if 0 <= n < 2:
            self.data_dir['standard_analog_output_mask'] = n
            return self.data_dir['standard_analog_output_mask']
        else:
            raise ValueError("n must be 0 or 1")
    
    def standard_analog_output_type(self, n: int=0):
        if 0 <= n < 2:
            self.data_dir['standard_analog_output_type'] = n
            return self.data_dir['standard_analog_output_type']
        else:
            raise ValueError("n must be 0 or 1")
    
    def standard_analog_output(self, n: int) -> Union[int, float]:
        if n in [0, 1]:
            return self.fetch_data(f'standard_analog_output{n}')
        else:
            raise KeyError('Index out of range')
    
    def input_bit_registers(self) -> Optional[bool]:
        result = [None]*64
        for ii in range(64):
            if ii<32 and self.data_dir['input_bit_registers0_to_31'] is not None:
                result[ii] = 2**(ii)&self.data_dir['input_bit_registers0_to_31']==2**(ii)
            elif ii>31 and self.data_dir['input_bit_registers32_to_63'] is not None:
                result[ii] = 2**(ii-32)&self.data_dir['input_bit_registers32_to_63']==2**(ii-32)
        return result
    
    def input_bit_registers_x(self, x:int) -> Optional[bool]: # (x = [64, 127])
        result = [None]*128
        if x in range(64, 128) and self.dataDir[f"input_bit_registers_{x}"] is not None:
            result[x] = 2**(x-64)&self.dataDir[f"input_bit_registers_{x}"]==2**(x-64)
        return result
    
    def input_int_register_x(self, x:int) -> Optional[int]: # TODO try to make this work
        if x in range(0, 48):
            return self.fetch_data(f"input_int_register_{x}")
    
    def input_double_register_x(self, x:int) -> Optional[float]: # TODO try to make this work
        if x in range(0, 48):
            return self.fetch_data(f"input_double_register_{x}")
    

class RobotStatusBit:
    def __init__(self):
        self.power_on: Optional[bool] = None
        self.program_running: Optional[bool] = None
        self.teach_button_pressed: Optional[bool] = None
        self.power_button_pressed: Optional[bool] = None
    
    # Do not use this method, it is only for testing
    @staticmethod
    def change_robot_status_bit(bit_name: str, status: bool):
        if hasattr(RobotStatusBit, bit_name):
            setattr(RobotStatusBit, bit_name, status)
        else:
            raise KeyError('No such bit name')
    
    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

class SafetyStatusBit:
    def __init__(self):
        self.normal_mode: Optional[bool] = None
        self.reduced_mode: Optional[bool] = None
        self.protective_stopped: Optional[bool] = None
        self.recovery_mode: Optional[bool] = None
        self.safeguard_stopped: Optional[bool] = None
        self.system_emergency_stopped: Optional[bool] = None
        self.robot_emergency_stopped: Optional[bool] = None
        self.emergency_stopped: Optional[bool] = None
        self.violation: Optional[bool] = None
        self.fault: Optional[bool] = None
        self.stopped_due_to_safety: Optional[bool] = None
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    # Do not use this method, it is only for testing
    @staticmethod
    def change_safety_status_bit(bit_name: str, status: bool):
        if hasattr(SafetyStatusBit, bit_name):
            setattr(SafetyStatusBit, bit_name, status)
        else:
            print(f"No such bit: {bit_name}")
    
    def __str__(self):
        attrs = vars(self)
        return ', '.join("\n%s: %s" % item for item in attrs.items())
    
    # return a list of all the bits that are True in  a dictionary format
    def get_true_bits(self):
        attrs = vars(self)
        return [item for item in attrs.items() if item[1] is True]
    
    # return a list of all the bits that are False in  a dictionary format
    def get_false_bits(self):
        attrs = vars(self)
        return [item for item in attrs.items() if item[1] is False]




if __name__ == "__main__":
    
    # Parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='192.168.1.11', nargs='?', help='name of host to connect to')
    parser.add_argument('--port', type=int, default=30004, help='port number')
    parser.add_argument('--frequency', type=int, default=500, choices=[125, 250, 500], metavar='FREQUENCY', help='Herz')
    parser.add_argument('--config', default='rtde_configuration.xml', help='data configuration file to use')
    parser.add_argument("--verbose", action="store_true", help="increase output verbosity")
    parser.add_argument("--buffered", action="store_true", help="Use buffered receive which doesn't skip data")
    parser.add_argument("--binary", action="store_true", help="Save the data in binary format")
    parser.add_argument("--recipe_setp", type=str, default='rci', help='Settable attributes in rtde_configuration.xml')
    parser.add_argument("--recipe_out", type=str, default='rco', help='Attributes that gives you the info, not changeable')
    args = parser.parse_args()

    # Create the RTDE object
    with RTDECommands(host=args.host, recipe_setp=args.recipe_setp, recipe_out=args.recipe_out) as ur:
        ur.set_configurable_digital_output(10,1)
        ur.set_configurable_digital_output(11,1)
        print(ur.read_configurable_digital_output_true())
