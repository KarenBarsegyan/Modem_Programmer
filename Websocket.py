import asyncio
import logging
import websockets
import json
import sys
import signal

ws_logger = logging.getLogger(__name__)
# Set logging level
ws_logger.setLevel(logging.INFO)
ws_log_hndl = logging.StreamHandler(stream=sys.stdout)
ws_log_hndl.setFormatter(logging.Formatter(fmt='[%(levelname)s] "%(message)s" \t\t- %(filename)s:%(lineno)s - %(asctime)s'))
ws_logger.addHandler(ws_log_hndl)

class WebSocketServer():

    class ConnectionClosedOk(Exception):
        pass

    class ConnectionClosedError(Exception):
        pass


    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._is_conn_established = False

    def __await__(self):
        async def closure():
            self._server_manager = await websockets.serve(self._connected_handler, self._ip, self._port)
            await self._server_manager.start_serving()
            return self
        return closure().__await__()
    
    async def __aenter__(self):
        await self
        return self
    
    async def __aexit__(self, *args):
        ws_logger.info("_aexit")

        self._is_conn_established = False
        self._server_manager.close()
        await self._server_manager.wait_closed()

        ws_logger.info("_aexit: now its closed")

        return True

    async def _connected_handler(self, websocket):
        if self._is_conn_established == True:
            return
        self._websocket = websocket
        self._is_conn_established = True
        ping_task = asyncio.ensure_future(self._ping())

        ws_logger.info("Handler Start")

        while self._server_manager.is_serving():
            await asyncio.sleep(0)
        
        ping_task.cancel()
        ws_logger.info("End while is serving")

    async def _ping(self):
        while self._server_manager.is_serving():
            try:
                await self.send('Ping', '')
            except:
                ws_logger.warning("Connection Ping Error")
                break

            await asyncio.sleep(0.5)

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
            
        except websockets.ConnectionClosedOK:
            ws_logger.info("raise ConnectionClosedOK in send")
            raise self.ConnectionClosedOk
        except:
            ws_logger.error("raise ConnectionClosedError in send")
            raise self.ConnectionClosedError


    async def receive(self):
        await self._ws_is_connected()
        try:
            rx_data = json.loads(await self._websocket.recv())
            return rx_data['cmd'], rx_data['msg']
        
        except websockets.ConnectionClosedOK:
            ws_logger.info("Raise ConnectionClosedOK in recv")
            raise self.ConnectionClosedOk
        except:
            ws_logger.error("Raise ConnectionClosedError in recv")
            raise self.ConnectionClosedError

