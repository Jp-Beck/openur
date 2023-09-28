__author__ = "Beck Isakov"
__copyright__ = "Copyright 2023, Beck Isakov, Japan"
__license__ = "GPL v3"

import threading
from . import dataLogging
import numpy as np
import time
import xml.etree.ElementTree as ET


class DataLog(threading.Thread):
    '''
    This module handle logging of all data signal from the robot (not event logging).
    ''' 
    def __init__(self, robotModel):

        if(False):
            assert isinstance(robotModel, URBasic.robotModel.RobotModel)  ### This line is to get code completion for RobotModel
        self.__robotModel = robotModel
        threading.Thread.__init__(self)
        logger = dataLogging.DataLogging()
        name = logger.AddDataLogging(__name__)
        self.__dataLogger = logger.__dict__[name]
        name = logger.AddEventLogging(__name__,log2Consol=True)        
        self.__logger = logger.__dict__[name]
        self.__stop_event = True
        
        
        configFilename = 'logConfig.xml'
        self.__config = Config
        self.__readConfig(configFileName=configFilename, config=self.__config)
        
        self.__robotModelDataDirCopy = None
        self.start()
        self.__logger.info('DataLog constructor done')
         
         
    def __readConfig(self, configFileName, config):
        tree = ET.parse(configFileName)
        logConfig = tree.getroot()
        dataLogConfig = logConfig.find('dataLogConfig')
        decimals = dataLogConfig.find('defaultDecimals')
        config.Decimals = int(decimals.text)         
        logParameters = dataLogConfig.find('logParameters')
        for Child in logParameters:
            setattr(config, Child.tag, Child.text)
            

         
    def logdata(self, robotModelDataDir):
        if(self.__robotModelDataDirCopy != None):
            if(self.__robotModelDataDirCopy['timestamp'] != robotModelDataDir['timestamp'] or robotModelDataDir['timestamp'] is None):
                for tagname in robotModelDataDir.keys():
                    if tagname != 'timestamp' and  robotModelDataDir[tagname] is not None:
                        roundingDecimals = self.__config.Decimals
                        tp = type(robotModelDataDir[tagname])
                        if tp is np.ndarray:
                            if tagname in self.__config.__dict__:
                                roundingDecimals = int(self.__config.__dict__[tagname])
                            roundedValues = np.round(robotModelDataDir[tagname], roundingDecimals)
                            if self.__robotModelDataDirCopy[tagname] is None:
                                roundedValuesCopy = roundedValues+1
                            else:
                                roundedValuesCopy = np.round(self.__robotModelDataDirCopy[tagname], roundingDecimals)
                            if not (roundedValues==roundedValuesCopy).all():
                                if 6==len(robotModelDataDir[tagname]):
                                    self.__dataLogger.info((tagname+';%s;%s;%s;%s;%s;%s;%s'), robotModelDataDir['timestamp'], *roundedValues)
                                elif 3==len(robotModelDataDir[tagname]):
                                    self.__dataLogger.info((tagname+';%s;%s;%s;%s'), robotModelDataDir['timestamp'], *roundedValues)
                                else:
                                    self.__logger.warning('Logger data unexpected type in rtde.py - class URRTDElogger - def logdata Type: ' + str(tp) + ' - Len: ' + str(len(robotModelDataDir[tagname])))
                        elif tp is float:
                            if tagname in self.__config.__dict__:
                                roundingDecimals = int(self.__config.__dict__[tagname])
                            roundedValues = round(robotModelDataDir[tagname], roundingDecimals)
                            if self.__robotModelDataDirCopy[tagname] is None:
                                roundedValuesCopy = roundedValues+1
                            else:                            
                                roundedValuesCopy = round(self.__robotModelDataDirCopy[tagname], roundingDecimals)
                            if roundedValues != roundedValuesCopy:
                                self.__dataLogger.info((tagname+';%s;%s'), robotModelDataDir['timestamp'], roundedValues)
                        elif tp is bool or tp is int or tp is np.float64: 
                            if robotModelDataDir[tagname] != self.__robotModelDataDirCopy[tagname]:
                                self.__dataLogger.info((tagname+';%s;%s'), robotModelDataDir['timestamp'], robotModelDataDir[tagname])
                        else:
                            self.__logger.warning('Logger data unexpected type in rtde.py - class URRTDElogger - def logdata Type: ' + str(tp))
        self.__robotModelDataDirCopy = robotModelDataDir
        
                    
    def close(self):
        if self.__stop_event is False:
            self.__stop_event = True
            self.join()
 
    def run(self):
        self.__stop_event = False
        while not self.__stop_event:
            try:
                dataDirCopy = self.__robotModel.dataDir.copy()
                self.logdata(dataDirCopy)
                time.sleep(0.005)
            except:
                self.__robotModelDataDirCopy = dataDirCopy
                self.__logger.warning("DataLog error while running, but will retry")
        self.__logger.info("DataLog is stopped")

class Config(object):
    Decimals = 5
