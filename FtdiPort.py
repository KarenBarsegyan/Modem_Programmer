from pyftdi.gpio import GpioAsyncController
from pyftdi.ftdi import Ftdi
import yaml
from time import sleep

class FtdiDriver:
    def __init__(self):
        self._config = yaml.load(open('configuration.yml', 'r'), yaml.SafeLoader)

        self._outputPinMask = 1 << int(self._config['ftdi_output_pin_num'])
        self._inputPinMask  = 1 << int(self._config['ftdi_input_pin_num'])
        self._ftdi = GpioAsyncController()

    def Config(self, url):
        # for cnt in range(self._config['chip_number']):
        #     self._ftdis.append(GpioAsyncController())

        # Print configured fdtis
        cnt = 0
        try:
            self._ftdi.configure(url, direction = self._outputPinMask)
            # self._ftdis[cnt].configure(self._config[('ftdii_url_%s' %(cnt+1))],
            #                             direction=0x01)
            # print(("Configured FTDI №%s :" % (cnt+1)) + (self._config[('ftdii_url_%s' %(cnt+1))]))
        except:
            print("Error Initializing FTDI")
        
        # Set default output state. It is 0 here
        # self.SetPowerPin(cnt, False)

    def getPortsList(self, chipNumber) -> list:
        result = []
        try:
            devices = Ftdi.list_devices()
            # print(devices)
            for dev in devices:
                ftdiNameString = str('ftdi://ftdi:2232:' + dev[0][4] + "/1")
                savedName = str(self._config[('ftdii_url_%s' %(chipNumber+1))])
                if savedName.find(ftdiNameString) >= 0:
                    result.append(ftdiNameString)

        except:
            print("No FTDI connected")

        return sorted(result)

    def ReadEnablePin(self, ftdiNum) -> bool:
        return (self._ftdi.read() & self._inputPinMask) == self._inputPinMask
    
    def SetPowerPin(self, pinState : bool):
        try:
            if (pinState):
                self._ftdi.write(self._outputPinMask)
            else:
                self._ftdi.write(0x00)
        except:
            print("FTDI Write error")
            

if __name__ == '__main__':
    f = FtdiDriver()
    sleep(1)
    f.Config("ftdi://ftdi:2232:FT5X4HI2/1")
    f.SetPowerPin(True)