'''
Python 3.x library to control an UR robot through its TCP/IP interfaces
Copyright (C) 2017  Martin Huus Bjerge, Rope Robotics ApS, Denmark

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL "Rope Robotics ApS" BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Except as contained in this notice, the name of "Rope Robotics ApS" shall not be used
in advertising or otherwise to promote the sale, use or other dealings in this Software
without prior written authorization from "Rope Robotics ApS".
'''

__author__ = "Martin Huus Bjerge"
__copyright__ = "Copyright 2017, Rope Robotics ApS, Denmark"
__license__ = "MIT License"

import logging
import time
import os
import re
import ast
from typing import Tuple, Optional
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml
from enum import Enum
import URBasic


class FileMode(Enum):
    OVERWRITE = "w"
    APPEND = "a"


class DataLogging:
    '''
    A module that add general logging functions to the UR Interface framework.
    '''

    def __init__(self, path: Optional[str] = None):
        '''
        Constructor that setup a path where log files will be stored.
        '''
        self.directory: Optional[Path] = None
        self.logDir: Optional[Path] = None

        self.developer_testing_flag = False
        self.event_log_file_mode = FileMode.OVERWRITE
        self.data_log_file_mode = FileMode.OVERWRITE

        config_filename = Path(URBasic.__file__).parent / 'logConfig.xml'
        self._read_config(config_filename)

        self.get_log_path(path=path, developer_testing_flag=self.developer_testing_flag)

        self.file_log_handler = logging.FileHandler(self.directory / 'UrEvent.log', mode=self.event_log_file_mode.value)
        self.file_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.stream_log_handler = logging.StreamHandler()
        self.stream_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.file_data_log_handler = logging.FileHandler(self.directory / 'UrDataLog.csv', mode=self.data_log_file_mode.value)
        self.write_data_log_header = True

    def _read_config(self, config_filename: Path):
        log_config = parse_xml(config_filename).getroot()
        developer_mode_tag = log_config.find('developerMode')
        self.developer_testing_flag = ast.literal_eval(developer_mode_tag.text)

        event_log_config = log_config.find('eventLogConfig')
        event_file_mode_tag = event_log_config.find('fileMode')
        self.event_log_file_mode = FileMode[event_file_mode_tag.text.upper()]

        data_log_config = log_config.find('dataLogConfig')
        data_file_mode_tag = data_log_config.find('fileMode')
        self.data_log_file_mode = FileMode[data_file_mode_tag.text.upper()]

    def get_log_path(self, path: Optional[str] = None, developer_testing_flag: bool = True):
        '''
        Setup a path where log files will be stored
        Path format .\[path]\YY-mm-dd\HH-MM-SS\
        '''
        if path is None:
            path = Path(URBasic.__file__).parent / 'log'
        else:
            path = Path(*re.split(r'\\|/', path))
        if self.directory is None:
            self.logDir = path
            if developer_testing_flag:
                self.directory = path
            else:
                self.directory = path / time.strftime("%Y-%m-%d", time.localtime()) / time.strftime("%H-%M-%S", time.localtime())
            self.directory.mkdir(parents=True, exist_ok=True)
        return self.directory, self.logDir

    def add_event_logging(self, name: str = 'root', log2file: bool = True, log2console: bool = True, level: int = logging.INFO):
        '''
        Add a new event logger, the event logger can log data to a file and also output the log to the console.

        Input Parameters:
        Name (str): The name of the logger the logger name will get the extension event
        Log2file (bool): Set if the log should be stored in a log file
        Log2console (bool): Set if the log should be output to the console

        Return parameter:
        Name (str): The logger name including the extension
        '''
        name = name.replace('__', '').replace('.', '_') + 'Event'
        logger = logging.getLogger(name)
        if log2file:
            logger.addHandler(self.file_log_handler)
        if log2console:
            logger.addHandler(self.stream_log_handler)
        logger.setLevel(level)
        return name

    def add_data_logging(self, name: str = 'root'):
        '''
        Add a new data logger, the data logger will log data to a csv-file.

        Input Parameters:
        Name (str): The name of the logger the logger name will get the extension Data

        Return parameter:
        Name (str): The logger name including the extension
        '''
        name = name+'Data'
        logger = logging.getLogger(name)
        logger.addHandler(self.file_data_log_handler)
        logger.setLevel(logging.INFO)
        if self.write_data_log_header:
            logger.info('Time;ModuleName;Level;Channel;UR_Time;Value1;Value2;Value3;Value4;Value5;Value6')
            self.file_data_log_handler.setFormatter(logging.Formatter('%(asctime)s;%(name)s;%(levelname)s;%(message)s'))
            logger.addHandler(self.file_data_log_handler)
            self.write_data_log_header = False
        return name