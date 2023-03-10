import yaml
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QListWidget,
    QComboBox,
    QLabel,
    QTextEdit,
    QPushButton
)
from PyQt6.QtCore import (
    Qt,
    QSize
)
from ComPort import ComPort
from Flasher import Flasher, _FlasherThread
from FtdiPort import FtdiDriver

class Workplace(QVBoxLayout):
    def __init__(self, wp_number):
        super().__init__()
        self._wpnumber = wp_number  # номер текущего рп
        self._cp = ComPort()  # объект для работы с модулем COM портов
        self._ftdi = FtdiDriver()  # переменная для работы со списком FTDI портов
        self._flasher = Flasher()  # объект для прошивки модема
        self._uiAddWidgets()  # заполнение рабочего пространства

    def _uiAddWidgets(self):
        self._uiAddComPortList()
        self._uiAddFtdiList()
        self._uiAddStatusField()
        self._uiAddInstructionField()
        self._uiAddFlashButton()

    def _uiAddComPortList(self):
        self._listcomports = QListWidget()
        # comports = self._cp.getPortsList()
        # self._listcomports.addItems(comports)
        self._listcomports.setMaximumSize(QSize(640, 320))
        self.addWidget(self._listcomports)

    def _uiAddFtdiList(self):
        self._listftdiports = QListWidget()
        # ftdis = self._ftdi.getPortsList()
        # self._listftdiports.addItems(ftdis)
        self._listftdiports.setMaximumSize(QSize(640, 320))
        self.addWidget(self._listftdiports)

    def _uiAddStatusField(self):
        self._status = QLabel()
        self._status.setText('Ожидание')
        self._status.setStyleSheet('background-color: gray')
        self._status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font = self._status.font()
        font.setPointSize(20)
        self._status.setFont(font)
        self.addWidget(self._status)

    def _uiAddInstructionField(self):
        self._instructions = QTextEdit()
        self._instructions.setReadOnly(True)
        self._instructions.setText('Для начала прошивки нажмите кнопку \"Push to flash\".')
        font = self._instructions.font()
        font.setPointSize(14)
        self._instructions.setFont(font)
        self.addWidget(self._instructions)

    def _uiAddFlashButton(self):
        self._button = QPushButton('Push to flash')
        self._button.clicked.connect(self._btnFlashClickedCallback)
        self.addWidget(self._button)

    def _btnFlashClickedCallback(self):
        cp_list = self._listcomports.selectedItems()
        ftdi_list = self._listftdiports.selectedItems()
        if len(cp_list) == 0 or len(ftdi_list) == 0:
            return
        self._flasher.flashModem(cp_list[0].text(), ftdi_list[0].text())
        self.uiRefreshInstructionField("Прошивка началась...")

    def uiRefreshPortsList(self):
        com_port = self._cp.getPortsList(self._wpnumber)
        self._listcomports.clear()
        self._listcomports.addItems(com_port)

        ftdi_port = self._ftdi.getPortsList(self._wpnumber)
        self._listftdiports.clear()
        self._listftdiports.addItems(ftdi_port)
        for ftdp in ftdi_port:
            ftdiport = FtdiDriver()
            ftdiport.Config(ftdp)
            ftdiport.SetPowerPin(True)

    def uiRefreshInstructionField(self, text: str):
        self._instructions.clear()
        self._instructions.setText(text)