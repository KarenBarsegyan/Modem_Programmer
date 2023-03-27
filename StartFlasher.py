import asyncio
from Flasher import Flasher
from Websocket import WebSocketServer
import logging
import sys


main_logger = logging.getLogger(__name__)
# Set logging level
main_logger.setLevel(logging.INFO)
main_log_hndl = logging.StreamHandler(stream=sys.stdout)
main_log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] "%(message)s" \t\t- %(filename)s:%(lineno)s - %(asctime)s'))
main_logger.addHandler(main_log_hndl)

async def main_thread(ws_server):
    main_logger.info("Main Thread")
    flasher = Flasher(ws_server)

    while True:
        try:
            cmd, msg = await ws_server.receive()

            main_logger.info("Main after receive")

            if cmd == 'Start Flashing':
                main_logger.info("Flash Started")
                await ws_server.send('Start Flashing', 'Ok')
                # await asyncio.sleep(2)
                # await ws_server.send('End Flashing', 'Ok')
                if await flasher.flashModem('/dev/ttyUSB2'):
                    await ws_server.send('End Flashing', 'Ok')
                else:
                    await ws_server.send('End Flashing', 'Not Ok')

        except WebSocketServer.ConnectionClosedOk:
            main_logger.info("End of connection")
            break
        except:
            main_logger.error("End of connection with ERROR")
            raise


async def main():
    main_logger.info("STARTING")

    async with WebSocketServer(ip = '0.0.0.0', port = 8000) as ws_server:
        try:
            await main_thread(ws_server)
        except: 
            main_logger.error("Main_thread Error")

    main_logger.info("Ended async with loop")

    

if __name__ == '__main__':
    while True:
        try:
            asyncio.run(main())

        except KeyboardInterrupt:
            main_logger.info('Keyboard Int In Main')
            break
        except:
            main_logger.error('Unknown Int In Main')


