import sys
from ComPort import ComPort
from logger import logger
import asyncio
import RPi.GPIO as gpio


log = logger(__name__, logger.INFO, indent=75)

RELAY_PIN = 21

class Flasher:
    def __init__(self, websocket):
        self._flash_thread = None
        self._websocket = websocket

        self._adb_fastboot_path = '/usr/lib/android-sdk/platform-tools/'
        self._fw_path = '/home/pi/FlashData/'
        
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
        gpio.output(RELAY_PIN, gpio.HIGH)
        gpio.cleanup()
        return True

    async def _print_msg(self, level: str, msg: str):
        if level == 'INFO':
            log.info_no_lineo(msg, str(sys._getframe(1).f_lineno))
            await self._websocket.send('Log', msg)

        elif level == 'WARNING':
            log.warning_no_lineo(msg, str(sys._getframe(1).f_lineno))
            await self._websocket.send('LogWarn', msg)

        elif level == 'ERROR':
            log.error_no_lineo(msg, str(sys._getframe(1).f_lineno))
            await self._websocket.send('LogErr', msg)

        elif level == 'OK':
            log.info_no_lineo(msg, str(sys._getframe(1).f_lineno))
            await self._websocket.send('LogOk', msg)

        else:
            raise Exception('Wrong log level')

    async def _getAdbDevices(self):
        """Get list of ADB devices"""
        for i in range(30):
            try:
                proc = await asyncio.create_subprocess_shell(
                    self._adb_fastboot_path + r'\adb devices',
                    shell=True,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                adb_res = stdout.decode().split('\r\n')
            
            except Exception:
                await self._print_msg('ERROR', 'GetAdbDevices Error')
                adb_res = []

            if sys.platform.startswith('linux'):
                adb_res = adb_res[0].split('\n')

            if adb_res[1] != '':
                return adb_res
            
            await asyncio.sleep(1)

        return adb_res

    async def _setAdbMode(self, port):
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
        
        await self._print_msg('ERROR', f'ADB on {port} was not taken on')
        return False

    async def _wait_until_reboot(self, port):
        """Wait while com port is not available"""
        result = False
        for i in range(20):
            try:
                cp = ComPort()
                cp.openPort(port)
                result = True
                break
            except Exception:
                await asyncio.sleep(1)
        
        if result:
            await self._print_msg('OK', f'Flashing ended OK\n\n')
        else:
            await self._print_msg('ERROR', f'Flashing ended with Error')

    async def _setBootloaderMode(self):
        """Reboot device in bootloader (fastboot) mode"""
        try:
            proc = await asyncio.create_subprocess_shell(
                 self._adb_fastboot_path + r'\adb reboot bootloader',
                shell=True,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

        except Exception:
            await self._print_msg('ERROR', 'SetBootloaderMode Error')

    async def _setNormalMode(self):
        """Reboot device in normal (adb) mode"""
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot reboot',
                shell=True,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )   
            stdout, stderr = await proc.communicate()

        except Exception:
            await self._print_msg('ERROR', 'SetNormalMode Error')

    async def _fastbootFlashAboot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash aboot ' + self._fw_path + r'\appsboot.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            for msg in stderr.decode().split('\n'):
                await self._print_msg('INFO', msg)
            
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashAboot Error')

    async def _fastbootFlashRpm(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash rpm ' + self._fw_path + r'\rpm.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            for msg in stderr.decode().split('\n'):
                await self._print_msg('INFO', msg)

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashRpm Error')

    async def _fastbootFlashSbl(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash sbl ' + self._fw_path + r'\sbl1.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            for msg in stderr.decode().split('\n'):
                await self._print_msg('INFO', msg)
    
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashSbl Error')

    async def _fastbootFlashTz(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash tz ' + self._fw_path + r'\tz.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            for msg in stderr.decode().split('\n'):
                await self._print_msg('INFO', msg)
            
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashTz Error')

    async def _fastbootFlashModem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash modem ' + self._fw_path + r'\modem.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            for msg in stderr.decode().split('\n'):
                await self._print_msg('INFO', msg)

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashModem Error')

    async def _fastbootFlashBoot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash boot ' + self._fw_path + r'\boot.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            for msg in stderr.decode().split('\n'):
                await self._print_msg('INFO', msg)

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashBoot Error')

    async def _fastbootFlashSystem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash system ' + self._fw_path + r'\system.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            for msg in stderr.decode().split('\n'):
                await self._print_msg('INFO', msg)

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
        adb_devices = await self._getAdbDevices()

        # if adb device was found go next, otherwise return
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
        
        # Check if reboot was OK or Not OK
        await self._wait_until_reboot(self._port)

        # Take off relay
        gpio.output(RELAY_PIN, gpio.HIGH)
        
        return True


if __name__ == '__main__':
    flasher = Flasher()
    asyncio.run(flasher.flashModem('/dev/ttyUSB2'))