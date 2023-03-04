import yaml
import subprocess
from ComPort import ComPort
from PyQt6.QtCore import QThread
from FtdiPort import FtdiDriver

class Flasher:
    def __init__(self):
        self._flash_thread = None
        self._config = yaml.load(open('configuration.yml', 'r'), yaml.SafeLoader)

    def getAdbDevices(self):
        try:
            adb_res = subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\adb devices',
                shell=True,
                stdout=subprocess.PIPE
            ).stdout.read().decode('utf-8').split('\r\n')
        except Exception:
            print('Exception occurred!')
            adb_res = []
        return adb_res

    def getFbDevices(self):
        try:
            fb_res = subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\fastboot devices',
                shell=True,
                stdout=subprocess.PIPE
            ).stdout.read().decode('utf-8').split('\r\n')
        except Exception:
            print('Exception occurred!')
            fb_res = []
        return fb_res

    def _setAdbMode(self, port):
        """Set modem ADB mode"""
        try:
            cp = ComPort()
            cp.openPort(port)  # неправильно сделана обработка исключений - переделать
            cp.sendATCommand('at+cusbadb=1')
            if 'OK' in cp.getATResponse():
                print(f'ADB на {port} включился успешно')
            cp.sendATCommand('at+creset')
        except Exception:
            print(f'Включение ADB на {port} не удалось')

    def _setBootloaderMode(self):
        """Reboot device in bootloader (fastboot) mode"""
        try:
            subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\adb reboot bootloader',
                shell=True,
                stdout=subprocess.PIPE
            )
        except Exception:
            print('Couldn\'t reboot in fastboot mode!')

    def _setNormalMode(self):
        """Reboot device in normal (adb) mode"""
        try:
            subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\fastboot reboot',
                shell=True,
                stdout=subprocess.PIPE
            )
        except Exception:
            print('Couldn\'t reboot in adb mode!')

    def _adbReboot(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\adb reboot ',
                shell=True
            )
        except Exception:
            print('Couldn\'t reboot adb!')

    def _fastbootFlashAboot(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash aboot ' + self._config['fw_path'] + r'\appsboot.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash aboot!')

    def _fastbootFlashRpm(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash rpm ' + self._config['fw_path'] + r'\rpm.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash rpm!')

    def _fastbootFlashSbl(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash sbl ' + self._config['fw_path'] + r'\sbl1.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash sbl!')

    def _fastbootFlashTz(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash tz ' + self._config['fw_path'] + r'\tz.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash tz!')

    def _fastbootFlashModem(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash modem ' + self._config['fw_path'] + r'\modem.img',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash modem!')

    def _fastbootFlashBoot(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash boot ' + self._config['fw_path'] + r'\boot.img',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash boot!')

    def _fastbootFlashSystem(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash system ' + self._config['fw_path'] + r'\system.img',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash system!')

    def _fastbootFlash(self):
        self._fastbootFlashAboot()
        self._fastbootFlashRpm()
        self._fastbootFlashSbl()
        self._fastbootFlashTz()
        self._fastbootFlashModem()
        self._fastbootFlashBoot()
        self._fastbootFlashSystem()

    def flashModem(self, comport='' , ftdiport=''):
        self._flash_thread = _FlasherThread(comport, ftdiport)
        self._flash_thread.start()


class _FlasherThread(QThread):
    def __init__(self, comport='', ftdiport ='', parent=None):
        QThread.__init__(self, parent)
        self._flasher = Flasher()
        self._comport = comport
        self._ftdiportUrl = ftdiport
        # self._ftdiport = FtdiDriver()
        # self._ftdiport.Config(ftdiport)

    def run(self) -> None:
        print(f'Take on Power on {self._ftdiportUrl}')
        # self._ftdiport.SetPowerPin(False)
        # QThread.sleep(5)
        # self._ftdiport.SetPowerPin(True)
        # QThread.sleep(18)

        print(f'Start flashing {self._comport}')
        self._flasher._setAdbMode(self._comport)
        QThread.sleep(25)

        adb_devices = self._flasher.getAdbDevices()
        print(adb_devices) 
        if adb_devices[1] == '': #!ERROR
            print('Прошивка не удалась, выход')
            return

        self._flasher._setBootloaderMode()
        QThread.sleep(2)  # временные промежутки нужно изменить (подправить под оптимальные)

        self._flasher._fastbootFlash()

        self._flasher._setNormalMode()
        QThread.sleep(5)

        print(f'Succesfully flashed {self._comport}')
        print(f'Take off Power on {self._ftdiportUrl}')
        # self._ftdiport.SetPowerPin(False)


from PyQt6.QtWidgets import QApplication
import sys

if __name__ == '__main__':
    flasher = Flasher()

    app = QApplication(sys.argv)

    flasher.flashModem('COM28', 'ftdi://ftdi:2232:FT5X4HI2/1')
    # flasher.flashModem('COM33', 'ftdi://ftdi:2232:FT7FLE7U/1')

    app.exec()