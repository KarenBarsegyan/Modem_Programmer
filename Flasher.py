import sys
from ComPort import ComPort
from logger import logger
import asyncio
import RPi.GPIO as gpio
import time

VERSION = '0.1.7'

log = logger(__name__, logger.INFO, indent=75)

RELAY_PIN = 14

class Flasher:
    def __init__(self, websocket):
        self._flash_thread = None
        self._websocket = websocket

        # Path to ADB, Fastboot and FlashData from apt server
        self._adb_fastboot_path = '/usr/lib/android-sdk/platform-tools/'
        self._fw_path = '/home/pi/FlashData/'
        
        # Relay pin setup
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
        """
        Print log in file and send log in websocket
        with corresponding level
        """
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


    async def _test(self):
        # for i in range(30):
        
        print('aaa')
        proc = await asyncio.create_subprocess_shell(
            'bash ~/Work/Modem_Programmer/while.sh ',
            shell=True,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print('bbb')

        await asyncio.sleep(3)
        await proc.terminate()
        stdout, stderr = await proc.communicate()
        print('ccc')
        print(stdout.decode().split('\n'))
        print('ddd')
        

    async def _waitForPort(self, cp, secs) -> bool:
        """Try get usb device until some found & open port"""
        found = False
        for i in range(secs):
            for port in cp.getPortsList():
                if self._port.find(port) >= 0:
                    found = True
                    break
            
            if found:
                try:
                    cp.openPort(self._port)
                    await self._print_msg('INFO', f'Waited for com port: {i} sec')
                    break
                except:
                    found = False

            await asyncio.sleep(1)
        
        if not found:
            await self._print_msg('ERROR', f'Com port not found. {secs} sec tried')

        return found

    async def _AT_send_recv(self, cp, cmd, secs):
        """Send and receive AT command"""
        cp.flushPort()
        await self._print_msg('INFO', f'Send: {cmd}')
        cp.sendATCommand(cmd)

        resp = ''
        ansGot = False
        time = 0
        for i in range(secs):
            # Try to read COM port
            # If nothing there, try after one sec
            resp_raw = cp.getATResponse()
            
            # If smth found
            if resp_raw != '':
                # Try to wait a bit more, 
                # mayby SIM is trying to send more msgs
                await asyncio.sleep(0.5)
                time = time + 0.5
                new_resp = cp.getATResponse()

                # Do it while SIM sends smth. 
                # Sometimes it can happen 2 or 3 times
                while new_resp != '':
                    await asyncio.sleep(0.5)
                    time = time + 0.5
                    resp_raw += new_resp
                    new_resp_split = new_resp.split('\r\n')
                    await self._print_msg('INFO', f'Added to resp: {new_resp_split}')
                    new_resp = cp.getATResponse()

                # Parce data: delete all \r and \n
                # Sometimes SIM sends smth like
                # "cmd \r\r\n\n cmd" so just .split(\r\n)
                # is not enough
                resp = []
                for chr in resp_raw.split('\r\n'):
                    if chr != '' and chr != '\r' and chr != '\n':
                        chr = chr.replace('\r', '')
                        chr = chr.replace('\n', '')
                        resp.append(chr)

                await self._print_msg('INFO', f'At response got in {time} sec')
                await self._print_msg('INFO', f'AT response: {resp}')   

                # AT terminal starts before modem, so it will
                # send this msg. Before calling this function you have to
                # wait about 10-30 sec after reboot while modem is starting.
                # But if it's not enough just try to call this function one more time  
                if '+CME ERROR: SIM not inserted' in resp:
                    await self._print_msg('WARNING', f'SIM not found in {time} sec')
                    return []

                ansGot = True
                break

            await asyncio.sleep(1)
            time = time + 1

        if not ansGot:
            await self._print_msg('WARNING', f'AT ans not gotten. {time} sec tried')

        return resp
    
    async def _getAdbDevices(self):
        """Get list of ADB devices"""
        for i in range(25):
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
                await self._print_msg('ERROR', 'GetAdbDevices command Error')
                adb_res = []

            if sys.platform.startswith('linux'):
                adb_res = adb_res[0].split('\n')

            if adb_res[1] != '':
                await self._print_msg('INFO', f'Waited for ADB Devices {i} sec')
                return adb_res
            
            await asyncio.sleep(1)
        
        return adb_res

    async def _setAdbMode(self):
        """Set modem ADB mode"""
        cp = ComPort()
        if await self._waitForPort(cp, 15):
            # Wait untill modem starts
            await asyncio.sleep(20)
            for i in range(10):
                try:
                    # Send ADM take on command
                    resp = await self._AT_send_recv(cp, 'at+cusbadb=1', 20)
                    if resp == ['OK'] or resp == ['at+cusbadb=1', 'OK']:
                        # If modem sends 'OK' then we can reboot it.
                        # After that modem goes in ADB mode
                        await self._print_msg('OK', f'Cusbadb ok in {i} sec')
                        resp = await self._AT_send_recv(cp, 'at+creset', 20)
                        if resp == ['OK']:
                            # If modem sends 'OK' we can start waiting until reboot
                            await self._print_msg('OK', f'Creset ok in {i} sec')
                            return True
                
                except Exception: pass

                await asyncio.sleep(1)
        
        await self._print_msg('ERROR', f'ADB was not taken on')
        return False

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
            await self._print_msg('OK', 'SetBootloaderMode Ok')
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
            await self._print_msg('OK', 'SetNormalMode Ok')
        except Exception:
            await self._print_msg('ERROR', 'SetNormalMode Error')

    async def _get_fw_version(self) -> bool:
        """Get firmware version of modem"""
        cp = ComPort()
        if await self._waitForPort(cp, 20):
            # Wait untill modem starts
            await asyncio.sleep(20)
            for i in range(20):
                try:
                    await self._print_msg('INFO', f'Start get fw')
                    fw = await self._AT_send_recv(cp, 'at+GMR', 20)
                    if '+GMR:' in fw[0] and fw[1] == 'OK' and len(fw) == 2:
                        await self._print_msg('OK', f'FW version got ok in {i} sec')
                        await self._print_msg('INFO', f'FW version: {fw[0][6:]}')
                        return True
                
                except Exception: pass

                await asyncio.sleep(1)

        await self._print_msg('ERROR', f'Get fw version Error')
        return False
    
    async def _get_fun(self) -> bool:
        """Get flag of correct\incorrect modem state"""
        cp = ComPort()
        if await self._waitForPort(cp, 10):
            # You don't have to wait here like in '_get_fw_version'
            # because modem is already started
            for i in range(20):
                try:
                    fun = await self._AT_send_recv(cp, 'at+CFUN?', 20)           
                    if fun == ['+CFUN: 1', 'OK'] :
                        await self._print_msg('OK', f'FUN ok in {i} sec')
                        return True
                    elif fun[1] == 'OK' and len(fun) == 2 :
                        await self._print_msg('ERROR', f'Fun != 1')
                        return False
                
                except Exception: pass

                await asyncio.sleep(1)

        await self._print_msg('ERROR', f'Get fun Error')
        return False

    async def _communicate(self, proc):
            stdout, stderr = await proc.communicate()
            msgs = stderr.decode().split('\n')
            for msg in msgs[:len(msgs)-1]:
                await self._print_msg('INFO', msg)

    async def _fastbootFlashAboot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash aboot ' + self._fw_path + r'\appsboot.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._communicate(proc)
            return True
            
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashAboot Error')
            return False

    async def _fastbootFlashRpm(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash rpm ' + self._fw_path + r'\rpm.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._communicate(proc)
            return True

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashRpm Error')
            return False

    async def _fastbootFlashSbl(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash sbl ' + self._fw_path + r'\sbl1.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._communicate(proc)
            return True
    
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashSbl Error')
            return False

    async def _fastbootFlashTz(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash tz ' + self._fw_path + r'\tz.mbn',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._communicate(proc)
            return True
            
        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashTz Error')
            return False

    async def _fastbootFlashModem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash modem ' + self._fw_path + r'\modem.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._communicate(proc)
            return True

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashModem Error')
            return False

    async def _fastbootFlashBoot(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash boot ' + self._fw_path + r'\boot.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._communicate(proc)
            return True

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashBoot Error')
            return False

    async def _fastbootFlashSystem(self):
        try:
            proc = await asyncio.create_subprocess_shell(
                self._adb_fastboot_path + r'\fastboot flash system ' + self._fw_path + r'\system.img',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._communicate(proc)
            return True

        except Exception:
            await self._print_msg('ERROR', 'FastbootFlashSystem Error')
            return False

    async def _fastbootFlash(self) -> bool:
        await self._print_msg(f'INFO', 'FastbootFlashAboot')
        if not await self._fastbootFlashAboot():
            await self._print_msg(f'ERROR', 'FastbootFlashAboot Error')
            return False
        await self._print_msg(f'INFO', '------------------')
        await self._print_msg(f'INFO', 'FastbootFlashSbl')
        if not await self._fastbootFlashSbl():
            await self._print_msg(f'ERROR', 'FastbootFlashSbl Error')
            return False
        await self._print_msg(f'INFO', '------------------')
        await self._print_msg(f'INFO', 'FastbootFlashTz')
        if not await self._fastbootFlashTz():
            await self._print_msg(f'ERROR', 'FastbootFlashTz Error')
            return False
        await self._print_msg(f'INFO', '------------------')
        await self._print_msg(f'INFO', 'FastbootFlashRpm')
        if not await self._fastbootFlashRpm():
            await self._print_msg(f'ERROR', 'FastbootFlashRpm Error')
            return False
        await self._print_msg(f'INFO', '------------------')
        await self._print_msg(f'INFO', 'FastbootFlashModem')
        if not await self._fastbootFlashModem():
            await self._print_msg(f'ERROR', 'FastbootFlashModem Error')
            return False
        await self._print_msg(f'INFO', '------------------')
        await self._print_msg(f'INFO', 'FastbootFlashBoot')
        if not await self._fastbootFlashBoot():
            await self._print_msg(f'ERROR', 'FastbootFlashBoot Error')
            return False
        await self._print_msg(f'INFO', '------------------')
        await self._print_msg(f'INFO', 'FastbootFlashSystem')
        if not await self._fastbootFlashSystem():
            await self._print_msg(f'ERROR', 'FastbootFlashSystem Error')
            return False
        return True

    async def flashModem(self, comport) -> bool:
        start_time = time.time()

        self._port = comport

        # print('lol')
        # await self._test()
        # print('kek')

        await self._print_msg('INFO', f'Flasher Version: {VERSION}')

        # Take on Relay
        gpio.output(RELAY_PIN, gpio.LOW)
        await self._print_msg('INFO', f'Start flashing {self._port}')

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Try set ADB mode
        if not await self._setAdbMode():
            return False

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Check until adb device is not founв or timeout what is less
        adb_devices = await self._getAdbDevices()

        # if adb device was found go next, otherwise return
        if adb_devices[1] == '':
            await self._print_msg('ERROR', f'No ADB device found')
            return False
        else:
            await self._print_msg('OK', 'ADB device found!')
        
        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Show time from begin of flashing
        await self._print_msg('INFO', f'Time: {(time.time()-start_time):.03f} sec')

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Take on bootloader mode to get ready for flashing
        await self._setBootloaderMode()
        await asyncio.sleep(2)

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Flash all of the data step by step
        if not await self._fastbootFlash():
            return False

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Show time from begin of flashing
        await self._print_msg('INFO', f'Time: {(time.time()-start_time):.03f} sec')

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Reboot in normal mode
        await self._setNormalMode()

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Get firmware version
        if not await self._get_fw_version(): 
            return False
        
        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Get status flag
        if not await self._get_fun(): 
            return False
        
        await asyncio.sleep(1)
        
        # Take off relay
        gpio.output(RELAY_PIN, gpio.HIGH)
        
        await self._print_msg('INFO', f'')
        await self._print_msg('OK', f'Success!')

        # Show time from begin of flashing
        await self._print_msg('INFO', f'Full Time: {(time.time()-start_time):.03f} sec')
        await self._print_msg('INFO', f'')

        return True



# Tests
from Websocket import WebSocketServer
async def test():
    async with WebSocketServer(ip = '0.0.0.0', port = 8000) as ws_server, Flasher(ws_server) as flasher:
        await flasher.flashModem('/dev/ttyUSB2')

if __name__ == '__main__':
    asyncio.run(test())
    