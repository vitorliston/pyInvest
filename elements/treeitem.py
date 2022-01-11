from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *

from elements.asset_window import Asset_Window

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


class TreeWidgetItem(QTreeWidgetItem):

    def __init__(self,parent,stock):
        super(TreeWidgetItem, self).__init__(parent)

        self.asset=Asset_Window(stock)

    def __lt__(self, otherItem):

        column = self.treeWidget().sortColumn()
        try:
            return float(self.text(column)) < float(otherItem.text(column))
        except:
            return super().__lt__(otherItem)
    def raise_window(self):

        self.asset.show()







