import sys
import serial
from serial.tools.list_ports import comports

class ComPort:
    def __init__(self):
        self._com = serial.Serial()
        self._com_name_win = ''
        self._com_name_linux = ''

    def getPortsList(self) -> list:
        result = []
        for port in serial.tools.list_ports.comports():
            desc = str(port.description)
            if sys.platform.startswith('win'):
                if desc.find(self._com_name_win) >= 0: 
                    result.append(str(port.name))  
            
            elif sys.platform.startswith('linux'):
                if desc.find(self._com_name_linux) >= 0: 
                    result.append(str(port.name)) 

        return sorted(result)

    def openPort(self, comport: str):
        if not self._com.isOpen():
            self._com.baudrate = 115200
            self._com.port = comport
            self._com.timeout = 1
            self._com.write_timeout = 1
            try:
                self._com.open()
            except serial.SerialException:
                raise
        else:
            print(comport + ' already opened')

    def closePort(self, comport: str):
        if self._com.isOpen():
            try:
                self._com.close()
            except serial.SerialException:
                print('Couldn\'t close COM port')
        else:
            print(comport + ' already closed')

    def sendATCommand(self, cmd=''):
        cmd = cmd + '\x0D'  # символ возврата каретки - нужен для воспринятия AT команды модемом
        self._com.write(cmd.encode('utf-8'))

    def getATResponse(self) -> str:
        return self._com.readall().decode('utf-8')


if __name__ == '__main__':
    cp = ComPort()
    # cp.getPortsList()
    print(cp.getPortsList())
    # port = input()
    # cp.openPort(port)
# 1E0E:9001
# 18d1:d00d