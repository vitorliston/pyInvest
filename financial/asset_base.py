from scipy.interpolate import interp1d

from util import *

TODAY = datetime.datetime.today()


class Asset_base():

    def __init__(self, ticker, transactions, inflation,exchange):
        self.history = get_ticker_history(ticker)
        self.exchange=exchange
        self.currency=self.history['chart']['result'][0]['meta']['currency']
        if self.currency != self.exchange.ref_currency:
            transactions['Total'] = transactions.apply(
                lambda row: row['Total'] * self.exchange.to_ref(self.currency, row['Date']), axis=1)

        self.inf = inflation
        self.ticker = ticker

        data = self.history['chart']['result'][0]['indicators']['quote'][0]['close']

        last_value = 0
        new = []
        for i in range(len(data)):
            if data[i] != None:
                new.append(data[i])
                last_value = data[i]
            else:
                new.append(last_value)

        self.history['chart']['result'][0]['indicators']['quote'][0]['close'] = new  # Fix nones

        self.transactions = transactions.reset_index(drop=True)

        splits = self.splits()
        for date_split, val_split in splits.items():
            self.transactions.loc[self.transactions['Date'] < date_split - datetime.timedelta(days=0.5), 'Quantity'] = (
                    self.transactions['Quantity'] * val_split).astype(int)

        self.transactions.loc[self.transactions['Order'] == 'Sell', 'Total'] = -1 * self.transactions['Total']
        self.transactions.loc[self.transactions['Order'] == 'Sell', 'Quantity'] = -1 * self.transactions['Quantity']

        #	quit()
        qtd = 0
        invested = 0
        self.start_date = None
        for index, row in self.transactions.iterrows():

            if row['Order'] == 'Buy':
                qtd += row['Quantity']
                invested += row['Total']
                if self.start_date == None:
                    self.start_date = row['Date']


            elif row['Order'] == 'Sell':
                qtd += row['Quantity']
                invested += row['Total']

            if qtd == 0:
                invested = 0
                self.start_date = None
        if qtd > 0:
            cps = invested / qtd

        else:
            cps = 0

        self.cps = round(cps, 2)

        timestamp = [0]
        qtd_changes = [0]
        for i in self.transactions['Date']:
            timestamp.append(i.timestamp())
            qtd_changes.append(self.qtd_at_date(i))
        if len(timestamp) > 1:
            self._qtd = interp1d(timestamp, qtd_changes, kind='previous', fill_value=(0, qtd_changes[-1]),bounds_error=False)
        else:
            self._qtd = lambda x: qtd_changes[0]



        if len(self.history['chart']['result'][0]['timestamp']) > 1:  # Create asset price by time curve for better speed
            self._price_at_date = interp1d(self.history['chart']['result'][0]['timestamp'],
                                           self.history['chart']['result'][0]['indicators']['quote'][0]['close'],
                                           kind='previous', fill_value=(0, self.history['chart']['result'][0]['indicators']['quote'][0]['close'][-1]),
                                           bounds_error=False)
        else:
            print('Limited data available for {}'.format(self.ticker))
            self._price_at_date = lambda x: self.history['chart']['result'][0]['indicators']['quote'][0]['close'][0]

        try:

            a = self.history['chart']['result'][0]['events']['dividends']

            div = {}
            for value in a.values():
                div[datetime.datetime.fromtimestamp(value['date'])] = value['amount']

            total = 0
            bb = [0]
            aa = [0]
            cc = [0]
            for date_div, val_div in div.items():
                qtd = self.qtd(date_div)

                aa.append(date_div.timestamp())
                cc.append(val_div)
                total += qtd * val_div * self.exchange.to_ref(self.currency,date_div)
                bb.append(total)



            self.pos_acc_div_at_date = interp1d(aa, bb,
                                                kind='previous', fill_value=(0,bb[-1]),bounds_error=False)
            self.acc_div_at_date = interp1d(aa, cc,
                                            kind='previous', fill_value=(0,cc[-1]),bounds_error=False)
        except Exception as e:
            self.pos_acc_div_at_date = lambda x: 0
            self.acc_div_at_date = lambda x: 0

    @property
    def net(self):
        return round((self.price - self.cps) * self.qtd(), 2)

    @property
    def price(self):
        return round(self.history['chart']['result'][0]['indicators']['quote'][0]['close'][-1] * self.exchange.to_ref(self.currency,
                                                                                                                      TODAY), 2)

    @property
    def change(self):
        return round(100 * (self.price / self.cps - 1), 2)

    def price_live(self):
        return get_stock_price_live(self.ticker)

    def price_at_date(self, date):
        try:
            price = round(self._price_at_date(date.timestamp()) * self.exchange.to_ref(self.currency, date), 2)
        except:
            price = 0
        return price

    def splits(self):
        try:
            a = self.history['chart']['result'][0]['events']['splits']
        except:
            return {}
        splits = {}
        for value in a.values():
            splits[datetime.datetime.fromtimestamp(value['date'])] = value['numerator'] / value['denominator']

        return splits

    def qtd_at_date(self, date):

        if date >= self.transactions['Date'].min():
            trans = self.transactions.loc[self.transactions['Date'] <= date].copy()
            if trans.empty:
                return 0

            a = trans['Quantity'].sum()

            return a

        return 0

    def qtd(self, date=TODAY):

        return self._qtd(date.timestamp())

    def invested_corrected(self, date):
        """Compensate all transactions with inflation and return the sum up to the input date"""
        if date >= self.transactions['Date'][0]:
            if self.qtd(date) > 0:
                trans = self.transactions.loc[self.transactions['Date'] <= date].copy()

                trans['Total inf'] = trans['Total']

                if self.currency==self.exchange.ref_currency: #Only consider inflation for same base currency asset, inflation is already included in exchange prices
                    trans['Total inf'] = trans.apply(
                        lambda row: row['Total'] * (self.inf.inflation_range(row['Date'], date) + 1), axis=1)

                return trans['Total inf'].sum()

        return 0

    def invested(self, date=None):
        if date == None:
            return self.qtd() * self.price

        elif date >= self.transactions['Date'][0]:
            if self.qtd(date) > 0:
                trans = self.transactions.loc[self.transactions['Date'] <= date].copy()

                return trans['Total'].sum()

        return 0

    def dividends(self, date=TODAY, pos=True):
        if pos:
            div = self.pos_acc_div_at_date(date.timestamp())
        else:
            div = self.acc_div_at_date(date.timestamp())

        return round(float(div), 2)

    def chart(self):
        x = self.history['chart']['result'][0]['timestamp']
        y = self.history['chart']['result'][0]['indicators']['quote'][0]['close']
        return x, y

    def summary(self):

        s = {'Ticker': self.ticker, 'Qtd': self.qtd(), 'Cost': self.cps, 'Value': self.price, 'Net': self.net,
             'Change': self.change, 'Total': round(self.qtd() * self.price, 2), 'Income': self.dividends(),
             'Type': self.type}

        return s

    def rentability(self):

        vals = {'RENT': {}, 'RENT IPCA': {}, 'RENT IPCA DIV': {}}

        for name, i in {'1M': 1, '2M': 2, '6M': 6, '1Y': 12, '2Y': 24, '5Y': 5 * 12, '10Y': 10 * 12}.items():
            initdate = TODAY - datetime.timedelta(days=int(30 * i))
            start = self._price_at_date((initdate).timestamp())

            if start == 0:
                vals['RENT'][name] = 0
                vals['RENT IPCA'][name] = 0
                vals['RENT IPCA DIV'][name] = 0
            else:

                end = self.price
                vals['RENT'][name] = 100 * (end - start) / start
                inf = (self.inf.inflation_range(initdate, TODAY) + 1)
                vals['RENT IPCA'][name] = 100 * (end - start * inf) / start * inf
                div = self.acc_div_at_date(TODAY.timestamp()) - self.acc_div_at_date(initdate.timestamp())
                vals['RENT IPCA DIV'][name] = 100 * (end - start * inf + div) / start * inf

        return vals
