from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from import_res import resource_path
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
from plotting.asset_plot import AssetWidget
from financial.asset_base import Asset_base
from plotting.items import PlotCurveItem
import pyqtgraph as pg


class Asset_Window(QWidget):

	def __init__(self, stock_item: Asset_base):
		super(Asset_Window, self).__init__()
		uic.loadUi(resource_path('ui/asset_window.ui'), self)
	#	self.events=QtWidgets.QWidget()
	#	uic.loadUi(resource_path('ui/events.ui'), self.events)
		#self.viewevents.clicked.connect(self.view_events)
#		self.viewevents.hide()
		self.stock = stock_item
		self.setWindowTitle(self.stock.ticker)
		self.ticker.setText(self.stock.ticker)
		self.setWindowModality(Qt.ApplicationModal)

		self.ui_items = {}
		self.ui_grids = {'': self.names, 'RENT': self.real, 'RENT IPCA': self.ipca,
		                 'RENT IPCA DIV': self.ipcaprov}

		self.plot = AssetWidget()

		data = self.stock.chart()

		self.plot_item = PlotCurveItem(data[0], data[1], connect='finite', pen=pg.mkPen(color=(0, 0, 0), width=3))

		self.plot.addItem(self.plot_item)

		self.load_ui()
		self.layoutitems=[]

	def load_ui(self):

		for label, value in self.stock.summary().items():
			self.poslayout.addRow(QLabel(label), QLabel(str(value)))

		self.plot_grid.addWidget(self.plot)

		values = ['', 'RENT', 'RENT IPCA', 'RENT IPCA DIV']

		rentability = ['1M', '6M', '1Y', '2Y', '5Y', '10Y']
		rents = self.stock.rentability()

		for value in values:
			self.ui_items[value] = {}

			for item in rentability:
				if value == '':
					self.ui_items[value][item] = QLabel()
					#   self.ui_items[value][item].setAlignment(QtCore.Qt.AlignRight)
					self.ui_items[value][item].setText(item)


				else:
					self.ui_items[value][item] = QLabel()
					self.ui_items[value][item].setAlignment(QtCore.Qt.AlignHCenter)
					try:
						self.ui_items[value][item].setText(str(round(rents[value][item], 2)))
					except Exception as e:
						self.ui_items[value][item].setText('-')
				self.ui_grids[value].addWidget(self.ui_items[value][item])
	# def view_events(self):
	#
	# 	a = self.stock.history['chart']['result'][0]['events']['dividends']
	# 	lay=QFormLayout()
	# 	self.layoutitems.append(lay)
	# 	self.events.divlayout.addItem(lay)
	# 	i=0
	# 	for value in a.values():
	# 		lay.addRow(QLabel(datetime.datetime.fromtimestamp(value['date']).strftime("%m/%d/%Y")) ,QLabel(str(value['amount'])))
	# 		i+=1
	# 		if i==10:
	# 			i=0
	# 			lay = QFormLayout()
	# 			self.events.divlayout.addItem(lay)
	# 			self.layoutitems.append(lay)
	# 	# a = self.stock.history['chart']['result'][0]['events']['splits']
	# 	# for value in a.values():
	# 	# 	self.events.splits.addRow(QLabel(datetime.datetime.fromtimestamp(value['date']).strftime("%m/%d/%Y")) ,QLabel(str(value['numerator'] / value['denominator'])))
	#
	#
	# 	self.events.show()