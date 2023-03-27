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
flash_log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] "%(message)s"'))
flash_logger.addHandler(flash_log_hndl)

RELAY_PIN = 21

class Flasher:
    def __init__(self, websocket):
        self._flash_thread = None
        self._websocket = websocket
        self._config = yaml.load(open('configuration.yml', 'r'), yaml.SafeLoader)
        
        gpio.setmode(gpio.BCM)
        gpio.setup(RELAY_PIN, gpio.OUT)
        gpio.output(RELAY_PIN, gpio.HIGH)

    def __await__(self):
        async def closure():
            return self
        return closure().__await__()
    
    async def __aenter__(self):
        await self
        return self
    
    async def __aexit__(self, type, value, traceback):
        flash_logger.info("_aexit")
        gpio.output(RELAY_PIN, gpio.HIGH)
        gpio.cleanup()
        flash_logger.info("_aexit_end")
        return True

    async def _print_msg(self, level: str, msg: str):
        if level == 'INFO':
            flash_logger.info(msg)
            await self._websocket.send('Log', msg)

        elif level == 'WARNING':
            flash_logger.warning(msg)
            await self._websocket.send('Log', msg)

        elif level == 'ERROR':
            flash_logger.error(msg)
            await self._websocket.send('Log', msg)

        else:
            raise Exception('Wrong log level')

    async def getAdbDevices(self):
        for i in range(30):
            try:
                adb_res = subprocess.Popen(
                    self._config['adb_fastboot_path'] + r'\adb devices',
                    shell=True,
                    stdout=subprocess.PIPE
                ).stdout.read().decode('utf-8').split('\r\n')
            except Exception:
                await self._print_msg('ERROR', 'GetAdbDevices Error')
                adb_res = []

            if sys.platform.startswith('linux'):
                adb_res = adb_res[0].split('\n')

            if adb_res[1] != '':
                return adb_res
            
            await asyncio.sleep(1)

        return adb_res


    async def _setAdbMode(self, port) -> bool:
        """Set modem ADB mode"""
        for i in range(30):
            try:
                cp = ComPort()
                cp.openPort(port)
                cp.sendATCommand('at+cusbadb=1')
                await asyncio.sleep(0.5)
                if 'OK' in cp.getATResponse():
                    cp.sendATCommand('at+creset')
                    await self._print_msg('INFO', f'ADB on {port} is taken on succesfully')
                    return True
            
            except Exception: pass

            await asyncio.sleep(1)
            # await self._print_msg('INFO', f'Try {i}')
        
        await self._print_msg('ERROR', f'ADB on {port} was not taken on')
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
            await self._print_msg('ERROR', 'SetBootloaderMode Error')

    async def _setNormalMode(self):
        """Reboot device in normal (adb) mode"""
        try:
            subprocess.Popen(
                self._config['adb_fastboot_path'] + r'\fastboot reboot',
                shell=True,
                stdout=subprocess.PIPE
            )
        except Exception:
            await self._print_msg('ERROR', 'SetNormalMode Error')


    async def _fastbootFlashAboot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash aboot ' + self._config['fw_path'] + r'\appsboot.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            await self._print_msg('INFO', stderr.decode())

            
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashAboot Error')

    async def _fastbootFlashRpm(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash rpm ' + self._config['fw_path'] + r'\rpm.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            await self._print_msg('INFO', stderr.decode())

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashRpm Error')

    async def _fastbootFlashSbl(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash sbl ' + self._config['fw_path'] + r'\sbl1.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            await self._print_msg('INFO', stderr.decode())
    
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashSbl Error')

    async def _fastbootFlashTz(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash tz ' + self._config['fw_path'] + r'\tz.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            await self._print_msg('INFO', stderr.decode())
            
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashTz Error')

    async def _fastbootFlashModem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash modem ' + self._config['fw_path'] + r'\modem.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            await self._print_msg('INFO', stderr.decode())

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashModem Error')

    async def _fastbootFlashBoot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash boot ' + self._config['fw_path'] + r'\boot.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            await self._print_msg('INFO', stderr.decode())

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashBoot Error')

    async def _fastbootFlashSystem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._config['adb_fastboot_path'] + r'\fastboot flash system ' + self._config['fw_path'] + r'\system.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await proc.communicate()
            await self._print_msg('INFO', stderr.decode())

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashSystem Error')

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

        # Take on Relay
        gpio.output(RELAY_PIN, gpio.LOW)
        await self._print_msg('INFO', f'Start flashing {self._port}')

        # Wait until SIM is Taken On and take on adb
        if not await self._setAdbMode(self._port):
            return False

        # Check until adb device is not foung or 30 sec what is less
        adb_devices = await self.getAdbDevices()

        # if adb was found go next, otherwise return
        if adb_devices[1] == '':
            await self._print_msg('ERROR', 'No ADB device found')
            return False
        else:
            await self._print_msg('INFO', 'ADB device found!')

        # Take on bootloader mode to get ready for flashing
        await self._setBootloaderMode()
        await asyncio.sleep(2)

        # Flash all of the data step by step
        await self._fastbootFlash()

        # Reboot in normal mode
        await self._setNormalMode()
        await asyncio.sleep(5)

        await self._print_msg('INFO', f'Stop flashing {self._port}')

        # Take off relay
        gpio.output(RELAY_PIN, gpio.HIGH)
        
        return True


if __name__ == '__main__':
    flasher = Flasher()
    asyncio.run(flasher.flashModem('/dev/ttyUSB2'))