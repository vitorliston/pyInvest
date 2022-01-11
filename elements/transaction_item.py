from PyQt5.QtWidgets import *

class TransactionItem(QTreeWidgetItem):

	def __init__(self,parent,values,header):
		super(TransactionItem, self).__init__(parent)
		self.header=header
		self.values=values
		self.update_view()
	def update_view(self):
		for ind,column in enumerate(self.header):
			self.setText(ind,str(self.values[column]))