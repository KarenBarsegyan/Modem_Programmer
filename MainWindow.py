import yaml
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QGroupBox,
    QGridLayout,
    QPushButton
)
from PyQt6.QtCore import (
    Qt,
    QSize
)
from Workplace import Workplace
from ComPort import ComPort


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._config = yaml.load(open("configuration.yml"), yaml.SafeLoader)
        self.chipQty = self._config['chip_number']
        # настройка главного окна
        self.setWindowTitle('Программатор SIMCOM7600')
        self.resize(QSize(1280, 720))
        self._mainWidget = QWidget()
        self.setCentralWidget(self._mainWidget)
        self._mainLayout = QGridLayout()
        self._mainWidget.setLayout(self._mainLayout)

        self._cp = ComPort()  # переменная для работы со списком Com портов
        self._group = []      # список рабочих групп (рамок с подписью "Рабочее место №")
        self._wp = []         # список рабочих пространств для взаимодействия с модемом
        for i in range(0, self.chipQty):
            self._wp.append(Workplace(i))  # создание нового рабочего пространства
            self._group.append(QGroupBox())

        # заполнение главного окна
        self._uiJoin()

        self.show()

    def _uiJoin(self):
        for i in range(0, self.chipQty):
            # настройка группы и добавление в неё рабочего
            # пространства (а по факту: кастомного слоя - см. класс Workplace)
            self._group[i].setTitle('Рабочее место №{0}'.format(i+1))
            self._group[i].setLayout(self._wp[i])
            # добавление группы в главное окно
            self._mainLayout.addWidget(self._group[i], 0, i)

        self._uiAddRefreshButton()

    def _uiAddRefreshButton(self):
        self._refresh_button = QPushButton('Refresh COM port list')
        self._mainLayout.addWidget(self._refresh_button, 1, 0, 1, self.chipQty)
        self._refresh_button.clicked.connect(self._btnRefreshPortList)

    def _btnRefreshPortList(self):
        ports = self._cp.getPortsList()
        for i in range(0, self.chipQty):
            self._wp[i].uiRefreshComPortList(ports)