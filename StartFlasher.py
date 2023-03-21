import asyncio
from Flasher import Flasher
from Websocket import WebSocketServer

async def main_thread(ws_server):
    print("Main Thread")
    flasher = Flasher()

    await asyncio.sleep(5)
    print("Main after sleep 10")
    cmd, msg = await ws_server.receive()
    print(f"cmd {cmd} ; msg {msg}")
    print("Main after receive")

    if cmd == 'Start Flashing':
        print("Flash Started")

        # await flasher.flashModem('/dev/ttyUSB2', ws_server)

        await ws_server.send('End Flashing', 'Ok')
        


async def main():
    ws_server = WebSocketServer(ip = '0.0.0.0', port = 8000)
    
    print("Gather")
    await asyncio.gather(
        ws_server.start(),
        main_thread(ws_server)
    )


if __name__ == '__main__':
    asyncio.run(main())

