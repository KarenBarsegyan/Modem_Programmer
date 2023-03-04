import json
import socket
from typing import Union
from pydantic import BaseModel
import time

class ScadaData:
    class SimModel(BaseModel):
        IMEI                : str
        KU                  : int
        SWVersion           : str
        StartProgramming    : str = ''
        EndProgramming      : str = ''
        Result              : bool
        Error               : str
        Command             : str
        Message             : str
        Info                : str

    def __init__(self, **kwargs):
        self._sim_data = self.SimModel(**kwargs)

    @property
    def ScadaData(self) -> bytes:
        return bytes(self._sim_data.json().encode('ascii'))
    
    @ScadaData.setter
    def ScadaData(self, dataToSet: bytes):
        self._sim_data = json.loads(str(dataToSet))

    def SetStartTime(self):
        time_string = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        time_string = time_string[:-2] + ':' + time_string[-2:]
        self._sim_data.StartProgramming = time_string

    def SetEndTime(self):
        time_string = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        time_string = time_string[:-2] + ':' + time_string[-2:]
        self._sim_data.EndProgramming = time_string