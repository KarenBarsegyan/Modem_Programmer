import asyncio
from Flasher import Flasher
from Websocket import WebSocketServer
import logging
import sys
import RPi.GPIO as gpio

main_logger = logging.getLogger(__name__)
# Set logging level
main_logger.setLevel(logging.ERROR)
main_log_hndl = logging.StreamHandler(stream=sys.stdout)
main_log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] %(message)s'))
main_logger.addHandler(main_log_hndl)

async def main_thread(ws_server):
    main_logger.info("Main Thread")
    flasher = Flasher()

    while True:
        try:
            cmd, msg = await ws_server.receive()

            main_logger.info("Main after receive")

            if cmd == 'Start Flashing':
                main_logger.info("Flash Started")
                await ws_server.send('Start Flashing', 'Ok')
                await asyncio.sleep(2)
                main_logger.info("Send End Flashing")
                await ws_server.send('End Flashing', 'Ok')
                # if await flasher.flashModem('/dev/ttyUSB2', ws_server):
                #     await ws_server.send('End Flashing', 'Ok')
                # else:
                #     await ws_server.send('End Flashing', 'Not Ok')
        except WebSocketServer.ConnectionClosedOk:
            main_logger.info("End of connection")
            break
        except:
            main_logger.error("End of connection with ERROR")
            raise


async def main():
    while True:
        async with WebSocketServer(ip = '0.0.0.0', port = 8000) as ws_server:
            try:
                await main_thread(ws_server)
            except:
                main_logger.error("Async With ended with error")
                break

        main_logger.info("Ended async with")
    

if __name__ == '__main__':
    # RELAY_PIN = 21
    # gpio.setmode(gpio.BCM)
    # gpio.setup(RELAY_PIN, gpio.OUT)
    # gpio.output(RELAY_PIN, gpio.LOW)
    # print("STARTING")

    try:
        asyncio.run(main())
    except:
        print("End with error")


