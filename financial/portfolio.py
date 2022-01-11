from datetime import datetime
from datetime import timedelta
from functools import lru_cache

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from financial.assets import Stock_BR, Stock_US, REIT, FII
from financial.exchange import Exchange
from financial.index import Index
from financial.inflation import Inflation
from util import get_date_range


class Portfolio(QObject):
    signalStatus = pyqtSignal(str)

    def __init__(self, config):
        super(Portfolio, self).__init__(None)
        self.inflation = Inflation(config['inflation'])
        self.exchange = Exchange(config['currency'])
        self.transactions = None
        self.data = {}
        self.assets = {}
        self.ibov = Index('%5EBVSP')
        self.sp500 = Index('%5EGSPC')
        self.cache = {}
        self.types = {'BR': Stock_BR, 'US': Stock_US, 'FII': FII, 'REIT': REIT}

    @pyqtSlot()
    def load_transactions(self, transactions):
        self.assets = {}
        self.transactions = transactions
        self.status('Loading transactions')
        for type, asset in self.types.items():
            tran = transactions.loc[transactions['Type'] == type]
            if not tran.empty:
                self.assets.update(
                    {i: asset(i, transactions.loc[(transactions['Symbol'] == i)].copy(), self.inflation, self.exchange) for i in set(tran['Symbol'])})

    @property
    def start_date(self):

        return self.transactions['Date'][0]

    @lru_cache(maxsize=None)
    def chart_stock(self):

        dates = get_date_range(self.start_date, datetime.today())
        stocks = {}

        for date in dates:
            for ticker, stock in self.assets.items():
                if stock.qtd(date) > 0:
                    if ticker not in stocks.keys():
                        stocks[ticker] = {'Total': [], 'Date': [], 'Change': [], 'Prices': []}
                    if stock.cps != 0:
                        stocks[ticker]['Change'].append((stock.price_at_date(date) / stock.cps - 1) * 100)
                    else:
                        stocks[ticker]['Change'].append(0)
                    stocks[ticker]['Prices'].append(stock.price_at_date(date))
                    stocks[ticker]['Total'].append(stock.price_at_date(date) * stock.qtd(date))
                    stocks[ticker]['Date'].append(date)

        return stocks

    @lru_cache(maxsize=None)
    def chart_pos(self):

        dates = get_date_range(self.start_date, datetime.today())

        total = {'Date': [], 'Value': [], 'Invested': [], 'Div': [], 'Invested_corr': []}

        for date in dates:
            value = 0
            invested = 0
            invested_corr = 0
            div = 0
            for ticker, stock in self.assets.items():
                div += stock.dividends(date)
                value += stock.price_at_date(date) * stock.qtd(date)
                invested += stock.invested(date)  # Sum of transactions, not cps*qtd
                invested_corr += stock.invested_corrected(date)
            total['Invested_corr'].append(invested_corr)
            total['Invested'].append(invested)
            total['Value'].append(value)
            total['Div'].append(div)
            total['Date'].append(date)

        return total

    @lru_cache(maxsize=None)
    def get_pos(self):

        pos = {'BR': {}, 'US': {}, 'FII': {}}
        for ticker, stock in self.assets.items():
            if stock.qtd(datetime.today()) > 0:
                pos[stock.type][ticker] = stock

        return pos

    @pyqtSlot()
    def rentability(self, range_months):
        types = ['', 'US', 'BR', 'FII']

        if str(range_months) in self.cache.keys():  # Store results
            return self.cache[str(range_months)]

        if range_months == 0:
            self.status('Calculating total rentability')
            range_months = 120000
        else:
            self.status('Calculating rentability for {} months'.format(range_months))

        if range_months > int((datetime.today() - self.start_date).days / (365 / 12)):
            range_months = int((datetime.today() - self.start_date).days / (365 / 12))

        start_date = datetime.today() - timedelta(days=range_months * 365 / 12)
        dates = get_date_range(start_date, datetime.today())
        data = {i: [] for i in
                ['DATE', 'RENT IPCA ', 'RENT ', 'RENT IPCA FII', 'RENT FII', 'RENT BR', 'RENT US', 'RENT IPCA BR',
                 'RENT IPCA US', 'IBOV', 'SP500', 'IPCA']}

        ibov0 = self.ibov.price_at_date(dates[0])
        sp500 = self.sp500.price_at_date(dates[0])
        for date in dates:
            data['IBOV'].append(100 * (self.ibov.price_at_date(date) - ibov0) / ibov0)
            data['SP500'].append(100 * (self.sp500.price_at_date(date) - sp500) / sp500)
            inf = self.inflation.inflation_range(start_date, date)
            data['IPCA'].append(100 * inf)
            data['DATE'].append(date)

        for TYP in types:
            init, init_inf = 0, 0
            first = True
            for date in dates:
                value = 0
                invested = 0
                invested_corr = 0
                div = 0
                for stock in self.assets.values():
                    if stock.type == TYP or TYP == '':
                        qtd = stock.qtd(date)
                        div += stock.dividends(date)
                        value += stock.price_at_date(date) * qtd
                        invested += stock.invested(date)  # Sum of transactions, not cps*qtd
                        invested_corr += stock.invested_corrected(date)

                if first and invested > 0:
                    init = (value + div) / invested - 1
                    first = False
                    init_inf = (value + div) / invested_corr - 1

                if invested > 0:

                    data['RENT {}'.format(TYP)].append(100 * ((value + div) / invested - 1 - init))
                    data['RENT IPCA {}'.format(TYP)].append(100 * ((value + div) / invested_corr - 1 - init_inf))
                else:
                    data['RENT {}'.format(TYP)].append(0)
                    data['RENT IPCA {}'.format(TYP)].append(0)

        self.cache[str(range_months)] = data
        return data

    @lru_cache(maxsize=None)
    def get_rentability_data(self):

        data = self.chart_pos()

        # sales=sum([i['Sold'] for j,i in self.assets.items() if i.qtd_now==0])

        names = {'N': 0, 'Invested': data['Invested'][-1], 'Value': data['Value'][-1],
                 'Net': data['Value'][-1] - data['Invested'][-1], 'Income': data['Div'][-1], 'Sales': 0}

        rwinf = {'1M': [[1], 'RENT IPCA '], '6M': [[6], 'RENT IPCA '], '1A': [[12], 'RENT IPCA '],
                 '2A': [[24], 'RENT IPCA '],
                 'Total': [[int((datetime.today() - self.start_date).days / (365 / 12))], 'RENT IPCA ']}

        rninf = {'1M': [[1], 'RENT '], '6M': [[6], 'RENT '], '1A': [[12], 'RENT '],
                 '2A': [[24], 'RENT '],
                 'Total': [[int((datetime.today() - self.start_date).days / (365 / 12))], 'RENT ']}

        rwinf_res = {}
        for key, val in rwinf.items():
            rwinf_res[key] = self.rentability(*val[0])[val[1]][-1]

        rninf_res = {}
        for key, val in rninf.items():
            rninf_res[key] = self.rentability(*val[0])[val[1]][-1]

        return {'RENT IPCA': rwinf_res, 'RENT': rninf_res, 'SUMMARY': names}

    def status(self, message):
        self.signalStatus.emit(message)
