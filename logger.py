import logging
import sys


class logger():

    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def __init__(self, name: str, level, indent = 50):

        self._logger = logging.getLogger(name)

        self._logger.setLevel(level)

        log_hndl = logging.FileHandler(f"log/{name}.log")
        log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] %(message)s - %(asctime)s'))

        self._logger.addHandler(log_hndl)

        self._indent = indent

    def info(self, msg: str):
        self._logger.info   (msg + ' ' * (self._indent - len(msg) - len('info')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(sys._getframe(1).f_lineno))
    
    def warning(self, msg: str):
        self._logger.warning(msg + ' ' * (self._indent - len(msg) - len('warning')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(sys._getframe(1).f_lineno))

    def error(self, msg: str):
        self._logger.error  (msg + ' ' * (self._indent - len(msg) - len('error')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(sys._getframe(1).f_lineno))