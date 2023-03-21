import asyncio
import websockets
import json
from Flasher import Flasher
# from pydantic import BaseModel
from typing import Union

# class PayLoad():
#     cmd: str
#     log: Union[str, None] = None

class WebSocketServer():
    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._is_conn_established = False

    async def start(self):
        print("Def Start")
        loop = asyncio.get_running_loop()

        men = await websockets.serve(self._connected_handler, self._ip, self._port)
        
        loop.create_task(men.serve_forever())


        print("Def Start end")
        # DONT FORGET TO CLOSE


    async def _connected_handler(self, websocket):
        self._websocket = websocket
        self._is_conn_established = True
        print("Handler Start")

        while True:
            await asyncio.sleep(1)
            await self.send('Ping', '')
            print("Ping")

    async def _ws_is_connected(self):
        while not self._is_conn_established:
            await asyncio.sleep(0)
        return

    async def send(self, cmd, msg):
        await self._ws_is_connected()
        try:
            await self._websocket.send(
                json.dumps({'cmd': cmd, 'msg': msg})
            )
        except:
            print('Connection Closed')

    async def receive(self):
        await self._ws_is_connected()
        try:
            rx_data = json.loads(await self._websocket.recv())
            return rx_data['cmd'], rx_data['msg']
        except:
            raise
