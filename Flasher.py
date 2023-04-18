import sys
from ComPort import ComPort
from logger import logger
import asyncio
from async_timeout import timeout
import RPi.GPIO as gpio
import time

VERSION = '0.2.0'

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
        await self._print_msg('INFO', f'Send AT: {cmd}')
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
            res = await self._create_shell(r'\adb devices', 5)
            adb_res = res[0].decode().split('\r\n')   
            if sys.platform.startswith('linux'):
                adb_res = adb_res[0].split('\n')

            if adb_res[1] != '':
                await self._print_msg('INFO', f'Waited for ADB Devices {i} sec')
                return adb_res
            
            await asyncio.sleep(1)
        
        return adb_res

    async def _setUpModem(self):
        """Set some modem parameters"""
        cp = ComPort()
        if await self._waitForPort(cp, 15):
            # Wait untill modem starts
            await asyncio.sleep(20)
            for i in range(10):
                try:
                    resp = await self._AT_send_recv(cp, 'AT+CPCMREG=0', 20)
                    if resp == ['OK']:
                        await self._print_msg('OK', f'CPCMREG0 ok in {i} sec')

                    resp = await self._AT_send_recv(cp, 'ATE0', 20)
                    if resp == ['OK']:
                        await self._print_msg('OK', f'ATE0 ok in {i} sec')
                        
                    return True
                except Exception:
                    await self._print_msg('WARNING', 'Port error. Reopen')
                    try:
                        cp.closePort()
                    except: pass
                    await self._waitForPort(cp, 10)

                await asyncio.sleep(1)
        

    async def _setAdbMode(self):
        """Set modem ADB mode"""
        cp = ComPort()
        if await self._waitForPort(cp, 15):
            # Wait untill modem starts
            # await asyncio.sleep(20)
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
                
                except Exception:
                    await self._print_msg('WARNING', 'Port error. Reopen')
                    try:
                        cp.closePort()
                    except: pass
                    await self._waitForPort(cp, 10)

                await asyncio.sleep(1)
        
        await self._print_msg('ERROR', f'ADB was not taken on')
        return False

    async def _setBootloaderMode(self):
        """Reboot device in bootloader (fastboot) mode"""
        try:
            res = await self._create_shell(r'\adb reboot bootloader', 15)
            if res[2]:
                await self._print_msg('OK', 'SetBootloaderMode Ok')
        except Exception:
            await self._print_msg('ERROR', 'SetBootloaderMode Error')

    async def _setNormalMode(self):
        """Reboot device in normal (adb) mode"""
        try:
            res = await self._create_shell(r'\fastboot reboot', 15)
            if res[2]:
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
                    fw = await self._AT_send_recv(cp, 'at+GMR', 20)
                    if '+GMR:' in fw[0] and fw[1] == 'OK' and len(fw) == 2:
                        await self._print_msg('OK', f'FW version got ok in {i} sec')
                        await self._print_msg('INFO', f'FW version: {fw[0][6:]}')
                        return True
                
                except Exception:
                    await self._print_msg('WARNING', 'Port error. Reopen')
                    try:
                        cp.closePort()
                    except: pass
                    await self._waitForPort(cp, 10)

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
                    if fun == ['+CFUN: 1', 'OK']:
                        await self._print_msg('OK', f'FUN ok in {i} sec')
                        return True
                    elif '+CFUN' in fun[0] and fun[1] == 'OK' and len(fun) == 2 :
                        await self._print_msg('ERROR', f'Fun != 1')
                        return False
                
                except Exception:
                    await self._print_msg('WARNING', 'Port error. Reopen')
                    try:
                        cp.closePort()
                    except: pass
                    await self._waitForPort(cp, 10)

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
                    for msg in msgs[:len(msgs)-1]:
                        await self._print_msg('INFO', msg)
                    
                    return stdout, stderr, True
                
                except Exception:
                    await self._print_msg('ERROR', f'CMD {cmd} Error')
                    return '', '', False

        except asyncio.exceptions.TimeoutError: 
            await self._print_msg('ERROR', f'CMD {cmd} timeout')
            return '', '', False

    async def _fastbootFlash(self) -> bool:
        res = await self._create_shell(r'\fastboot flash aboot '  + self._fw_path + 
                                       r'\appsboot.mbn', 5)
        if not res[2]: return False
        
        await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash sbl '    + self._fw_path + 
                                       r'\sbl1.mbn',     5)
        if not res[2]: return False

        await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash tz '     + self._fw_path + 
                                       r'\tz.mbn',       5)
        if not res[2]: return False

        await self._print_msg(f'INFO', '------------------')
        
        res = await self._create_shell(r'\fastboot flash rpm '    + self._fw_path + 
                                       r'\rpm.mbn',      5)
        if not res[2]: return False

        res = await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash modem '  + self._fw_path + 
                                       r'\modem.img',    20)
        if not res[2]: return False

        res = await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash boot '   + self._fw_path + 
                                       r'\boot.img',     10)
        if not res[2]: return False

        res = await self._print_msg(f'INFO', '------------------')

        res = await self._create_shell(r'\fastboot flash system ' + self._fw_path + 
                                       r'\system.img',   30)
        if not res[2]: return False

        return True

    async def flashModem(self, comport) -> bool:
        start_time = time.time()

        self._port = comport

        await self._print_msg('INFO', f'Flasher Version: {VERSION}')

        # Take on Relay
        gpio.output(RELAY_PIN, gpio.LOW)
        await self._print_msg('INFO', f'Start flashing {self._port}')

        # Just \n in logs
        await self._print_msg('INFO', f'')
        await self._print_msg('INFO', f'-----> SETUP MODEM <-----')

        # Try send setup commands
        if not await self._setUpModem():
            return False
        
        # Just \n in logs
        await self._print_msg('INFO', f'')
        await self._print_msg('INFO', f'-----> TAKE ON ADB <-----')

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
        await self._print_msg('INFO', f'-----> FLASH MODEM <-----')

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
        await self._print_msg('INFO', f'-----> TESTS <-----')

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
    