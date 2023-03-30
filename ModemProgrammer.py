import asyncio
from Flasher import Flasher
from Websocket import WebSocketServer
import logging
import sys
import signal
import RPi.GPIO as gpio


main_logger = logging.getLogger(__name__)
# Set logging level
main_logger.setLevel(logging.WARNING)
main_log_hndl = logging.StreamHandler(stream=sys.stdout)
main_log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] "%(message)s" \t\t- %(filename)s:%(lineno)s - %(asctime)s'))
main_logger.addHandler(main_log_hndl)


async def main_thread(ws_server, flasher):
    main_logger.info("Main Thread")

    # While true because we may receive not "Start Flashing" (any reason)
    # So we stay connected until "Start Flashing" is received or 
    # exception occurs
    while True:
        try:
            cmd, msg = await ws_server.receive()

            main_logger.info("Main after receive")

            # Start flashing!
            if cmd == 'Start Flashing':
                main_logger.info("Flash Started")

                await ws_server.send('Start Flashing', 'Ok')

                if await flasher.flashModem('/dev/ttyUSB2'):
                    await ws_server.send('End Flashing', 'Ok')
                else:
                    await ws_server.send('End Flashing', 'Not Ok')

        except WebSocketServer.ConnectionClosedOk:
            main_logger.info("End of connection")
        except WebSocketServer.ConnectionClosedError:
            main_logger.warning("End of connection with ERROR")
        except asyncio.CancelledError:
            main_logger.info("Main thread task was canceled")
        finally:
            break


async def main():
    main_logger.info("STARTING")

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
            main_logger.info("Ended async with loop")

# ctrl+c press handler
def sigint_handler(signum, frame):
    main_logger.info('Ctrl+C was pressed')

    # Stop all tasks
    tasks = asyncio.all_tasks()
    for task in tasks:
        task.cancel()

    loop = asyncio.get_running_loop()

    # Close loop and go to exception in __main__
    try:
        loop.stop()
        main_logger.info('Loop stopped')
    except:
        main_logger.info('Loop stopping error')

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
        main_logger.info('_Main_ ended')

