__author__ = "Beck Isakov"
__copyright__ = "Beck isakov"
__contact__ = "https://github.com/Jp-Beck"
__license__ = "GPL v3"
__version__ = "0.2.0"
__maintainer__ = "Beck Isakov"
__email__ = "jp-beck@outlook.com"
__status__ = "Development"

class ConnectionState:
    ERROR = 0
    DISCONNECTED = 1
    CONNECTED = 2
    PAUSED = 3
    STARTED = 4

    @staticmethod
    def change_connection_state(state):
        if state == ConnectionState.ERROR:
            return "ERROR"
        elif state == ConnectionState.DISCONNECTED:
            return "DISCONNECTED"
        elif state == ConnectionState.CONNECTED:
            return "CONNECTED"
        elif state == ConnectionState.PAUSED:
            return "PAUSED"
        elif state == ConnectionState.STARTED:
            return "STARTED"
        else:
            return "UNKNOWN"

# print(ConnectionState.change_connection_state(ConnectionState.ERROR))
