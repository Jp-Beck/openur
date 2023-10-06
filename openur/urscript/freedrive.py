#!/usr/bin/env python
# myDashClient.py
# Description: This script is a simple example of how to use the Real Time Client iand Dashboard nterface to send commands to the robot.
"""
# Author: i-beck 
"""

__all__ = ['RemoteControl']


tcp_port = 30003
BUFFER_SIZE = 1108
tcp_ip = '10.2.4.110'

import socket
import time
import sys

class RemoteControl:
    def __init__(self, host=tcp_ip, port=29999):
        self.host = host
        self.port = port
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect()

    def _connect(self):
        attempts = 0
        while attempts < 5:
            try:
                self.conn.connect((self.host, self.port))
                sys.stdout.write('Socket opened...\n')
                data = self.conn.recv(1024).decode('utf8')
                break 
            except socket.error as e:
                sys.stdout.write("Error connecting to {0}:{1}: {2}\n".format(self.host, self.port, e))
                time.sleep(5)
                attempts += 1
        if attempts == 5:
            sys.stdout.write("Failed to connect to {0}:{1}\n".format(self.host, self.port))
            sys.exit(1)

    def close(self):
        self.conn.close()

    def dashboard_command(self, cmd='is in remote control'):
        try:
            self.conn.send("{}\n".format(cmd).encode('utf-8'))
            data = self.conn.recv(1024)
            if data == b'Safetymode: PROTECTIVE_STOP\n':
                return True
            elif data != b'Safetymode: NORMAL\n':
                return False
        except socket.error as e:
            sys.stdout.write("Error communicating with {0}:{1}: {2}\n".format(self.host, self.port, e))
            time.sleep(5)
            self._connect()
            #return self.command(cmd) # retry if you want to make sure the last command was executed

class RealTimeClient:
    def __init__(self, host=tcp_ip, port=30003):
        self.host = host
        self.port = port
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect()

    def _connect(self):
        try:
            self.conn.connect((self.host, self.port))
            sys.stdout.write("Connected to Real Time Client on {0}:{1}\n".format(self.host, self.port))
        except socket.error as e:
            sys.stdout.write("Failed to connect to Real Time Client on {0}:{1}: {2}\n".format(self.host, self.port, e))
            time.sleep(5)
            self._connect() # Try to reconnect if connection failed

    def matlab_command(self, matlab_cmd='set_digital_out(0,True)'):
        try:
            self.conn.send(("{}\n").format(matlab_cmd).encode('utf-8'))
        except socket.error as e:
            sys.stdout.write("Failed to send command to Real Time Client on {0}:{1}: {2}\n".format(self.host, self.port, e))
            self._connect() # Try to reconnect and resend the command if it failed

    def close(self):
        self.conn.close()

def main(rc, rtc):
    attempts = 0
    while True:
        try:
            time.sleep(1)
            if rc.dashboard_command("safetymode"):
                # Set signal to visualize that the robot is in normal safety mode
                rtc.matlab_command('sec beck():')
                rtc.matlab_command('set_digital_out(0,False)') # You may want top use set_configurable_digital_input_action(0, "freedrive")
                rtc.matlab_command('end')
                time.sleep(0.008)
                rc.dashboard_command("unlock protective stop")
                time.sleep(2)
                rc.dashboard_command("play")
            else:
                # Set signal to visualize that the robot is in protective stop
                rtc.matlab_command('sec beck():')
                rtc.matlab_command('set_digital_out(0,True)')
                rtc.matlab_command('end')
                print("Robot is in normal safety mode")
                if attempts == 0:
                    rc.dashboard_command("play")
                    time.sleep(1)
                    attempts += 1
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            rc.close()
            rtc.close() # Don't forget to close this connection too
            sys.exit(0)
        except socket.error as e:
            print("Error communicating with {0}:{1}: {2}\n".format(rc.host, rc.port, e))
            time.sleep(5)
            rc._connect()



if __name__ == '__main__':
    rc = RemoteControl()
    rtc = RealTimeClient()
    main(rc, rtc) # Pass the rtc instance to the main function