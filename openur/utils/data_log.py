import threading
from . import dataLogging
from. import robotModel
import numpy as np
import time
import xml.etree.ElementTree as ET
from typing import Dict, Union, Any

class DataLog(threading.Thread):
    """
    This module handle logging of all data signal from the robot (not event logging).
    """ 

    def __init__(self, robotModel: robotModel.RobotModel) -> None:

        threading.Thread.__init__(self)

        # Initialize logger
        logger = dataLogging.DataLogging()
        self.__dataLogger = logger.__dict__[logger.AddDataLogging(__name__)]
        self.__logger = logger.__dict__[logger.AddEventLogging(__name__, log2Consol=True)] 

        self.__robotModel = robotModel
        self.__stop_event = threading.Event()

        # Config initialization
        self.__config = Config()
        self.__readConfig(configFileName='logConfig.xml', config=self.__config)
        
        self.__robotModelDataDirCopy: Dict[str, Any] = None
        self.start()
        self.__logger.info('DataLog constructor done')

    def __readConfig(self, configFileName: str, config: 'Config') -> None:
        tree = ET.parse(configFileName)
        logConfig = tree.getroot()
        config.Decimals = int(logConfig.find('dataLogConfig').find('defaultDecimals').text)       
        for child in logConfig.find('dataLogConfig').find('logParameters'):
            setattr(config, child.tag, child.text)

    def logdata(self, robotModelDataDir: Dict[str, Union[np.ndarray, float, bool, int, np.float64]]) -> None:
        """
        Logs data if it is not equal to the previously logged data after rounding it to required decimal places.
        """

        if self.__robotModelDataDirCopy is not None:
            if self.__robotModelDataDirCopy['timestamp'] != robotModelDataDir['timestamp'] or robotModelDataDir['timestamp'] is None:
                for tagname, tagvalue in robotModelDataDir.items():
                    if tagname != 'timestamp' and  tagvalue is not None:
                        self.__log_value(tagname, tagvalue, robotModelDataDir['timestamp'])

        self.__robotModelDataDirCopy = robotModelDataDir.copy()

    def __log_value(self, tagname: str, tagvalue: Union[np.ndarray, float, bool, int, np.float64], timestamp: Any) -> None:
        """
        Helper function to log a particular tag value
        """
        roundingDecimals = getattr(self.__config, tagname, self.__config.Decimals)
        if isinstance(tagvalue, np.ndarray):
            self.__log_array(tagname, tagvalue, timestamp, roundingDecimals)
        elif isinstance(tagvalue, (float, np.float64)):
            self.__log_float(tagname, tagvalue, timestamp, roundingDecimals)
        elif isinstance(tagvalue, (bool, int)):
            self.__log_primitive(tagname, tagvalue, timestamp)
        else:
            self.__logger.warning(f'Logger data unexpected type in rtde.py - class URRTDElogger - def logdata Type: {type(tagvalue).__name__}')

    def __log_array(self, tagname: str, tagvalue: np.ndarray, timestamp: Any, roundingDecimals: int) -> None:
        """
        Helper function to log array type values
        """
        roundedValues = np.round(tagvalue, roundingDecimals)
        roundedValuesCopy = np.round(self.__robotModelDataDirCopy.get(tagname, roundedValues+1), roundingDecimals)
        if not np.array_equal(roundedValues, roundedValuesCopy):
            data = ';'.join(map(str, roundedValues.tolist()))
            self.__dataLogger.info(f'{tagname};{timestamp};{data}')

    def __log_float(self, tagname: str, tagvalue: float, timestamp: Any, roundingDecimals: int) -> None:
        """
        Helper function to log float type values
        """
        roundedValue = round(tagvalue, roundingDecimals)
        roundedValueCopy = round(self.__robotModelDataDirCopy.get(tagname, roundedValue+1), roundingDecimals)
        if roundedValue != roundedValueCopy:
            self.__dataLogger.info(f'{tagname};{timestamp};{roundedValue}')

    def __log_primitive(self, tagname: str, tagvalue: Union[bool, int], timestamp: Any) -> None:
        """
        Helper function to log boolean or integer type values
        """
        if tagvalue != self.__robotModelDataDirCopy.get(tagname):
            self.__dataLogger.info(f'{tagname};{timestamp};{tagvalue}')

    def close(self) -> None:
        if not self.__stop_event.is_set():
            self.__stop_event.set()
            self.join()
 
    def run(self) -> None:
        self.__stop_event.clear()
        while not self.__stop_event.is_set():
            try:
                dataDirCopy = self.__robotModel.dataDir.copy()
                self.logdata(dataDirCopy)
                time.sleep(0.005)
            except Exception as e:
                self.__robotModelDataDirCopy = dataDirCopy
                self.__logger.warning(f"DataLog error while running, but will retry. Error: {str(e)}")
        self.__logger.info("DataLog is stopped")

class Config:
    Decimals: int = 5
