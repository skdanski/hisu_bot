import os
import logging
from logging.handlers import TimedRotatingFileHandler

from util import config

class Logger:
    def __init__(self, python_file_name, logger_name, level=logging.DEBUG):
        self.python_file_name = python_file_name
        logname = "app.log"

        configuration = config.Config()
        logs_location = configuration.log_location
        Logger.time_zone = configuration.time_zone

        MYDIR = logs_location
        CHECK_FOLDER = os.path.isdir(MYDIR)
        if not CHECK_FOLDER:
            os.makedirs(MYDIR)

        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        format_string = "%(asctime)s, %(levelname)s, %(message)s"

        handler = TimedRotatingFileHandler(filename=logs_location+logname, when="midnight")
        file_format = logging.Formatter(format_string)
        handler.setFormatter(file_format)
        handler.suffix = "%Y%m%d" #%Y%m%d%H%M%S
        logger.addHandler(handler)

        self.logger = logger


    def info(self, function_name: str, log_msg: str):
        self.logger.info(self.python_file_name + ', ' + function_name + ', ' + log_msg)

    def debug(self, function_name: str, log_msg: str):
        self.logger.debug(self.python_file_name + ', ' + function_name + ', ' + log_msg)

    def warning(self, function_name: str, log_msg: str):
        self.logger.warning(self.python_file_name + ', ' + function_name + ', ' + log_msg)
        
    def error(self, function_name: str, log_msg: str):
        self.logger.error(self.python_file_name + ', ' + function_name + ', ' + log_msg)

