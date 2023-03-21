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

    async def start(self):
        # ws_manager = await websockets.serve(self._connected_handler, self._ip, self._port)
        print("Def Start")
        async with websockets.serve(self._connected_handler, self._ip, self._port):
            await asyncio.Future()  # run forever


    async def _connected_handler(self, websocket):
        self._websocket = websocket
        print("Handler Start")

        while True:
            await asyncio.sleep(1)
            await self.send('Ping', '')
            print("Ping")


    async def send(self, cmd, msg):
        await self._websocket.send(
            json.dumps({'cmd': cmd, 'msg': msg})
        )

    async def receive(self):
        rx_data = json.loads(await self._websocket.recv())
        return rx_data['cmd'], rx_data['msg']

    # async def _send_ping(self, websocket):
    #     while True:
    #         await websocket.send(
    #             json.dumps({'cmd': 'Ping', 'log': ''})
    #         ) 
    #         asyncio.sleep(5)

    # async def _ws_send(self, cmd, msg):

    #     await self._websocket.send(
    #         json.dumps({'cmd': cmd, 'msg': msg})
    #     )


    # def ws_send(self, cmd: str, msg: str):
    #     self._loop.run_forever(self._ws_send(cmd, msg))




# rx_data = json.loads(await self._websocket.recv())
        # if rx_data['cmd'] == 'Start Flashing':
        #     print("Flash Started")
        
        # flash = Flasher()

        # await flash.flashModem('/dev/ttyUSB2', self._websocket)
        # task1 = asyncio.create_task(
        #     flash.flashModem('/dev/ttyUSB2', self._websocket)
        # )
        # # task2 = asyncio.create_task(self._send_ping(websocket))
        # await task1
        # # await task2
            
        # await self._websocket.send(
        #     json.dumps({'cmd': 'End Flashing', 'log': ''})
        # )