import sys
import yaml
import subprocess
from ComPort import ComPort
import json
import asyncio


class Flasher:
    def __init__(self):
        self._flash_thread = None
        self._config = yaml.load(open('configuration.yml', 'r'), yaml.SafeLoader)

    async def getAdbDevices(self):
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

    async def getFbDevices(self):
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

    async def _setAdbMode(self, port):
        """Set modem ADB mode"""
        try:
            cp = ComPort()
            cp.openPort(port)  # неправильно сделана обработка исключений - пределать
            cp.sendATCommand('at+cusbadb=1')
            if 'OK' in cp.getATResponse():
                print(f'ADB на {port} включился успешно')
            cp.sendATCommand('at+creset')
        except Exception:
            print(f'Включение ADB на {port} не удалось')

    async def _setBootloaderMode(self):
        """Reboot device in bootloader (fastboot) mode"""
        try:
            subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\adb reboot bootloader',
                shell=True,
                stdout=subprocess.PIPE
            )
        except Exception:
            print('Couldn\'t reboot in fastboot mode!')

    async def _setNormalMode(self):
        """Reboot device in normal (adb) mode"""
        try:
            subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\fastboot reboot',
                shell=True,
                stdout=subprocess.PIPE
            )
        except Exception:
            print('Couldn\'t reboot in adb mode!')

    async def _adbReboot(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\adb reboot ',
                shell=True
            )
        except Exception:
            print('Couldn\'t reboot adb!')

    async def _fastbootFlashAboot(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash aboot ' + self._config['fw_path'] + r'\appsboot.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash aboot!')

    async def _fastbootFlashRpm(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash rpm ' + self._config['fw_path'] + r'\rpm.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash rpm!')

    async def _fastbootFlashSbl(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash sbl ' + self._config['fw_path'] + r'\sbl1.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash sbl!')

    async def _fastbootFlashTz(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash tz ' + self._config['fw_path'] + r'\tz.mbn',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash tz!')

    async def _fastbootFlashModem(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash modem ' + self._config['fw_path'] + r'\modem.img',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash modem!')

    async def _fastbootFlashBoot(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash boot ' + self._config['fw_path'] + r'\boot.img',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash boot!')

    async def _fastbootFlashSystem(self):
        try:
            subprocess.run(
                self._config['adb_fastboot_path'] + r'\fastboot flash system ' + self._config['fw_path'] + r'\system.img',
                shell=True
            )
        except Exception:
            print('Couldn\'t flash system!')

    async def _fastbootFlash(self):
        await self._fastbootFlashAboot()
        await self._fastbootFlashRpm()
        await self._fastbootFlashSbl()
        await self._fastbootFlashTz()
        await self._fastbootFlashModem()
        await self._fastbootFlashBoot()
        await self._fastbootFlashSystem()

    async def flashModem(self, comport, websocket):
        self._port = comport

        print(f'Start flashing {self._port}')
        # await websocket.send(
        #     json.dumps({'cmd': 'Log', 'log': 'Start flashing'})
        # )

        await self._setAdbMode(self._port)
        await asyncio.sleep(20)

        adb_devices = await self.getAdbDevices()
        if sys.platform.startswith('linux'):
            adb_devices = adb_devices[0].split('\n')
        
        if adb_devices[1] == '':
            print('No ADB device found')
            # await websocket.send(
            #     json.dumps({'cmd': 'Log', 'log': 'NO ADB device found'})
            # )   
            # return
        # else:
        #     await websocket.send(
        #         json.dumps({'cmd': 'Log', 'log': 'ADB device found!'})
        #     )   

        await self._setBootloaderMode()
        await asyncio.sleep(2)

        await self._fastbootFlash()

        await self._setNormalMode()
        await asyncio.sleep(5)

        print(f'Stop flashing {self._port}')
        # await websocket.send(
        #     json.dumps({'cmd': 'Log', 'log': 'Stop flashing'})
        # )


# class _FlasherThread():
#     def __init__(self, comport=''):
#         self._flasher = Flasher()
#         self._port = comport

#     def run(self) -> None:
#         print(f'Start flashing {self._port}')
#         self._flasher._setAdbMode(self._port)
#         QThread.sleep(25)

#         adb_devices = self._flasher.getAdbDevices()
#         print(adb_devices)
#         if adb_devices[1] == '':
#             print('Прошивка не удалась, выход')
#             return

#         self._flasher._setBootloaderMode()
#         QThread.sleep(2)  # временные промежутки нужно изменить (подправить под оптимальные)

#         self._flasher._fastbootFlash()

#         self._flasher._setNormalMode()
#         QThread.sleep(5)

#         print(f'Stop flashing {self._port}')



if __name__ == '__main__':
    flasher = Flasher()
    asyncio.run(flasher.flashModem('/dev/ttyUSB2'))