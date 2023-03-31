import asyncio
from logger import logger
import websockets
import json

log = logger(__name__, logger.WARNING)

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
            # Create and start websocket manager (is used to close serv in future)
            self._server_manager = await websockets.serve(self._connected_handler, self._ip, self._port)
            await self._server_manager.start_serving()
            return self
        return closure().__await__()
    
    async def __aenter__(self):
        await self
        return self
    
    async def __aexit__(self, *args):
        log.info("_aexit")

        self._is_conn_established = False
        self._server_manager.close()
        await self._server_manager.wait_closed()

        log.info("_aexit: now its closed")

        return True

    async def _connected_handler(self, websocket):
        # This 'if' makes only one connection possible
        if self._is_conn_established == True:
            return
        self._is_conn_established = True

        # Make websocket obj for calling recv and send global
        self._websocket = websocket

        # Create ping task for keepalive approove
        ping_task = asyncio.ensure_future(self._ping())

        log.info("Handler Start")

        # Wait until somebody would ask to close server
        while self._server_manager.is_serving():
            await asyncio.sleep(0)
        
        # Stop Ping task
        ping_task.cancel()
        
        log.info("End while is serving")

    async def _ping(self):
        while self._server_manager.is_serving():
            try:
                # await self.send('Ping', '')
                pong_waiter = await self._websocket.ping()
                await pong_waiter
                log.info("Pong Received")
            except:
                log.warning("Ping Error")
                break

            await asyncio.sleep(3)

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
            log.info("raise ConnectionClosedOK in send")
            raise self.ConnectionClosedOk
        except:
            log.warning("raise ConnectionClosedError in send")
            raise self.ConnectionClosedError


    async def receive(self):
        await self._ws_is_connected()
        try:
            rx_data = json.loads(await self._websocket.recv())
            return rx_data['cmd'], rx_data['msg']
        
        except websockets.ConnectionClosedOK:
            log.info("Raise ConnectionClosedOK in recv")
            raise self.ConnectionClosedOk
        except:
            log.warning("Raise ConnectionClosedError in recv")
            raise self.ConnectionClosedError

