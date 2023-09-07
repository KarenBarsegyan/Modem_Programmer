import logging
from logging.handlers import RotatingFileHandler
import sys, os


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

        log_path = '/home/pi/sim76prg_log'

        try:
            os.mkdir(f"{log_path}/")
        except: pass
        
        log_hndl = RotatingFileHandler(f"{log_path}/{name}.log", maxBytes=1000000, 
                                               backupCount=3, encoding=None, delay=0)

        log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] %(message)s - %(asctime)s'))

        self._logger.addHandler(log_hndl)

        self._indent = indent

    def info(self, msg: str):
        self._logger.info   (('%.*s' % (self._indent - len('info'), msg)) + ' ' * (self._indent - len(msg) - len('info')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(sys._getframe(1).f_lineno))
    
    def warning(self, msg: str):
        self._logger.warning(('%.*s' % (self._indent - len('warning'), msg)) + ' ' * (self._indent - len(msg) - len('warning')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(sys._getframe(1).f_lineno))

    def error(self, msg: str):
        self._logger.error  (('%.*s' % (self._indent - len('error'), msg)) + ' ' * (self._indent - len(msg) - len('error')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(sys._getframe(1).f_lineno))

    def info_no_lineo(self, msg: str, line: int):
        self._logger.info   (('%.*s' % (self._indent - len('info'), msg)) + ' ' * (self._indent - len(msg) - len('info')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(line))
    
    def warning_no_lineo(self, msg: str, line: int):
        self._logger.warning(('%.*s' % (self._indent - len('warning'), msg)) + ' ' * (self._indent - len(msg) - len('warning')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(line))

    def error_no_lineo(self, msg: str, line: int):
        self._logger.error  (('%.*s' % (self._indent - len('error'), msg)) + ' ' * (self._indent - len(msg) - len('error')) + 
                             str(sys._getframe(1).f_globals['__file__']) + 
                             ':' + str(line))


if __name__ == '__main__':
    log = logger(__name__, logger.INFO)

    log.info('Check MSG')