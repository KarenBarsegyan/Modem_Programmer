import asyncio
from Flasher import Flasher
from Websocket import WebSocketServer, logger
import signal
import RPi.GPIO as gpio

log = logger('ModemProgrammer', logger.WARNING)

async def main_thread(ws_server, flasher):
    log.info("Main Thread")

    # While true because we may receive not "Start Flashing" (any reason)
    # So we stay connected until "Start Flashing" is received or 
    # exception occurs
    while True:
        try:
            cmd, msg = await ws_server.receive()

            log.info("Main after receive")

            # Start flashing!
            if cmd == 'Start Flashing':
                log.info("Flash Started")

                await ws_server.send('Start Flashing', 'Ok')

                if await flasher.flashModem('/dev/ttyUSB2'):
                    await ws_server.send('End Flashing', 'Ok')
                else:
                    await ws_server.send('End Flashing', 'Not Ok')

        except WebSocketServer.ConnectionClosedOk:
            log.info("End of connection")
        except WebSocketServer.ConnectionClosedError:
            log.warning("End of connection with ERROR")
        except asyncio.CancelledError:
            log.info("Main thread task was canceled")
        finally:
            break


async def main():
    log.info("STARTING")

    # While true is used because we don't want to start programm each time
    # we want to flash modem. After flashing we just close all connections, delete all class objs
    # and starts waiting for websocket client again
    while True:
        # Create websocket and Flasher
        # This is nonblocking operation, but if you want to call
        # ws_server.receive() or ws_server.send() then it would be awaited 
        # until websocket client would try to connect to ws_server
        async with WebSocketServer(ip = '0.0.0.0', port = 8000) as ws_server, Flasher(ws_server) as flasher:
            await main_thread(ws_server, flasher)
            log.info("Ended async with loop")

# ctrl+c press handler
def sigint_handler(signum, frame):
    log.info('Ctrl+C was pressed')

    # Stop all tasks
    tasks = asyncio.all_tasks()
    for task in tasks:
        task.cancel()

    loop = asyncio.get_running_loop()

    # Close loop and go to exception in __main__
    try:
        loop.stop()
        log.info('Loop stopped')
    except:
        log.info('Loop stopping error')

    gpio.setwarnings(False)
    gpio.cleanup()

# Take on ctrl+c press catch
signal.signal(signal.SIGINT, sigint_handler) 


if __name__ == '__main__':
    # Create asyncio loop. Here all tasks will be sheduled
    loop = asyncio.get_event_loop()
    try:
        # Run loop
        loop.run_until_complete(main())
    except:
        # If error occurs and loop stops program drops here
        log.info('_Main_ ended')

