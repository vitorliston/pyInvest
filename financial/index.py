import numpy as np

from util import *


class Index():

	def __init__(self, index):
		self.index=index
		self.history()

	@property
	def price(self):
		return round(self.history()['chart']['result'][0]['indicators']['quote'][0]['close'][-1], 2)

	@lru_cache(maxsize=128)
	def history(self):

		return get_ticker_history(self.index)

	def price_at_date(self, date):
		his = self.history()
		values, dates = his['chart']['result'][0]['indicators']['quote'][0]['close'], his['chart']['result'][0]['timestamp']

		index = (np.abs(np.array(dates) - date.timestamp())).argmin()

		if values[index] == None:
			for i in range(1, 20):
				a = values[index - i]
				if a != None:
					return a

		return values[index]

