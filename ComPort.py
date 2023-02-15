import sys
import glob
import serial
import yaml
# from serial.tools import list_ports
from serial.tools.list_ports import comports


class ComPort:
    def __init__(self):
        self._com = serial.Serial()
        self._config = yaml.load(open("configuration.yml"), yaml.SafeLoader)
        self._start_names = []
        for cnt in range(self._config['chip_number']):
            self._start_names.append(self._config['chip_name_%s' %(cnt+1)])

    def getPortsList(self, chipNum) -> list:
        result = []
        for port in serial.tools.list_ports.comports():
            try:
                s = serial.Serial(port.name)
                s.close()

                desc = str(port.description)
                if desc.find(self._start_names[chipNum]) >= 0: 
                    result.append(str(port.name) + " : " + str(port.description))
                    
            except (OSError, serial.SerialException):
                pass
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
    
    
import usb.core

if __name__ == '__main__':
    cp = ComPort()
    # print(cp.getPortsList(0))
    # port = input()
    # cp.openPort(port)k

    ports = serial.tools.list_ports.comports()

    for port, desc, hwid in ports:
        if desc.find("AT") > 0:
            print("{}: {} [{}]".format(port, desc, hwid))
            print(hwid[hwid.find("LOCATION") : ])

    # print(len(ports), 'ports found')

    # print(usb.core.find())

# COM14: SimTech HS-USB AT Port 9001 (COM14) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1148094C&0&0002]
# COM18: SimTech HS-USB AT Port 9001 (COM18) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1939758C&0&0002]kkk


# Port 1
# COM18: SimTech HS-USB AT Port 9001 (COM18) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1939758C&0&0002]
# COM14: SimTech HS-USB AT Port 9001 (COM14) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1148094C&0&0002]
# COM14: SimTech HS-USB AT Port 9001 (COM14) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1148094C&0&0002]
# COM14: SimTech HS-USB AT Port 9001 (COM14) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1148094C&0&0002]
# Port 2
# COM14: SimTech HS-USB AT Port 9001 (COM14) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1148094C&0&0002]
# COM14: SimTech HS-USB AT Port 9001 (COM14) [AWUSB\VID_1E0E&PID_9001&MI_02\5&1148094C&0&0002]