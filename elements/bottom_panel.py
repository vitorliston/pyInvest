from PyQt5 import QtCore, QtWidgets, uic
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from import_res import resource_path

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
from PyQt5.QtChart import QChart
from PyQt5.QtChart import QPieSeries, QChartView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from elements.treeitem import TreeWidgetItem



class BottomPanel(QWidget):

	def __init__(self, ):
		super(BottomPanel, self).__init__()

		stocks=[(120,0,0),(255,150,150)]
		acao=[(0,0,100),(140,150,255)]
		fi=[(0,100,0),(150,255,150)]
		self.colors={'BR':acao,'US':stocks,'FII':fi}
		uic.loadUi(resource_path('ui/stocks.ui'), self)
		self.ui_items = {}
		self.ui_grids = {'Nome': self.names, 'RENT': self.real, 'RENT IPCA': self.ipca}
		self.summary_labels = {}

		self.load_ui()
		self.piechart = QChart()
		self.piechart.setMargins(QMargins(0, 0, 0, 0))
		self.piechart.setContentsMargins(0, 0, 0, 0)
		self.piechart.setAnimationOptions(QChart.SeriesAnimations)
		self.piechart.legend().setVisible(True)
		self.piechart.legend().setAlignment(QtCore.Qt.AlignLeft)
		self.piechart.setAnimationDuration(250)
		chartview = QChartView(self.piechart)
		chartview.setRenderHint(QPainter.Antialiasing)
		chartview.setAlignment(Qt.AlignRight)
		self.piechart_grid.addWidget(chartview)




	    #  table_columns=['Empresa','Qtd','PM','Cotação','Valor total','Proventos','Rent. total','Rent. a.m.','Rent. a.a.','% em ações','% na carteira']

	def get_color(self,n,total,colorrnge):
		deltas=[]
		for i in range(3):
			deltas.append((colorrnge[1][i]-colorrnge[0][i])/total)

		color = [colorrnge[0][i]+deltas[i]*n for i in range(3)]

		return color

	def load_ui(self):

		self.setWindowIcon(QtGui.QIcon(resource_path('ui/icon.ico')))

		self.stock_tree.clear()
		self.stock_tree.setHeaderLabels(['Ticker', 'Qtd', 'Cost', 'Value','Net', 'Change', 'Total','Income','Type'])
		self.stock_tree.itemDoubleClicked.connect(self.onItemClicked)
		#self.stock_tree_frame.setMaximumWidth(self.stock_tree.columnCount() * 70)

	def onItemClicked(self, it, col):
		it.raise_window()


	def update_data(self,position,portfolio_data):

		for type,items in position.items():
			for ticker, stock in items.items():
				item = TreeWidgetItem(self.stock_tree, stock)
				i=0
				for label, value in stock.summary().items():
					try:
						item.setText(i, str(round(value,2)))
					except:
						item.setText(i, str(value))
					i+=1

		summary = ['N', 'Invested', 'Value', 'Net', 'Income']  # ,'Sales']
		labels={'N':'Companies', 'Invested':'Invested', 'Value':'Current value', 'Net': 'Net', 'Income':'Income'}
		values = ['Nome', 'RENT', 'RENT IPCA']
		rentability = ['1M', '6M', '1A', 'Total']  # , 'Total', 'Month', 'Year']



		portfolio_data['SUMMARY']['N'] = sum([sum([len(ite.keys())]) for type,ite in position.items()])

		for i in summary:
			label = QLabel(labels[i])
			label.setStyleSheet("font-weight: bold; color: black")

			label2 = QLabel(str(round(portfolio_data['SUMMARY'][i], 2)))

			self.summary.addRow(label, label2)
			self.summary_labels[i] = label2

		for value in values:
			self.ui_items[value] = {}

		for value in values:

			for item in rentability:
				if value == 'Nome':
					self.ui_items[value][item] = QLabel()
					#self.ui_items[value][item].setAlignment(QtCore.Qt.AlignHCenter)
					self.ui_items[value][item].setText(item)
					self.ui_items[value][item].setStyleSheet("font-weight: bold; color: black")

				else:

					self.ui_items[value][item] = QLabel()

					self.ui_items[value][item].setText(str(round(portfolio_data[value][item], 2)))

				self.ui_grids[value].addWidget(self.ui_items[value][item])



		pie_data = {}
		total = sum([sum([stock.qtd() * stock.cps for ticker, stock in ite.items()]) for type,ite in position.items()])

		for type,items in position.items():
			i=0
			for ticker, stock in items.items():
				pie_data[ticker] = [stock.qtd() * stock.cps, 100 * stock.qtd() * stock.cps / total,stock.type,self.get_color(i,len(items.keys()),self.colors[type])]
				i+=1



		series = QPieSeries()
		series.setPieSize(0.6)
		series.hovered.connect(self.slicesignal)
		for index, a in enumerate(series.slices()):
			a.setLabelArmLengthFactor(1)

		for name, value in pie_data.items():
			_slice = series.append('{}\n{}%'.format(name, round(value[1]), 1), value[0])
			_slice.setBrush(QtGui.QColor(*value[3]))



		self.piechart.addSeries(series)





	def slicesignal(self, a, b):

		if b:
			a.setExploded(True)
			a.setLabelVisible(True)

		else:
			a.setExploded(False)

			a.setLabelVisible(False)
