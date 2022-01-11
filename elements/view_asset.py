from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from import_res import resource_path

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
from plotting.asset_plot import AssetWidget
from util import get_ticker_history
from plotting.items import PlotCurveItem
import pyqtgraph as pg


class ViewAsset(QWidget):

    def __init__(self, ticker):
        super(ViewAsset, self).__init__()
        uic.loadUi(resource_path('ui/view_asset.ui'), self)
        self.history = get_ticker_history(ticker)
        data = self.history['chart']['result'][0]['indicators']['quote'][0]['close']

        last_value = 0
        new = []
        for i in range(len(data)):
            if data[i] != None:
                new.append(data[i])
                last_value = data[i]
            else:
                new.append(last_value)

        self.setWindowTitle(ticker)

        self.setWindowModality(Qt.ApplicationModal)

        self.plot = AssetWidget()

        self.plot.plotItem.setLabel(axis='left', text=self.history['chart']['result'][0]['meta']['currency'])

        self.plot_item = PlotCurveItem(self.history['chart']['result'][0]['timestamp'], new, connect='finite', pen=pg.mkPen(color=(0, 0, 0), width=3),name=ticker)

        self.plot.addItem(self.plot_item)

        self.plot_grid.addWidget(self.plot)
