import json
import sys

import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from import_res import resource_path

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

from elements.transactions import Transactions
from elements.bottom_panel import BottomPanel

from os.path import exists

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('background', 'w')
from financial.portfolio import Portfolio

pg.setConfigOption('antialias', True)  # Set to False if there is too much lag when dragging scene
from plotting.plot_widget import PlotWidget
from thread import Thread
from elements.view_asset import ViewAsset


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        try:
            self.config = json.load(open('config'))
        except:
            self.config={"currency":"BRL","inflation":"IPCA","defaultfile":"status.txt"}
            out_file = open("config", "w+")
            json.dump(self.config, out_file)

        self.datafile = self.config['defaultfile']
        self.transaction_window = Transactions(self)
        self.portfolio = Portfolio(self.config)
        self.portfolio.signalStatus.connect(lambda x: self.statusBar().showMessage(x, 100000))
        self.bottompanel = BottomPanel()
        self.load_ui()
        self.bottompanel.hide()
        self.frame.setDisabled(True)
        self.plot = PlotWidget(self.chartcombo, self.plot_title)
        # self.plot.plotItem.setLabel(axis='left', text=self.config['currency'])
        self.upper_grid.addWidget(self.plot)
        self.thr = None
        self.view = None

        if exists(self.datafile):
            self.update_thread()
        else:
            self.statusBar().showMessage('Please select transactions file to begin', 100000)

    def done(self, a):
        """
        Updates UI elements after update thread finishes processing all transactions

        """
        self.bottompanel.update_data(self.portfolio.get_pos(), self.portfolio.get_rentability_data())
        self.bottompanel.show()
        self.frame.setDisabled(False)

    def update_thread(self):
        """
        Processes all heavy tasks inside a thread, tasks are defined in self.update_data
        """

        self.thr = Thread(self.update_data, None)
        self.thr.signalStatus.connect(self.done)
        self.thr.signalStatus.connect(lambda: self.statusBar().showMessage('Done', 1000))
        self.thr.start()

    def load_ui(self):
        """Load main ui elements"""
        uic.loadUi(resource_path('ui/ui.ui'), self)
        self.setWindowIcon(QtGui.QIcon(resource_path('ui/icon.ico')))
        self.MainMenu.addAction("Open transactions file", self.open_transactions)
        self.MainMenu.addAction("Transactions", lambda: self.transaction_window.show())
        self.MainMenu.addAction("View asset", lambda: self.view_asset())
        self.MainMenu.addAction("Information", lambda: self.view_information())
        self.tabs.addTab(self.bottompanel, 'Overview')

    def view_information(self):
        """View software information"""
        self.view = QWidget()
        uic.loadUi(resource_path('ui/info.ui'), self.view)

        self.view.show()

    def view_asset(self):
        """View asset not in wallet"""
        text, ok = QInputDialog.getText(self, 'View asset', 'Asset ticker (Yahoo Finance)')
        if ok:
            self.view = ViewAsset(text)
            self.view.show()

    def open_transactions(self):
        """Manually load transactions file"""

        file = QtWidgets.QFileDialog.getOpenFileName(self, 'Select transactions file')[0]
        self.datafile = file
        print('Open {}'.format(self.datafile))
        if exists(self.datafile):
            self.update_thread()
        else:
            print('File path {} is not valid'.format(self.datafile))


    def update_data(self):
        """Tasks to be performed inside a thread, do not update gui elements here"""

        self.transaction_window.filename = self.datafile
        self.transaction_window.parse_transactions()

        self.portfolio.load_transactions(self.transaction_window.transactions)

        portfolio = self.portfolio.chart_pos()

        self.portfolio.get_pos()
        self.portfolio.get_rentability_data()

        self.plot.add_plot('Portfolio', {'Invested': [portfolio['Date'], portfolio['Invested']],
                                         'Value': [portfolio['Date'], portfolio['Value']],
                                         'Invested w/ infl.': [portfolio['Date'], portfolio['Invested_corr']]})

        rents = {'1m': [1], '6m': [6], '12m': [12], 'Total': [0]}

        for title, time in rents.items():

            v = self.portfolio.rentability(*time)
            values = {}
            for key, value in v.items():
                if key != 'DATE':
                    values["{} {}".format(key, title)] = [v['DATE'], value]

            self.plot.add_plot('Rentability {}'.format(title), values)

        stocks = self.portfolio.chart_stock()
        items = {}
        for stock, values in stocks.items():
            items[stock] = [values['Date'], values['Total']]
        self.plot.add_plot('Stocks - Total', items)

        items = {}
        for stock, values in stocks.items():
            items[stock] = [values['Date'], values['Change']]
        self.plot.add_plot('Stocks - Change', items)

        items = {}
        for stock, values in stocks.items():
            items[stock] = [values['Date'], values['Prices']]
        self.plot.add_plot('Stocks - Prices', items)

        self.statusBar().showMessage('Done', 1000)


app = QApplication(sys.argv)
a = MainWindow()
a.show()
sys.exit(app.exec_())
