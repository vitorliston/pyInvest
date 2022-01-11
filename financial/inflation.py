import datetime

from scipy.interpolate import interp1d

from util import get_cpi


class Inflation():
	def __init__(self,reference):
		if reference=='IPCA':
			x,y = get_cpi()
		self.spline=interp1d(x,y,fill_value=(y[0],y[-1]),bounds_error=False)
		self.today=datetime.datetime.today().timestamp()


	def inflation_range(self,start,end):

		start=self.spline(start.timestamp())
		end=self.spline(end.timestamp())

		return (end-start)/start

	def acc_inflation(self,start):
		start=self.spline(start.timestamp())
		end=self.spline(self.today)
		return (end-start)/start


