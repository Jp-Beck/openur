'''import socket
import threading
import time
import re
import numpy as np
import select
import logging

from openur.rtde_command import RTDECommands

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')



class ConnectionState:
    ERROR = 0
    DISCONNECTED = 1
    CONNECTED = 2
    PAUSED = 3
    STARTED = 4
    STOPPED = 5




DEFAULT_TIMEOUT = 2.0  # Assuming a value for the constant as it's not provided in the code

class RealTimeClient:

    PORT = 30003  # Real Time CLient Port

    def __init__(self):
        self.__robot_model = RTDECommands(host='10.2.4.111', recipe_setp='rci', recipe_out='rco')
        self.__robot_model.connect()
        self.__robot_model.safety_status_bits()



        self.__robot_model.rtc_connection_state = ConnectionState.DISCONNECTED
        self.__reconnect_timeout = 60
        self.__sock = None
        self.__thread = None

        if self.__connect():
            logging.info('RT_Client constructor done')
        else:
            logging.info('RT_Client constructor done but not connected')

    def __connect(self):
        if self.__sock:
            return True

        t0 = time.time()
        while (time.time() - t0 < self.__reconnect_timeout) and self.__robot_model.rtc_connection_state < ConnectionState.CONNECTED:
            try:
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.__sock.settimeout(DEFAULT_TIMEOUT)
                self.__sock.connect(('10.2.4.111', self.PORT)) # self.__robot_model.ip_address
                self.__robot_model.rtc_connection_state = ConnectionState.CONNECTED
                time.sleep(0.5)
                logging.info('Connected')
                return True
            except (socket.timeout, socket.error):
                self.__sock = None
                logging.error('RTC connecting')

        return False

    def disconnect(self):
        if self.__sock:
            self.__sock.close()
            self.__sock = None
            logging.info('Disconnected')
        self.__robot_model.rtc_connection_state = ConnectionState.DISCONNECTED
        return True

    def is_rtc_connected(self):
        return self.__robot_model.rtc_connection_state > ConnectionState.DISCONNECTED

    def send_program(self, prg=''):
        if not self.is_rtc_connected():
            if not self.__connect():
                logging.error('SendProgram: Not connected to robot')

        if self.__robot_model.stop_running_flag:
            logging.info('SendProgram: Send program aborted due to stop_running_flag')
            return

        # Use a lock here for thread safety
        thread_lock = threading.Lock()
        with thread_lock:
            if self.__thread is not None and self.__robot_model.rtc_program_running:
                self.__robot_model.stop_running_flag = True
                while self.__robot_model.rtc_program_running:
                    time.sleep(0.1)
                self.__robot_model.stop_running_flag = False
                self.__thread.join()

        self.__robot_model.rtc_program_running = True
        self.__robot_model.rtc_program_execution_error = False

        modified_program = self.__add_status_bit_to_prog(prg)

        self.__send_prg(modified_program)
        self.__thread = threading.Thread(target=self.__wait_for_program_to_finish, kwargs={'prg': prg})
        self.__thread.start()

    def send(self, prg=''):
        if not self.is_rtc_connected() and not self.__connect():
            logging.error('Send: Not connected to robot')
            return

        if self.__robot_model.stop_running_flag:
            logging.info('Send: Send command aborted due to stop_running_flag')
            return

        self.__robot_model.rtc_program_running = True
        self.__robot_model.rtc_program_execution_error = False

        self.__send_prg(prg)
        self.__robot_model.rtc_program_running = False

    def __add_status_bit_to_prog(self, prg):
        def1 = prg.find('def ')
        if def1 >= 0:
            prg_len = len(prg)
            prg = prg.replace('):\n', '):\n  write_output_boolean_register(0, True)\n', 1)
            if len(prg) == prg_len:
                self.__logger.warning('Send_program: Syntax error in program')
                return False

            if (len(re.findall('def ', prg))) > 1:
                main_prg = prg[0:prg[def1 + 4:].find('def ') + def1 + 4]
                main_prg_end = (np.max([main_prg.rfind('end '), main_prg.rfind('end\n')]))
                prg = prg.replace(prg[0:main_prg_end],
                                  f"{prg[0:main_prg_end]}\n  write_output_boolean_register(1, True)\n", 1)
            else:
                main_prg_end = prg.rfind('end')
                prg = prg.replace(prg[0:main_prg_end],
                                  f"{prg[0:main_prg_end]}\n  write_output_boolean_register(1, True)\n", 1)

        else:
            prg = 'def script():\n  write_output_boolean_register(0, True)\n  ' + prg + '\n  write_output_boolean_register(1, True)\nend\n'
        return prg

    def __send_prg(self, prg):
        program_send = False
        self.__robot_model.force_remote_active_flag = False
        while not self.__robot_model.stop_running_flag and not program_send:
            try:
                (_, writable, _) = select.select([], [self.__sock], [], DEFAULT_TIMEOUT)
                if writable:
                    self.__sock.send(prg.encode())
                    logging.info(f'Program sent to Robot:\n{prg}')
                    program_send = True
            except:
                self.__sock = None
                self.__robot_model.rtc_connection_state = ConnectionState.ERROR
                self.__logger.warning('Could not send program!')
                self.__connect()
        if not program_send:
            self.__robot_model.rtc_program_running = False
            logging.error('Program re-sending timed out - Could not send program!')
        time.sleep(0.1)

    def __wait_for_program_to_finish(self, prg):
        wait_for_program_start = len(prg) / 50
        not_run = 0
        prg_rest = 'def reset_register():\n  write_output_boolean_register(0, False)\n  write_output_boolean_register(1, False)\nend\n'
        while not self.__robot_model.stop_running_flag and self.__robot_model.rtc_program_running:
            if self.__robot_model.safety_status_bits().stopped_due_to_safety:
                    self.__robot_model.rtc_program_running = False
                    self.__robot_model.rtc_program_execution_error = True
                    logging.error('SendProgram: Safety Stop')
            elif self.__robot_model.output_bit_registers()[0] == False:
                logging.debug('sendProgram: Program not started')
                not_run += 1
                if not_run > wait_for_program_start:
                    self.__robot_model.rtc_program_running = False
                    logging.error('sendProgram: Program not able to run')
            elif self.__robot_model.output_bit_registers()[0] == True and self.__robot_model.output_bit_registers()[1] == True:
                self.__robot_model.rtc_program_running = False
                logging.info('sendProgram: Finished')
            elif self.__robot_model.output_bit_registers()[0] == True:
                if self.__robot_model.robot_status_bits().program_running:
                    logging.debug('sendProgram: UR running')
                    not_run = 0
                else:
                    not_run += 1
                    if not_run > 10:
                        self.__robot_model.rtc_program_running = False
                        self.__robot_model.rtc_program_execution_error = True
                        logging.error('SendProgram: Program Stopped but not finished!!!')
            else:
                self.__robot_model.rtc_program_running = False
                logging.error('SendProgram: Unknown error')
            time.sleep(0.5)
        self.__send_prg(prg_rest)
        self.__robot_model.rtc_program_running = False'''



import socket
import threading
import time
import re
import select
import logging
import numpy as np

from openur.rtde_command import RTDECommands

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ConnectionState:
    ERROR = 0
    DISCONNECTED = 1
    CONNECTED = 2
    PAUSED = 3
    STARTED = 4
    STOPPED = 5

DEFAULT_TIMEOUT = 2.0

class RealTimeClient:

    PORT = 30003

    def __init__(self):
        self.robot_model = RTDECommands(host='10.2.4.111', recipe_setp='rci', recipe_out='rco')
        self.robot_model.connect()
        self.robot_model.safety_status_bits()
        self.robot_model.rtc_connection_state = ConnectionState.DISCONNECTED
        self.reconnect_timeout = 60
        self.sock = None
        self.thread = None

        if self.connect():
            logging.info('RealTimeClient constructor done')
        else:
            logging.info('RealTimeClient constructor done but not connected')

    def connect(self):
        if self.sock:
            return True

        start_time = time.time()
        while (time.time() - start_time < self.reconnect_timeout) and self.robot_model.rtc_connection_state < ConnectionState.CONNECTED:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.settimeout(DEFAULT_TIMEOUT)
                self.sock.connect(('10.2.4.111', self.PORT))
                self.robot_model.rtc_connection_state = ConnectionState.CONNECTED
                time.sleep(0.5)
                logging.info('Connected')
                return True
            except (socket.timeout, socket.error):
                self.sock = None
                logging.error('RealTimeClient connecting')

        return False

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
            logging.info('Disconnected')
        self.robot_model.rtc_connection_state = ConnectionState.DISCONNECTED
        return True

    def is_rtc_connected(self):
        return self.robot_model.rtc_connection_state > ConnectionState.DISCONNECTED

    def send_program(self, prg=''):
        if not self.is_rtc_connected():
            if not self.connect():
                logging.error('SendProgram: Not connected to robot')

        if self.robot_model.stop_running_flag:
            logging.info('SendProgram: Send program aborted due to stop_running_flag')
            return

        # Use a lock here for thread safety
        thread_lock = threading.Lock()
        with thread_lock:
            if self.thread is not None and self.robot_model.rtc_program_running:
                self.robot_model.stop_running_flag = True
                while self.robot_model.rtc_program_running:
                    time.sleep(0.1)
                self.robot_model.stop_running_flag = False
                self.thread.join()

        self.robot_model.rtc_program_running = True
        self.robot_model.rtc_program_execution_error = False

        modified_program = self.add_status_bit_to_prog(prg)

        self.send_prg(modified_program)
        self.thread = threading.Thread(target=self.wait_for_program_to_finish, kwargs={'prg': prg})
        self.thread.start()

    def send(self, prg=''):
        if not self.is_rtc_connected() and not self.connect():
            logging.error('Send: Not connected to robot')
            return

        if self.robot_model.stop_running_flag:
            logging.info('Send: Send command aborted due to stop_running_flag')
            return

        self.robot_model.rtc_program_running = True
        self.robot_model.rtc_program_execution_error = False

        self.send_prg(prg)
        self.robot_model.rtc_program_running = False

    def add_status_bit_to_prog(self, prg):
        def1 = prg.find('def ')
        if def1 >= 0:
            prg_len = len(prg)
            prg = prg.replace('):\n', '):\n  write_output_boolean_register(0, True)\n', 1)
            if len(prg) == prg_len:
                self.logger.warning('Send_program: Syntax error in program')
                return False

            if (len(re.findall('def ', prg))) > 1:
                main_prg = prg[0:prg[def1 + 4:].find('def ') + def1 + 4]
                main_prg_end = (np.max([main_prg.rfind('end '), main_prg.rfind('end\n')]))
                prg = prg.replace(prg[0:main_prg_end],
                                  f"{prg[0:main_prg_end]}\n  write_output_boolean_register(1, True)\n", 1)
            else:
                main_prg_end = prg.rfind('end')
                prg = prg.replace(prg[0:main_prg_end],
                                  f"{prg[0:main_prg_end]}\n  write_output_boolean_register(1, True)\n", 1)

        else:
            prg = 'def script():\n  write_output_boolean_register(0, True)\n  ' + prg + '\n  write_output_boolean_register(1, True)\nend\n'
        return prg

    def send_prg(self, prg):
        program_send = False
        self.robot_model.force_remote_active_flag = False
        while not self.robot_model.stop_running_flag and not program_send:
            try:
                (_, writable, _) = select.select([], [self.sock], [], DEFAULT_TIMEOUT)
                if writable:
                    self.sock.send(prg.encode())
                    logging.info(f'Program sent to Robot:\n{prg}')
                    program_send = True
            except:
                self.sock = None
                self.robot_model.rtc_connection_state = ConnectionState.ERROR
                self.logger.warning('Could not send program!')
                self.connect()
        if not program_send:
            self.robot_model.rtc_program_running = False
            logging.error('Program re-sending timed out - Could not send program!')
        time.sleep(0.1)

    def wait_for_program_to_finish(self, prg):
        wait_for_program_start = len(prg) / 50
        not_run = 0
        prg_rest = 'def reset_register():\n  write_output_boolean_register(0, False)\n  write_output_boolean_register(1, False)\nend\n'
        while not self.robot_model.stop_running_flag and self.robot_model.rtc_program_running:
            if self.robot_model.safety_status_bits().stopped_due_to_safety:
                    self.robot_model.rtc_program_running = False
                    self.robot_model.rtc_program_execution_error = True
                    logging.error('SendProgram: Safety Stop')
            elif self.robot_model.output_bit_registers()[0] == False:
                logging.debug('sendProgram: Program not started')
                not_run += 1
                if not_run > wait_for_program_start:
                    self.robot_model.rtc_program_running = False
                    logging.error('sendProgram: Program did not start')
            elif self.robot_model.output_bit_registers()[1] == True:
                self.robot_model.rtc_program_running = False
                logging.info('SendProgram: Program finished')
                self.send(prg_rest)
            else:
                logging.debug('SendProgram: Program running')
        self.robot_model.rtc_program_running = False

    def abort_program(self):
        self.robot_model.stop_running_flag = True
        prg_rest = 'def reset_register():\n  write_output_boolean_register(0, False)\n  write_output_boolean_register(1, False)\nend\n'
        self.send(prg_rest)
        while self.robot_model.rtc_program_running:
            time.sleep(0.1)
        self.robot_model.stop_running_flag = False

    def pause_program(self):
        if self.is_rtc_connected() and self.robot_model.rtc_program_running:
            self.robot_model.suspend_program()
            self.robot_model.rtc_connection_state = ConnectionState.PAUSED
        else:
            logging.error('PauseProgram: Not connected to robot or no program running')

    def resume_program(self):
        if self.is_rtc_connected() and self.robot_model.rtc_connection_state == ConnectionState.PAUSED:
            self.robot_model.rtc_connection_state = ConnectionState.CONNECTED
            self.robot_model.resume_program()
        else:
            logging.error('ResumeProgram: Not connected to robot or no program running')

    def is_program_running(self):
        return self.robot_model.rtc_program_running

    def is_program_paused(self):
        return self.robot_model.rtc_connection_state == ConnectionState.PAUSED

    def has_program_execution_error(self):
        return self.robot_model.rtc_program_execution_error

    def is_safety_stopped(self):
        return self.robot_model.safety_status_bits().stopped_due_to_safety


rob =  RealTimeClient()
while True:
    rob.send_program('set_digital_out(0,True)\n  sleep(1)\n  set_digital_out(1,True)\n  sleep(1)\n  set_digital_out(0,False)\n  set_digital_out(2,True)\n  set_digital_out(1,False)\n  set_digital_out(3,True)\n  set_digital_out(2,False)\n  set_digital_out(3,False)')
    time.sleep(3)
