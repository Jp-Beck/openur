

import os, sys, time, logging, argparse, threading, functools
from contextlib import ExitStack
from openur.rtde import rtde
from openur.rtde import rtde_config

# from URBasic.dataTypes import DOUBLE, UINT32, UINT64, VECTOR3D, VECTOR6D, STRING

if sys.version_info[0] < 3:
    import xmlrpclib
    from SimpleXMLRPCServer import SimpleXMLRPCServer
else:
    from xmlrpc import client as xmlrpclib
    from xmlrpc.server import SimpleXMLRPCServer

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config


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

class URConnect:

    def __init__(self, host, port, recipe_setp, recipe_out, max_retries=10):
        self.ROBOT_HOST = host
        self.ROBOT_PORT = port
        self.Keep_running = True
        self.max_retries = max_retries
        self.exit_flag = threading.Event()
        self.lock = threading.Lock()
        self.con = None

        self.conf = rtde_config.ConfigFile('rtde_configuration.xml')
        self.setp_names, self.setp_types = self.conf.get_recipe(recipe_setp)
        self.output_names, self.output_types = self.conf.get_recipe(recipe_out)



    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

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
                logging.info('RTDE Connection established...')
                break 
            except (Exception) as e:
                logging.error(f"Error connecting to {self.ROBOT_HOST}:{self.ROBOT_PORT}: {e}")
                retries += 1
                time.sleep(5 ** retries)
    
    def close(self):
        try:
            if self.con:
                self.con.disconnect()
                logging.info('Connection closed...')
        except (Exception) as e:
            logging.error(f"Error closing connection to {self.ROBOT_HOST}:{self.ROBOT_PORT}: {e}")

    def stop_rtde_connection(self):
        """Stop any ongoing connection attempts or operations."""
        self.exit_flag.set()
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

