import time
import json
import socket
from ScadaDataTypes import ScadaData

class SimModel:
    IMEI                = str()
    KU                  = int()
    SWVersion           = str()
    StartProgramming    = time.time()
    EndProgramming      = time.time()
    Result              = bool()
    Error               = str()
    Command             = str()
    Message             = str()
    Info                = str()

class ScadaServer:

    def Connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # создаем сокет
        sock.bind(('127.0.0.1', 8081))  # связываем сокет с портом, где он будет ожидать сообщения
        sock.listen(10)  # указываем сколько может сокет принимать соединений
        print('Server is running, please, press ctrl+c to stop')
        while True:
            conn, addr = sock.accept()  # начинаем принимать соединения
            print('connected:', addr)  # выводим информацию о подключении
            data = conn.recv(1024)  # принимаем данные от клиента, по 1024 байт
            print(str(data))

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

            conn.send(self._data_to_send.ScadaData)  # в ответ клиенту отправляем сообщение в верхнем регистре
        conn.close()  # закрываем соединение

