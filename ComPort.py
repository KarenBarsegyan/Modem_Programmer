import sys
import glob
import serial


class ComPort:
    def __init__(self):
        self._com = serial.Serial()

    def getPortsList(self) -> list:
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux'):
            ports = glob.glob('/dev/ttyUSB*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in sorted(ports):
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def openPort(self, comport: str):
        if not self._com.isOpen():
            self._com.baudrate = 115200
            self._com.port = comport
            self._com.timeout = 1
            self._com.write_timeout = 1
            try:
                self._com.open()
            except serial.SerialException:
                print('Exception : Couldn\'t open COM port')
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
    print(cp.getPortsList())
    port = input()
    cp.openPort(port)
