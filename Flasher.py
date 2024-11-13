import sys
from ComPort import ComPort
from logger import logger
import asyncio
from async_timeout import timeout
import RPi.GPIO as gpio
import time

VERSION = '1.2.0'

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

    async def _waitForPort(self, cp, tries) -> bool:
        """Try get usb device until some found & open port"""

        await self._print_msg('INFO', f'< Wait for com port >')
        start_time = time.time()

        found = False
        for i in range(tries):
            for port in cp.getPortsList():
                if self._port.find(port) >= 0:
                    found = True
                    break
            
            if found:
                try:
                    cp.openPort(self._port)
                    await self._print_msg('INFO', f'Com port opened succesfully in {(time.time() - start_time):.03f} sec')
                    break
                except:
                    found = False

            await asyncio.sleep(1)
        
        if not found:
            await self._print_msg('ERROR', f'Com port not found. {(time.time() - start_time):.03f} sec tried')

        return found

    async def _AT_send_recv(self, cp, cmd, tries):
        """Send and receive AT command"""

        await self._print_msg('INFO', f'< AT send and receive ans >')
        start_time = time.time()

        cp.sendATCommand(cmd)

        await self._print_msg('INFO', f'Sending AT: \"{cmd}\"')

        resp = ''
        ansGot = False
        for i in range(tries):
            # Try to read COM port
            # If nothing there, try after one sec
            resp_raw = cp.getATResponse()
            
            # If smth found
            if resp_raw != '':
                # Try to wait a bit more, 
                # mayby SIM is trying to send more msgs
                await asyncio.sleep(0.5)
                new_resp = cp.getATResponse()

                # Do it while SIM sends smth. 
                # Sometimes it can happen 2 or 3 times
                while new_resp != '':
                    await asyncio.sleep(0.5)
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

                await self._print_msg('INFO', f'At response got in {(time.time() - start_time):.03f} sec')
                await self._print_msg('INFO', f'AT response: {resp}')   

                ansGot = True
                break

            await asyncio.sleep(1)

        if not ansGot:
            await self._print_msg('WARNING', f'AT response not gotten. {(time.time() - start_time):.03f} sec tried')

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
        await self._print_msg('INFO', f'< Setup Modem >')
        start_time = time.time()

        for cnt in range(1):
            # Wait untill modem starts
            await self._print_msg('INFO', f'Waiting 25 sec while AT port starts')
            await asyncio.sleep(25)
            cp = ComPort()
            if await self._waitForPort(cp, 5):
                for i in range(3):
                    try:
                        resp = await self._AT_send_recv(cp, 'AT', 3)
                        await self._print_msg('INFO', f'AT')
                        if resp == ['OK']:
                            await self._print_msg('OK', f'AT port check succes in {(time.time() - start_time):.03f} sec')
                            return True

                        # AT terminal starts before modem, so it will
                        # send this msg. Before calling this function you have to
                        # wait about 10-30 sec after reboot while modem is starting.
                        # But if it's not enough just try to call this function one more time  
                        if '+CME ERROR: SIM not inserted' in resp:
                            await self._print_msg('INFO', f'SIM not found. {(time.time() - start_time):.03f} sec tried')

                    except Exception: pass
            
            await self._print_msg('INFO', f'Close port')
            cp.closePort()
            await asyncio.sleep(1)
        return False

    async def _setAdbMode(self):
        """Get list of ADB devices"""
        await self._print_msg('INFO', f'< Get ADB Devices >')
        start_time = time.time()

        adb_res = []
        for i in range(3):
            try:
                cp = ComPort()
                if await self._waitForPort(cp, 5):
                    cp.sendATCommand('at+cusbadb=1,1')
                    cp.closePort()
            except:
                continue

            await asyncio.sleep(3)

            res = await self._create_shell(r'\adb devices', 10)
            adb_res = res[0].decode().split('\r\n')   
            if sys.platform.startswith('linux'):
                adb_res = adb_res[0].split('\n')

            if adb_res[1] != '':
                break
            
            await asyncio.sleep(1)

        if adb_res[1] == '':
            await self._print_msg('ERROR', f'No ADB device found in {(time.time() - start_time):.03f} sec')
        else:
            await self._print_msg('OK', f'ADB device found in {(time.time() - start_time):.03f} sec')
            return True
        
        return False

    async def _setBootloaderMode(self) -> bool:
        """Reboot device in bootloader (fastboot) mode"""
        await self._print_msg('INFO', f'< Set bootloader mode >')
        for i in range(3):
            try:
                res = await self._create_shell(r'\adb reboot bootloader', 30)
                if res[2]:
                    await self._print_msg('OK', 'SetBootloaderMode Ok')
                    return True
            except Exception:
                await self._print_msg('ERROR', 'SetBootloaderMode Error')

            await asyncio.sleep(1)

        return False

    async def _setNormalModeFastboot(self) -> bool:
        """Reboot device in normal mode"""
        await self._print_msg('INFO', f'< Set normal mode from fastboot>')
        for i in range(3):
            try:
                res = await self._create_shell(r'\fastboot reboot', 20)
                if res[2]:
                    await self._print_msg('OK', 'SetNormalMode from fastboot Ok')
                    return True
            except Exception:
                await self._print_msg('ERROR', 'SetNormalMode from fastboot Error')

            await asyncio.sleep(1)

        return False
        
    async def _setNormalModeADB(self) -> bool:
        """Reboot device in normal mode"""
        await self._print_msg('INFO', f'< Set normal mode from adb >')
        for i in range(3):
            try:
                res = await self._create_shell(r'\adb reboot', 20)
                if res[2]:
                    await self._print_msg('OK', 'SetNormalMode from adb Ok')
                    return True
            except Exception:
                await self._print_msg('ERROR', 'SetNormalMode from adb Error')

            await asyncio.sleep(1)

        return False
    
    async def _get_fw_version(self) -> bool:
        """Get firmware version of modem"""
        await self._print_msg('INFO', f'< Get FW version >')
        start_time = time.time()

        for i in range(5):
            cp = ComPort()
            if await self._waitForPort(cp, 5):
                try:
                    fw = await self._AT_send_recv(cp, 'at+GMR', 15)
                    if '+GMR:' in fw[0] and fw[1] == 'OK' and len(fw) == 2:
                        await self._print_msg('OK', f'FW version got ok in {(time.time() - start_time):.03f} sec')
                        await self._print_msg('INFO', f'FW version: {fw[0][6:]}')
                        return True
                
                except Exception: pass

            cp.closePort()
            await asyncio.sleep(1)

        await self._print_msg('ERROR', f'Get fw version Error. {(time.time() - start_time):.03f} sec tried')
        return False
    
    async def _get_fun(self) -> bool:
        """Get flag of correct\incorrect modem state"""
        await self._print_msg('INFO', f'< Get FUN >')
        start_time = time.time()
        
        for i in range(5):
            cp = ComPort()
            if await self._waitForPort(cp, 5):
                try:
                    fun = await self._AT_send_recv(cp, 'at+CFUN?', 15)           
                    if fun == ['+CFUN: 1', 'OK']:
                        await self._print_msg('OK', f'FUN ok in {(time.time() - start_time):.03f} sec')
                        return True
                    elif '+CFUN' in fun[0] and fun[1] == 'OK' and len(fun) == 2 :
                        await self._print_msg('ERROR', f'Fun != 1 in {(time.time() - start_time):.03f} sec')
                        return False
                
                except Exception: pass

            cp.closePort()
            await asyncio.sleep(1)

        await self._print_msg('ERROR', f'Get fun Error. {(time.time() - start_time):.03f} sec tried')
        return False

    async def _create_shell(self, cmd: str, secs):
        cmd_log = ''
        if len(cmd) > 25:
            cmd_log = f'\"...{cmd[-25:]}\"'
        else:
            cmd_log = f'\"{cmd}\"'

        await self._print_msg('INFO', f'< Exec: {cmd_log}>')

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
                    firststr = True
                    for msg in msgs[:len(msgs)-1]:
                        if firststr:
                            firststr = False
                            await self._print_msg('INFO', 'CMD Stderr:')

                        await self._print_msg('INFO', msg)
                        if 'FAILED' in msg or 'error' in msg:
                            result = False

                    msgs = stdout.decode().split('\n')
                    firststr = True
                    for msg in msgs[:len(msgs)-1]:
                        if firststr:
                            firststr = False
                            await self._print_msg('INFO', 'CMD Stdout:')
                    
                        await self._print_msg('INFO', msg)
        
                    if not result:
                        await self._print_msg('ERROR', f'CMD {cmd_log} Error')

                    return stdout, stderr, result
                
                except Exception:
                    await self._print_msg('ERROR', f'CMD {cmd_log} Error')
                    return '', '', False

        except asyncio.exceptions.TimeoutError: 
            await self._print_msg('ERROR', f'CMD {cmd_log} timeout')
            return '', '', False

    async def _fastboot_cmd(self, cmd, tries):
        for i in range(3):
            res = await self._create_shell(cmd, tries)
            if res[2]: 
                return True
            else: 
                await asyncio.sleep(1)
        
        await self._print_msg(f'ERROR', 'Fastboot Error')
        return False

    async def _fastbootFlash(self) -> bool:
        if not await self._fastboot_cmd(r'\fastboot flash aboot '  + self._fw_path + 
                                        r'appsboot.mbn', 10): return False
        
        await self._print_msg(f'INFO', '------------------')

        if not await self._fastboot_cmd(r'\fastboot flash sbl '    + self._fw_path + 
                                        r'sbl1.mbn',     10): return False

        await self._print_msg(f'INFO', '------------------')

        if not await self._fastboot_cmd(r'\fastboot flash tz '     + self._fw_path + 
                                        r'tz.mbn',       10): return False

        await self._print_msg(f'INFO', '------------------')
        
        if not await self._fastboot_cmd(r'\fastboot flash rpm '    + self._fw_path + 
                                        r'rpm.mbn',      10): return False

        await self._print_msg(f'INFO', '------------------')

        if not await self._fastboot_cmd(r'\fastboot flash modem '  + self._fw_path + 
                                        r'modem.img',    20): return False

        await self._print_msg(f'INFO', '------------------')

        if not await self._fastboot_cmd(r'\fastboot flash boot '   + self._fw_path + 
                                        r'boot.img',     10): return False

        await self._print_msg(f'INFO', '------------------')

        if not await self._fastboot_cmd(r'\fastboot flash system ' + self._fw_path + 
                                        r'system.img',   30): return False

        return True

    async def _writeFactoryNum(self):
        """Write Factory number"""
        await self._print_msg('INFO', f'< Write factory number >')
        try:
            res = await self._create_shell(r'\adb push factory.cfg /data', 30)
            if res[2]:
                await self._print_msg('OK', 'Factory number written Ok')
                return True
        except Exception:
            await self._print_msg('ERROR', 'Factory number write Error')
        
        return False

    async def flashModem(self, comport, system, factoryNum) -> bool:
        self._fw_path = self._fw_path_prefix + system + '/'
        start_time = time.time()
        start_time_nice_format = time.strftime("%H:%M:%S - %d.%m.%Y", time.localtime())
        self._port = comport

        model_id = ''
        serial_num = ''

        model_id = factoryNum[:factoryNum.find('#')]
        factoryNum = factoryNum[factoryNum.find('#') + 1:]
        serial_num = factoryNum[:factoryNum.find('#')]
        factoryNum = factoryNum[factoryNum.find('#') + 1:]
        modem_type = factoryNum[:factoryNum.find('#')]

        perform_tests = False
        if factoryNum[factoryNum.find('#') + 1:] == '1':
            perform_tests = True
                

        with open(f'factory.cfg', 'w') as file:
            file.write(model_id)
            file.write('\n')
            file.write(serial_num)


        # -----> INFO <-----

        await self._print_msg('INFO', f'Flasher Version: {VERSION}')
        await self._print_msg('INFO', f'Modem System: {system}')
        await self._print_msg('INFO', f'Modem Type: {modem_type}')
        await self._print_msg('INFO', f'Perform Tests: {perform_tests}')
        await self._print_msg('INFO', f'{model_id}')
        await self._print_msg('INFO', f'{serial_num}')
        # Take on Relay
        gpio.output(RELAY_PIN, gpio.LOW)
        await self._print_msg('INFO', f'Start flashing at {start_time_nice_format}')

        await self._print_msg('INFO', f'')

        # -----> END INFO <-----



        # -----> FLASH MODEM <-----

        await self._print_msg('INFO', f'-----> FLASH MODEM <-----')
        await self._print_msg('INFO', f'') 
        flash_modem_start_time = time.time()

        # Try send setup commands
        if not await self._setUpModem():
            log_status.error(f"First Setup Modem Error. Started in {start_time_nice_format}")
            return False

        await self._print_msg('INFO', f'')

        # Check until adb device is not found or timeout what is less
        if not await self._setAdbMode():
            log_status.error(f"First get ADB devices Error. Started in {start_time_nice_format}")
            return False

        await self._print_msg('INFO', f'')

        # Show time from begin of flashing
        await self._print_msg('INFO', f'Time: {(time.time()-start_time):.03f} sec')

        # Take on bootloader mode to get ready for flashing
        if not await self._setBootloaderMode():
            log_status.error(f"Set bootloader mode Error. Started in {start_time_nice_format}")
            return False

        await self._print_msg('INFO', f'')

        # Flash all of the data step by step
        if not await self._fastbootFlash():
            log_status.error(f"Flashing Error. Started in {start_time_nice_format}")
            return False

        await self._print_msg('INFO', f'')

        # Reboot in normal mode
        if not await self._setNormalModeFastboot():
            log_status.error(f"Set Normal mode from fastboot Error. Started in {start_time_nice_format}")
            return False

        await self._print_msg('INFO', f'')

        await self._print_msg('INFO', f'Flash modem time: {(time.time()-flash_modem_start_time):.03f} sec')
        
        await self._print_msg('INFO', f'')

        # -----> FLASH SYSTEM END <-----



        # -----> WRITE FACTORY NUM <-----

        if modem_type != 'Retrofit':
            await self._print_msg('INFO', f'-----> WRITE FACTORY NUM <-----')
            await self._print_msg('INFO', f'')
            write_factory_num_start_time = time.time()

            # Try send setup commands
            if not await self._setUpModem():
                log_status.error(f"Second setup Error. Started in {start_time_nice_format}")
                return False
            
            await self._print_msg('INFO', f'')
            
            # Check until adb device is not found or timeout what is less
            if not await self._setAdbMode():
                log_status.error(f"Second get ADB devices Error. Started in {start_time_nice_format}")
                return False
            
            await self._print_msg('INFO', f'')
            
            if not await self._writeFactoryNum():
                log_status.error(f"Factory Num write Error. Started in {start_time_nice_format}")
                return False
            
            await self._print_msg('INFO', f'')
            await self._print_msg('INFO', f'Wait 3 sec') 
            await asyncio.sleep(3)
            await self._print_msg('INFO', f'')
            
            if not await self._setNormalModeADB():
                log_status.error(f"Set Normal mode from ADB Error. Started in {start_time_nice_format}")
                return False
            
            await self._print_msg('INFO', f'')

            await self._print_msg('INFO', f'Write factory num time: {(time.time()-write_factory_num_start_time):.03f} sec')

            await self._print_msg('INFO', f'')

            if not perform_tests:
                await self._print_msg('INFO', f'Wait 3 sec') 
                await asyncio.sleep(3)
                await self._print_msg('INFO', f'')

        # -----> WRITE FACTORY NUM END <-----




        # -----> TEST MODEM <-----

        if perform_tests:
            await self._print_msg('INFO', f'-----> TESTS <-----')
            await self._print_msg('INFO', f'')
            test_modem_start_time = time.time()

            # Try send setup commands
            if not await self._setUpModem():
                log_status.error(f"Third setup Error. Started in {start_time_nice_format}")
                return False

            await self._print_msg('INFO', f'')

            # Get firmware version
            if not await self._get_fw_version(): 
                log_status.error(f"Get FW Error. Started in {start_time_nice_format}")
                return False
            
            await self._print_msg('INFO', f'')

            # Get status flag
            if not await self._get_fun(): 
                log_status.error(f"Get FUN Error. Started in {start_time_nice_format}")
                return False
            
            await self._print_msg('INFO', f'')

            await self._print_msg('INFO', f'Test modem time: {(time.time()-test_modem_start_time):.03f} sec')

            await self._print_msg('INFO', f'')

            await asyncio.sleep(1)

        # -----> TEST MODEM END <-----


        
        # Take off relay
        gpio.output(RELAY_PIN, gpio.HIGH)
        
        await self._print_msg('OK', f'Success!')
        log_status.info(f"Success. Started in {start_time_nice_format}")


        # Show time from begin of flashing
        await self._print_msg('INFO', f'Full Time: {(time.time()-start_time):.03f} sec')
        await self._print_msg('INFO', f'')
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
    