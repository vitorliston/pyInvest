import datetime
from functools import partial

import json
import numpy as np
import pyqtgraph as pg
import pytz
import requests
import yfinance as yahoo
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pandas import DataFrame, Series, date_range, to_datetime, Timestamp, Timedelta, isnull
from pandas import concat, read_json, offsets, read_csv
from plot import PlotWidget, PlotCurveItem
from scipy.optimize import curve_fit

from thread import Worker

UNIX_EPOCH_naive = datetime.datetime(1970, 1, 1, 0, 0)  # offset-naive datetime
UNIX_EPOCH_offset_aware = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=pytz.utc)  # offset-aware datetime
UNIX_EPOCH = UNIX_EPOCH_naive

TS_MULT_us = 1e6


def today():
	"""
	Gets current date as Timestamp rounded to the day
	"""
	return Timestamp.today().round('d')


def strptime(date_string, format='%Y-%m-%d'):
	"""
	Parses string representation of Timstamp to Timestamp object rounded to the day
	"""
	return to_datetime(date_string, format=format).round('d')


def linear_fit(x, a, b):
	"""
	Linear function used to fit CPI data
	"""
	return a * x + b


cpi_ibge_url = 'https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{0}/variaveis/2266?localidades=N1[all]'


def get_cpi_ibge(start_date=None, end_date=None):
	"""
	Retrieves the CPI (Consumer Price Index) from the IBGE API.

	Parameters
	----------
	start_date : Timestamp, str. optional
		Table start date. The default is None which fetches from the earliest possible date.
	end_date : Timestamp, str. optional
		Table end date. The default is None which fetches until most current date.

	Returns
	-------
	cpi : Series
		TimdeIndexed CPI data from given time frame.

	"""

	earliest = strptime('1979-12-1')

	if start_date == None:
		start_date = earliest
	elif start_date < earliest:
		raise ValueError(f"Earliest possible date from IBGE source is {earliest.strftime('%Y-%m')}")

	# rounds date to month start
	start_date = start_date.to_period('M').to_timestamp()

	if end_date == None:
		end_date = today()
	elif end_date > today():
		raise ValueError("Trying to fetch data from the future...")

	query_period = date_range(start_date, end_date, freq='MS')
	periods = '|'.join(map(lambda x: x.strftime('%Y%m'), query_period))
	api_page = requests.get(cpi_ibge_url.format(periods))
	# return url
	api_data = json.loads(api_page.text)
	cpi = DataFrame.from_dict(api_data[0]['resultados'][0]['series'][0]['serie'], orient='index', columns=['CPI-BR'], dtype=float)
	cpi.index = to_datetime(cpi.index, format='%Y%m')
	cpi = cpi['CPI-BR']

	if query_period[-1] > cpi.index[-1]:
		print("Warning: Asking for inflation data which is unavailable, extrapolating from last 12 months.")
		cpi_extra = Series(index=query_period, dtype=float)
		cpi_extra.loc[cpi.index] = cpi
		cpi = cpi.reset_index(drop=True)
		if len(cpi) > 12:
			x = cpi.iloc[-12:].index.astype(float).values
			y = cpi.iloc[-12:].values
		else:
			x = cpi.index.astype(float).values
			y = cpi.values
		coefs = curve_fit(linear_fit, x, y)[0]
		x = cpi_extra.reset_index(drop=True).loc[isnull(cpi_extra.reset_index(drop=True))].index.astype(float).values
		cpi_extra.loc[isnull(cpi_extra)] = linear_fit(x, *coefs)
		cpi = cpi_extra
	return cpi


def get_inflation_rate_ibge(reference_date, current_date='latest', date_format='%Y-%m', rate_by=None):
	"""
	Retrieves inflation rate from IBGE using its API.

	Parameters
	----------
	reference_date : str or datetime
		Reference date for prices.
	current_date : TYPE
		Date in which to compute inflated prices.
	date_format : str, optional
		If dates are informed as strings use this format to parse it. The default is '%Y-%m'.
	rate_by : str, optional
		Inform inflation rate by 'month','year','day' or 'quarter'. The default is None which gives the total inflation.

	Returns
	-------
	inflation_rate : float
		Total inflation or inflation by desired rate.

	"""
	if isinstance(reference_date, str):
		reference_date = strptime(reference_date, date_format)
	else:
		reference_date = reference_date.round('d')
	if isinstance(current_date, str):
		if current_date == 'latest':
			latest_data = get_cpi_ibge().index[-1]
		else:
			current_date = strptime(current_date, date_format)
	else:
		current_date = current_date.round('d')

	if reference_date > current_date:
		raise ValueError("Current date must be later than reference date")
	elif current_date >= today():
		print("Warning: asking for data from the future!")

	rate_by_options = ['year', 'month', 'day', 'quarter', None]
	if rate_by not in rate_by_options:
		raise ValueError(f"'{rate_by}' rates not supported. Try one of {rate_by_options}")

	api_page = requests.get(cpi_ibge_url.format(f"{reference_date.strftime('%Y%m')}|{current_date.strftime('%Y%m')}"))
	api_data = json.loads(api_page.text)
	cpi = api_data[0]['resultados'][0]['series'][0]['serie']
	cpi = DataFrame.from_dict(cpi, orient='index', columns=['cpi'], dtype=float)
	cpi.index = to_datetime(cpi.index, format='%Y%m')

	if current_date == cpi.index[-1]:
		pass
	else:
		latest_data = get_cpi_ibge().index[-1]
		raise ValueError(f"IBGE API did not relay data until requested date. Lastest CPI info avaible is from {latest_data.strftime('%Y-%m')}.")

	cpi_inflation = cpi.iloc[-1] / cpi.iloc[0]
	dt = (current_date - reference_date).days

	if rate_by == 'day':
		pass
	elif rate_by == 'month':
		dt = dt / 365 * 12
	elif rate_by == 'year':
		dt /= 365
	elif rate_by == 'quarter':
		dt = dt / 365 * 4
	else:
		dt = 1

	cpi_inflation = (cpi_inflation) ** (1 / dt)
	inflation_rate = cpi_inflation['cpi'] - 1
	return inflation_rate


def get_cpi_bls(start_date=None, end_date=None):
	"""
	Retrieves the CPI (Consumer Price Index) from the BLS (Bureou of Labor Statistics)

	Parameters
	----------
	start_date : datetime, optional
		Table start date. The default is None which fetches up to 10 years before end_date.
	end_date : TYPE, optional
		Table end date. The default is None which fetches until most current date.

	Raises
	------
	Exception
		If requests fails for some reason.

	Returns
	-------
	cpi : DataFrame
		CPI data from given time frame.

	"""
	earliest = strptime('1913-1-1')

	if end_date == None:
		end_date = today()

	if start_date == None:
		ten_years = Timedelta(days=3650)
		start_date = end_date - ten_years

	if start_date < earliest:
		print("Warning: earliest possible start_date is {earliest.strftime('%Y-%m)}")
		start_date = earliest

	if start_date > end_date:
		raise ValueError("End date must be later than start date")
	elif round((end_date - start_date).days / 365, 1) > 10:
		print(round((end_date - start_date).days / 365, 1))
		raise ValueError("BLS API allows queries spanning at most 10 years")

	headers = {'Content-type': 'application/json'}
	data = json.dumps({"seriesid": ['CUUR0000SA0'], "startyear": str(start_date.year), "endyear": str(end_date.year)})
	api_page = requests.post('https://api.bls.gov/publicAPI/v1/timeseries/data/', data=data, headers=headers)
	api_data = json.loads(api_page.text)
	if api_data['status'] != 'REQUEST_SUCCEEDED':
		raise Exception(f"Request failed {api_data['message']}")
	api_data = DataFrame(api_data['Results']['series'][0]['data'])
	api_data.index = to_datetime((api_data['year'] + api_data['period']).map(lambda x: x.replace('M', '')), format='%Y%m')
	api_data = api_data.drop(['year', 'period', 'periodName', 'footnotes'], axis=1)
	cpi = api_data.rename(columns={'value': 'CPI-US'}).sort_index()
	return cpi['CPI-US']


def get_cpi(location, start_date=None, end_date=None):
	if location == 'BR':
		return get_cpi_ibge(start_date, end_date)
	elif location == 'US':
		return get_cpi_bls(start_date, end_date)
	else:
		raise ValueError(f"Unsupported location '{location}'")


def col_data(ticker, start_date, end_date):
	Ticker = yahoo.Ticker(ticker)
	df = Ticker.history(interval='1mo', start=start_date, end=end_date, actions=False, back_adjust=True).dropna()
	df.index = df.index + offsets.MonthBegin(0)
	return df['Close']


def int2dt(ts, ts_mult=TS_MULT_us):
	return (datetime.datetime.utcfromtimestamp(float(ts) / ts_mult))


class TimeAxisItem(pg.AxisItem):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def tickStrings(self, values, scale, spacing):
		# PySide's QTime() initialiser fails miserably and dismisses args/kwargs
		# return [QTime().addMSecs(value).toString('mm:ss') for value in values]

		return [int2dt(value).strftime("%Y-%m-%d") for value in values]


class Analysis(QWidget):
	def __init__(self, parent=None):
		super(Analysis, self).__init__(parent)
		uic.loadUi('analysis.ui', self)

		self.resultsplot = PlotWidget()
		self.resultsplot.setAxisItems(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
		self.resultsplot.addLegend()

		self.interestplot = PlotWidget()
		self.interestplot.setAxisItems(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
		self.interestplot.addLegend()

		self.inflationplot = PlotWidget()
		self.inflation.addWidget(self.inflationplot)
		self.inflationplot.setAxisItems(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
		self.inflationplot.addLegend()

		self.interest.addWidget(self.interestplot)
		self.results.addWidget(self.resultsplot)
		self.inflation.addWidget(self.inflationplot)
		self.addlist.clicked.connect(self.run)
		self.thread = None


		self.line_colors = [QColor(*i) for i in [(28,134,238),(227,26,28),(0,139,0),(106,61,154),(255,127,0),(0,0,0),(255,215,0),(126,192,238),(251,154,153),(144,238,144),(202,178,214),(253,191,111),(179,179,179),(238,230,133),(176,48,96),(255,131,250),(255,20,147),(0,0,255),(54,100,139),(0,206,209),(0,255,0),(139,139,0),(205,205,0),(139,69,0),(165,42,42)]]
		self.line_colors += self.line_colors

		self.items = {}

	def clear(self):

		for i in [self.inflationplot, self.interestplot, self.resultsplot]:
			i.clear()
			self.items = {}

		for i in range(self.checkbox.count()):
			self.checkbox.itemAt(i).widget().deleteLater()

	def process(self, start_date, end_date, usstocks, brstocks):
		cpi = get_cpi('BR', start_date, end_date)
		inputs = (cpi / cpi.iloc[0]).to_frame('BRL')
		usdbrl = read_json('https://api.bcb.gov.br/dados/serie/bcdata.sgs.3698/dados?formato=json')
		usdbrl.data = to_datetime(usdbrl.data, format='%d/%m/%Y')
		usdbrl = usdbrl.set_index('data')
		inputs['USDBRL'] = usdbrl['valor'][inputs.index]
		inputs['USD'] = inputs['BRL'] / inputs['USDBRL']
		inputs['BRLINF'] = inputs['BRL'] * (inputs.reset_index().index + 1)

		cpi = get_cpi('BR', strptime('1994-07-01'), end_date)
		cum_inflation = (cpi / cpi.iloc[0]).to_frame('BR')
		df_inflation_us = read_csv('https://www.statbureau.org/en/united-states/inflation-tables/inflation.monthly.csv').set_index('Year').drop(columns=' Total')
		df_inflation_us.index = df_inflation_us.index.astype(str)
		df_inflation_us = df_inflation_us.stack()
		df_inflation_us.index = map(strptime, df_inflation_us.index.map('/'.join), ['%Y/ %B'] * len(df_inflation_us))
		df_inflation_us = df_inflation_us.reindex(index=cum_inflation.index) / 100 + 1
		df_inflation_us.iloc[0] = 1
		cum_inflation['US'] = df_inflation_us.cumprod()
		cum_inflation['BR/US'] = cum_inflation['BR'] / cum_inflation['US']
		cum_inflation['USDBRL'] = inputs['USDBRL']
		cum_inflation = cum_inflation.reindex(index=inputs.index)

		df_stocks = DataFrame()
		df_stonks = DataFrame()

		for ticker in brstocks:
			df_stocks[ticker] = col_data(ticker, start_date, end_date)

		for ticker in usstocks:
			df_stonks[ticker] = col_data(ticker, start_date, end_date)

		df_stocks_amounts = (1 / df_stocks).mul(inputs['BRL'], axis=0)
		df_stonks_amounts = (1 / df_stonks).mul(inputs['USD'], axis=0)
		df_capital_br = df_stocks_amounts.cumsum() * df_stocks
		df_capital_us = (df_stonks_amounts.cumsum() * df_stonks).mul(inputs['USDBRL'], axis=0)

		df_result = (concat([df_capital_br, df_capital_us], axis=1).interpolate(method='linear')).div(inputs['BRLINF'], axis=0)

		df_interest = (df_result.pow(1 / (df_result.reset_index().index + 1), axis=0) - 1) * 100

		cum_inflation=cum_inflation.fillna(np.nan)
		df_interest=df_interest.fillna(np.nan)
		df_result=df_result.fillna(np.nan)

		return cum_inflation, df_interest, df_result

	def run(self, result=None):


		if result == 'Done':

			self.clear()
			cum_inflation, df_interest, df_result = self.thread.results

			for i, y in enumerate(['BR/US', 'USDBRL']):
				color = self.line_colors[i]
				item = PlotCurveItem(pen=pg.mkPen(color=color, width=2), name=y)
				x=cum_inflation.index.astype(int).values / 1000
				item.setData(x, cum_inflation[y].values, connect="finite")
				self.inflationplot.addItem(item)

			self.inflationplot.getPlotItem().setLimits(xMin=x[0],
			                                           xMax=x[-1])
			self.resultsplot.getPlotItem().setLimits(xMin=x[0],
			                                           xMax=x[-1])
			self.interestplot.getPlotItem().setLimits(xMin=x[0],
			                                           xMax=x[-1])
			for i, y in enumerate(df_result.columns):

				check = QCheckBox(y)
				check.setChecked(True)
				check.clicked.connect(partial(self.check, y, check))

				self.checkbox.addWidget(check)

				color = self.line_colors[i]

				item = PlotCurveItem(pen=pg.mkPen(color=color, width=2), name=y)
				item.setData(df_result.index.astype(int).values / 1000, df_result[y].values, connect="finite")
				self.resultsplot.addItem(item)

				item2 = PlotCurveItem(pen=pg.mkPen(color=color, width=2), name=y)
				self.items[y] = [item, item2]
				item2.setData(df_interest.index.astype(int).values / 1000, df_interest[y].values, connect="finite")
				self.interestplot.addItem(item2)

		else:

			start_date = strptime(self.startdate.text())
			end_date = strptime(self.enddate.text())

			self.thread = Worker(self.process, [start_date, end_date, self.usstocks.text().split(','), self.brstocks.text().split(',')])
			self.thread.signal.connect(self.run)
			self.thread.start()

	def check(self, y, check):
		if check.isChecked():
			self.interestplot.addItem(self.items[y][1])
			self.resultsplot.addItem(self.items[y][0])

		else:
			self.interestplot.removeItem(self.items[y][1])
			self.resultsplot.removeItem(self.items[y][0])
