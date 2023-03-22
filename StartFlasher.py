import asyncio
from Flasher import Flasher
from Websocket import WebSocketServer

async def main_thread(ws_server):
    print("Main Thread")
    flasher = Flasher()

    while True:
        cmd, msg = await ws_server.receive()

        print("Main after receive")

        if cmd == 'Start Flashing':
            print("Flash Started")

            if await flasher.flashModem('/dev/ttyUSB2', ws_server):
                await ws_server.send('End Flashing', 'Ok')
            else:
                await ws_server.send('End Flashing', 'Not Ok')


async def main():
    ws_server = WebSocketServer(ip = '0.0.0.0', port = 8000)
    
    await ws_server.start()
    await main_thread(ws_server)



if __name__ == '__main__':
    asyncio.run(main())

