import asyncio
import websockets
import json
from Flasher import Flasher
# from pydantic import BaseModel
from typing import Union

# class PayLoad():
#     cmd: str
#     log: Union[str, None] = None

class WebSocket():
    # def __init__():

    async def _send_ping(self, websocket):
        while True:
            await websocket.send(
                json.dumps({'cmd': 'Ping', 'log': ''})
            ) 
            asyncio.sleep(5)

    async def _echo(self, websocket):
        rx_data = json.loads(await websocket.recv())
        if rx_data['cmd'] == 'Start Flashing':
            print("Flash Started")
        
        flash = Flasher()

        await flash.flashModem('/dev/ttyUSB2', websocket)
        task1 = asyncio.create_task(
            flash.flashModem('/dev/ttyUSB2', websocket)
        )
        # task2 = asyncio.create_task(self._send_ping(websocket))
        await task1
        # await task2
            
        await websocket.send(
            json.dumps({'cmd': 'End Flashing', 'log': ''})
        )


    async def main(self):
        async with websockets.serve(self._echo, '0.0.0.0', 8000, ping_timeout = 120):
            await asyncio.Future()  # run forever
