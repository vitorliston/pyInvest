from .asset_base import Asset_base




class Stock_BR(Asset_base):
    type = 'BR'
    def __init__(self, ticker, transactions, inflation, exchange):
        ticker += '.SA'
        super(Stock_BR, self).__init__(ticker, transactions, inflation, exchange)


class Stock_US(Asset_base):
    type = 'US'
    def __init__(self, ticker, transactions, inflation, exchange):
        super(Stock_US, self).__init__(ticker, transactions, inflation, exchange)


class REIT(Asset_base):
    type = 'REIT'

    def __init__(self, ticker, transactions, inflation, exchange):
        super(REIT, self).__init__(ticker, transactions, inflation, exchange)


class FII(Asset_base):
    type = 'FII'
    def __init__(self, ticker, transactions, inflation, exchange):
        ticker += '.SA'
        super(FII, self).__init__(ticker, transactions, inflation, exchange)