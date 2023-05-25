import sys
from ComPort import ComPort
from logger import logger
import asyncio
from async_timeout import timeout
import RPi.GPIO as gpio
import time
import os
import fcntl

VERSION = '1.0.4'

log = logger(__name__, logger.INFO, indent=75)
log_status = logger('FlashStatuses', logger.INFO, indent=75)

RELAY_PIN = 14

class Flasher:
    def __init__(self, websocket):
        self._flash_thread = None
        self._websocket = websocket

        # Path to ADB, Fastboot and FlashData from apt server
        self._adb_fastboot_path = '/usr/lib/android-sdk/platform-tools/'
        self._fw_path_prefix = '/home/pi/FlashData/'
        
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
                    await self._print_msg('INFO', f'Com port opened succesfully in {i} sec')
                    break
                except:
                    found = False

            await asyncio.sleep(1)
        
        if not found:
            await self._print_msg('ERROR', f'Com port not found. {secs} sec tried')

        return found

    async def _AT_send_recv(self, cp, cmd, secs):
        """Send and receive AT command"""

        cp.sendATCommand(cmd)

        await self._print_msg('INFO', f'Sending AT: {cmd}')

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
                    await self._print_msg('INFO', f'Added to response: {new_resp_split}')
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

                ansGot = True
                break

            await asyncio.sleep(1)
            time = time + 1

        if not ansGot:
            await self._print_msg('WARNING', f'AT response not gotten. {time} sec tried')

        return resp

    async def _reset_modem(self):
        await self._print_msg('WARNING', 'Port error. Power off')

        # Take off Relay
        gpio.output(RELAY_PIN, gpio.HIGH)

        await asyncio.sleep(5)

        # Take on Relay
        gpio.output(RELAY_PIN, gpio.LOW)

        await self._print_msg('INFO', 'Power on')
        
    async def _setUpModem(self) -> bool:
        """Set some modem parameters"""
        cp = ComPort()
        for cnt in range(2):
            if await self._waitForPort(cp, 15):
                # Wait untill modem starts
                await self._print_msg('INFO', f'Waiting 20 sec while AT port starts')
                await asyncio.sleep(20)
                
                for i in range(5):
                    try:
                        resp = await self._AT_send_recv(cp, 'AT', 10)
                        if resp == ['OK']:
                            await self._print_msg('OK', f'AT port check succes in {i} sec')
                            return True

                        # AT terminal starts before modem, so it will
                        # send this msg. Before calling this function you have to
                        # wait about 10-30 sec after reboot while modem is starting.
                        # But if it's not enough just try to call this function one more time  
                        if '+CME ERROR: SIM not inserted' in resp:
                            await self._print_msg('INFO', f'SIM not found. {i} sec tried')

                        if '+CPCMREG: (0-1)' in resp:
                            await self._print_msg('INFO', f'CPCMREG msg. {i} sec tried')

                    except Exception: pass

                    await asyncio.sleep(1)

            if cnt == 0:
                try:
                    cp.closePort()
                except: pass

                await self._reset_modem()

        return False

    async def _getAdbDevices(self):
        """Get list of ADB devices"""
        adb_res = []
        time = 0
        for i in range(3):
            try:
                cp = ComPort()
                if await self._waitForPort(cp, 5):
                    cp.sendATCommand('at+cusbadb=1,1')
                    cp.closePort()
            except:
                continue

            await asyncio.sleep(3)
            time += 1

            res = await self._create_shell(r'\adb devices', 10)
            adb_res = res[0].decode().split('\r\n')   
            if sys.platform.startswith('linux'):
                adb_res = adb_res[0].split('\n')

            if adb_res[1] != '':
                break
            
            await asyncio.sleep(1)
            time += 1

        if adb_res[1] == '':
            await self._print_msg('ERROR', f'No ADB device found in {time} sec')
        else:
            await self._print_msg('OK', f'ADB device found in {time} sec')
            return True
        
        return False

    async def _setBootloaderMode(self) -> bool:
        """Reboot device in bootloader (fastboot) mode"""
        try:
            res = await self._create_shell(r'\adb reboot bootloader', 30)
            if res[2]:
                await self._print_msg('OK', 'SetBootloaderMode Ok')
                return True
        except Exception:
            await self._print_msg('ERROR', 'SetBootloaderMode Error')
        
        return False

    async def _setNormalMode(self) -> bool:
        """Reboot device in normal (adb) mode"""
        try:
            res = await self._create_shell(r'\fastboot reboot', 20)
            if res[2]:
                await self._print_msg('OK', 'SetNormalMode Ok')
                return True
        except Exception:
            await self._print_msg('ERROR', 'SetNormalMode Error')

        return False

    async def _get_fw_version(self) -> bool:
        """Get firmware version of modem"""
        cp = ComPort()
        if await self._waitForPort(cp, 5):
            for i in range(5):
                try:
                    fw = await self._AT_send_recv(cp, 'at+GMR', 15)
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
        if await self._waitForPort(cp, 5):
            for i in range(5):
                try:
                    fun = await self._AT_send_recv(cp, 'at+CFUN?', 15)           
                    if fun == ['+CFUN: 1', 'OK']:
                        await self._print_msg('OK', f'FUN ok in {i} sec')
                        return True
                    elif '+CFUN' in fun[0] and fun[1] == 'OK' and len(fun) == 2 :
                        await self._print_msg('ERROR', f'Fun != 1')
                        return False
                
                except Exception: pass

                await asyncio.sleep(1)

        await self._print_msg('ERROR', f'Get fun Error')
        return False

    async def _create_shell(self, cmd: str, secs):
        try:
            async with timeout(secs):
                try:
                    proc = await asyncio.create_subprocess_shell(
                        self._adb_fastboot_path + cmd,
                        shell=True,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    msgs = stderr.decode().split('\n')
                    
                    result = True
                    for msg in msgs[:len(msgs)-1]:
                        await self._print_msg('INFO', msg)
                        if 'FAILED' in msg or 'error' in msg:
                            result = False
        
                    return stdout, stderr, result
                
                except Exception:
                    await self._print_msg('ERROR', f'CMD {cmd} Error')
                    return '', '', False

        except asyncio.exceptions.TimeoutError: 
            await self._print_msg('ERROR', f'CMD {cmd} timeout')
            return '', '', False

    async def _fastbootFlash(self) -> bool:
        res = await self._create_shell(r'\fastboot flash aboot '  + self._fw_path + 
                                       r'appsboot.mbn', 10)
        if not res[2]: return False
        
        await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash sbl '    + self._fw_path + 
                                       r'sbl1.mbn',     10)
        if not res[2]: return False

        await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash tz '     + self._fw_path + 
                                       r'tz.mbn',       10)
        if not res[2]: return False

        await self._print_msg(f'INFO', '------------------')
        
        res = await self._create_shell(r'\fastboot flash rpm '    + self._fw_path + 
                                       r'rpm.mbn',      10)
        if not res[2]: return False

        res = await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash modem '  + self._fw_path + 
                                       r'modem.img',    20)
        if not res[2]: return False

        res = await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash boot '   + self._fw_path + 
                                       r'boot.img',     10)
        if not res[2]: return False

        res = await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash system ' + self._fw_path + 
                                       r'system.img',   30)
        if not res[2]: return False

        return True

    async def flashModem(self, comport, system) -> bool:
        self._fw_path = self._fw_path_prefix + system + '/'

        start_time = time.time()
        start_time_nice_format = time.strftime("%H:%M:%S - %d.%m.%Y", time.localtime())

        self._port = comport

        await self._print_msg('INFO', f'Flasher Version: {VERSION}')

        await self._print_msg('INFO', f'Modem System: {system}')

        # Take on Relay
        gpio.output(RELAY_PIN, gpio.LOW)
        await self._print_msg('INFO', f'Start flashing at {start_time_nice_format}')

        # Just \n in logs
        await self._print_msg('INFO', f'')
        await self._print_msg('INFO', f'-----> SETUP MODEM <-----')

        # Try send setup commands
        if not await self._setUpModem():
            log_status.error(f"First Setup Modem Error. Started in {start_time_nice_format}")
            return False

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Check until adb device is not founв or timeout what is less
        if not await self._getAdbDevices():
            log_status.error(f"Get ADB devices Error. Started in {start_time_nice_format}")
            return False

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Show time from begin of flashing
        await self._print_msg('INFO', f'Time: {(time.time()-start_time):.03f} sec')

        # Just \n in logs
        await self._print_msg('INFO', f'')
        await self._print_msg('INFO', f'-----> FLASH MODEM <-----')

        # Take on bootloader mode to get ready for flashing
        if not await self._setBootloaderMode():
            log_status.error(f"Set bootloader mode Error. Started in {start_time_nice_format}")
            return False
        await asyncio.sleep(2)

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Flash all of the data step by step
        if not await self._fastbootFlash():
            log_status.error(f"Flashing Error. Started in {start_time_nice_format}")
            return False

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Show time from begin of flashing
        await self._print_msg('INFO', f'Time: {(time.time()-start_time):.03f} sec')

        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Reboot in normal mode
        if not await self._setNormalMode():
            log_status.error(f"Set Normal mode Error. Started in {start_time_nice_format}")
            return False

        # Just \n in logs
        await self._print_msg('INFO', f'')
        await self._print_msg('INFO', f'-----> SETUP MODEM <-----')

        # Try send setup commands
        if not await self._setUpModem():
            log_status.error(f"Second setup Error. Started in {start_time_nice_format}")
            return False

        # Just \n in logs
        await self._print_msg('INFO', f'')
        await self._print_msg('INFO', f'-----> TESTS <-----')

        # Get firmware version
        if not await self._get_fw_version(): 
            log_status.error(f"Get FW Error. Started in {start_time_nice_format}")
            return False
        
        # Just \n in logs
        await self._print_msg('INFO', f'')

        # Get status flag
        if not await self._get_fun(): 
            log_status.error(f"Get FUN Error. Started in {start_time_nice_format}")
            return False
        
        await asyncio.sleep(1)
        
        # Take off relay
        gpio.output(RELAY_PIN, gpio.HIGH)
        
        await self._print_msg('INFO', f'')
        await self._print_msg('OK', f'Success!')
        log_status.info(f"Success. Started in {start_time_nice_format}")

        # Show time from begin of flashing
        await self._print_msg('INFO', f'Full Time: {(time.time()-start_time):.03f} sec')
        await self._print_msg('INFO', f'')

        return True



# Tests
from Websocket import WebSocketServer
async def test():
    async with WebSocketServer(ip = '0.0.0.0', port = 8000) as ws_server, Flasher(ws_server) as flasher:
        print("Start")
        await flasher.flashModem('/dev/ttyUSB2', 'LE11B14SIM7600M22_211104')

if __name__ == '__main__':
    asyncio.run(test())
    