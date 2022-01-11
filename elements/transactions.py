from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from import_res import resource_path

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
from .transaction_item import TransactionItem
import pandas as pd


class Transactions(QWidget):
    header = ['Entrada/Saída', 'Date', 'Movimentação', 'Produto', 'Instituição', 'Quantity', 'Preço unitário',
              'Valor da Operação', 'Ignore']

    def __init__(self, mainwindow):

        super(Transactions, self).__init__(parent=None)
        self.setWindowTitle('Transactions')
        self.mainwindow = mainwindow
        self.load_ui()
        self.transactions = None
        self.transaction_items = []
        self.filename = None

    def load_ui(self):
        self.setWindowModality(Qt.ApplicationModal)
        uic.loadUi(resource_path('ui/transactions.ui'), self)
        self.setWindowFlags(self.windowFlags() & QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)

        self.tree.setHeaderLabels(self.header)

    def load_transactions(self, message):

        self.filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Select transaction files', '.', '(*.csv *.txt')[0]
        self.mainwindow.update_thread()

    def parse_transactions(self):

        sep = '\t' if self.filename.split('.')[-1] == 'txt' else ';'

        self.transactions = self.load_file(self.filename, sep=sep)
        self.populate_table(self.transactions.columns)

    def load_file(self, filename, sep):
        transactions = pd.read_csv(filename, sep)
       # transactions = transactions.loc[(transactions['Symbol'] == 'WEGE3')].reset_index(drop=True)
        transactions['Date'] = pd.to_datetime(transactions['Date'], format='%d/%m/%Y')

        if transactions['Date'][0] > transactions['Date'].iloc[-1]:
            transactions = transactions.iloc[::-1].reset_index(drop=True)

        return transactions

    def populate_table(self, header):
        trans = self.transactions
        self.tree.setHeaderLabels(header)

        for i in range(len(trans[list(trans.keys())[0]])):
            values = {}
            for k in header:
                values[k] = trans[k][i]

            item = TransactionItem(self.tree, values, header)
            self.transaction_items.append(item)
