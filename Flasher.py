import sys
import yaml
import subprocess
from ComPort import ComPort
import logging
import asyncio
import RPi.GPIO as gpio

flash_logger = logging.getLogger(__name__)
# Set logging level
flash_logger.setLevel(logging.INFO)
flash_log_hndl = logging.StreamHandler(stream=sys.stdout)
flash_log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] "%(message)s" \t\t- %(filename)s:%(lineno)s - %(asctime)s'))
flash_logger.addHandler(flash_log_hndl)

RELAY_PIN = 21

class Flasher:
    def __init__(self, websocket):
        self._flash_thread = None
        self._websocket = websocket
        self._config = yaml.load(open('configuration.yml', 'r'), yaml.SafeLoader)
        
        gpio.setmode(gpio.BCM)
        gpio.setup(RELAY_PIN, gpio.OUT)

    def __del__(self):
        gpio.output(RELAY_PIN, gpio.HIGH)
        gpio.cleanup()

    async def getAdbDevices(self):
        try:
            adb_res = subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\adb devices',
                shell=True,
                stdout=subprocess.PIPE
            ).stdout.read().decode('utf-8').split('\r\n')
        except Exception:
            flash_logger.error('GetAdbDevices Error')
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
            flash_logger.error('GetFbDevices Error')
            fb_res = []
        return fb_res

    async def _setAdbMode(self, port) -> bool:
        """Set modem ADB mode"""
        result = False
        try:
            cp = ComPort()
            cp.openPort(port)  # неправильно сделана обработка исключений - пределать
            cp.sendATCommand('at+cusbadb=1')
            if 'OK' in cp.getATResponse():
                flash_logger.info(f'ADB on {port} is taken On succesfully')
                # await self._websocket.send('Log', 'ADB is taken On succesfully')
            
            result = True
            cp.sendATCommand('at+creset')
            return result
        except Exception:
            flash_logger.info(f'Taking on ADB on {port} ended with error')
            await self._websocket.send('Log', 'ADB was not taken on with error')
            return False

    async def _setBootloaderMode(self):
        """Reboot device in bootloader (fastboot) mode"""
        try:
            subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\adb reboot bootloader',
                shell=True,
                stdout=subprocess.PIPE
            )
        except Exception:
            flash_logger.error('SetBootloaderMode Error')

    async def _setNormalMode(self):
        """Reboot device in normal (adb) mode"""
        try:
            subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\fastboot reboot',
                shell=True,
                stdout=subprocess.PIPE
            )
        except Exception:
            flash_logger.error('SetNormalMode Error')

    async def _adbReboot(self):
        try:
            # subprocess.run(
            #     self._config['adb_fastboot_path'] + r'\adb reboot ',
            #     shell=True
            # )
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\adb reboot '
            )
                # stdout=asyncio.subprocess.PIPE,
                # stderr=asyncio.subprocess.PIPE)
            await proc.wait()
        except Exception:
            flash_logger.error('AdbReboot Error')

    async def _fastbootFlashAboot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash aboot ' + self._config['fw_path'] + r'\appsboot.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            flash_logger.info(stderr.decode())
            await self._websocket.send('Log', f'  stdout [:\n{stderr.decode()}  ] end stdout')
            
        except Exception:
            flash_logger.error('FastbootFlashAboot Error')

    async def _fastbootFlashRpm(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash rpm ' + self._config['fw_path'] + r'\rpm.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            flash_logger.info(stderr.decode())
            await self._websocket.send('Log', f'  stdout [:\n{stderr.decode()}  ] end stdout')

        except Exception:
            flash_logger.error('FastbootFlashRpm Error')

    async def _fastbootFlashSbl(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash sbl ' + self._config['fw_path'] + r'\sbl1.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            flash_logger.info(stderr.decode())
            await self._websocket.send('Log', f'  stdout [:\n{stderr.decode()}  ] end stdout')

        except Exception:
            flash_logger.error('FastbootFlashSbl Error')

    async def _fastbootFlashTz(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash tz ' + self._config['fw_path'] + r'\tz.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            flash_logger.info(stderr.decode())
            await self._websocket.send('Log', f'  stdout [:\n{stderr.decode()}  ] end stdout')

        except Exception:
            flash_logger.error('FastbootFlashTz Error')

    async def _fastbootFlashModem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash modem ' + self._config['fw_path'] + r'\modem.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            flash_logger.info(stderr.decode())
            await self._websocket.send('Log', f'  stdout [:\n{stderr.decode()}  ] end stdout')

        except Exception:
            flash_logger.error('FastbootFlashModem Error')

    async def _fastbootFlashBoot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash boot ' + self._config['fw_path'] + r'\boot.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            flash_logger.info(stderr.decode())
            await self._websocket.send('Log', f'  stdout [:\n{stderr.decode()}  ] end stdout')

        except Exception:
            flash_logger.error('FastbootFlashBoot Error')

    async def _fastbootFlashSystem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash system ' + self._config['fw_path'] + r'\system.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            flash_logger.info(stderr.decode())
            await self._websocket.send('Log', f'  stdout [:\n{stderr.decode()}  ] end stdout')

        except Exception:
            flash_logger.error('FastbootFlashSystem Error')

    async def _fastbootFlash(self):
        await self._fastbootFlashAboot()
        await self._fastbootFlashRpm()
        await self._fastbootFlashSbl()
        await self._fastbootFlashTz()
        await self._fastbootFlashModem()
        await self._fastbootFlashBoot()
        await self._fastbootFlashSystem()

    async def flashModem(self, comport) -> bool:
        self._port = comport

        gpio.output(RELAY_PIN, gpio.LOW)

        flash_logger.info(f'Start flashing {self._port}')
        await self._websocket.send('Log', 'Start Flashing')


        await asyncio.sleep(15)
        if not await self._setAdbMode(self._port):
            return False
        await asyncio.sleep(20)

        adb_devices = await self.getAdbDevices()
        if sys.platform.startswith('linux'):
            adb_devices = adb_devices[0].split('\n')
        
        if adb_devices[1] == '':
            flash_logger.error('No ADB device found')
            await self._websocket.send('Log', 'No ADB device found') 
            return False
        else:
            flash_logger.info('ADB device found!')
            await self._websocket.send('Log', 'ADB device found!') 

        await self._setBootloaderMode()
        await asyncio.sleep(2)

        await self._fastbootFlash()

        await self._setNormalMode()
        await asyncio.sleep(5)

        flash_logger.info(f'Stop flashing {self._port}')
        await self._websocket.send('Log', 'Stop flashing') 

        gpio.output(RELAY_PIN, gpio.HIGH)
        
        return True


if __name__ == '__main__':
    flasher = Flasher()
    asyncio.run(flasher.flashModem('/dev/ttyUSB2'))