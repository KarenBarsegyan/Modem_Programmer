import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.resolve())+'/Sim7600-Flasher')
sys.path.append(str(pathlib.Path(__file__).parent.resolve())+'/ScadaSocket')

from MainWindow import MainWindow
from ProgrammerServer import ScadaServer
from ProgrammerClient import ScadaClient
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread


class ScadaServerWorkClass(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self._server = ScadaServer()

    def run(self) -> None:
        self._server.Connect()
        
class ScadaClientWorkClass(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self._client = ScadaClient()

    def run(self) -> None:
        while(1):
            QThread.sleep(5)
            self._client.Send()

if __name__ == '__main__':
    scada_server_thread = ScadaServerWorkClass()
    scada_server_thread.start()

    scada_client_thread = ScadaClientWorkClass()
    scada_client_thread.start()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
