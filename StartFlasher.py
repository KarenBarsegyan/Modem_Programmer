import asyncio
from Flasher import Flasher
from Websocket import WebSocket



if __name__ == '__main__':
    ws_obj = WebSocket()
    asyncio.run(ws_obj.main())