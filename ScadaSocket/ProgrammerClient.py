import json
import socket
from ScadaDataTypes import ScadaData

class ScadaClient:
    def __init__(self):
        data_dict = {
            "IMEI": "123456789",
            "KU": 1,
            "SWVersion": "1.0",
            "Result": True,
            "Error": "",
            "Command": "",
            "Message": "",
            "Info": ""
        }
        self._data_to_send = ScadaData(**data_dict)

        self._data_to_send.SetStartTime()

    def Send(self):
        self._data_to_send.SetEndTime()
        print(self._SendBytes(self._data_to_send.ScadaData).ScadaData)

    def _SendBytes(self, data_to_send) -> ScadaData:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create client socket
        sock.connect(('127.0.0.1', 8080))  # connect to server socket
        sock.send(data_to_send)  # send data
        data = sock.recv(1024)  # read server answer
        sock.close()  # close connection
        return ScadaData(**json.loads(data)) # return Answer in ScadaData format
