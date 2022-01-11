import datetime

from scipy.interpolate import interp1d

from util import get_cur_exchange

TODAY = datetime.datetime.today()

class Exchange():
    def __init__(self, ref_currency):
        self.ref_currency = ref_currency
        self.pairs = {}





    def ref_to(self, currency,date=TODAY):
        if currency == self.ref_currency:
            return 1
        else:
            if currency + self.ref_currency not in self.pairs.keys():
                self.add_pair(currency + self.ref_currency)
            return 1/self.pairs[currency + self.ref_currency](date.timestamp())

    def to_ref(self, currency,date=TODAY):
        if currency == self.ref_currency:
            return 1

        else:
            if currency + self.ref_currency not in self.pairs.keys():
                self.add_pair(currency + self.ref_currency)
            return self.pairs[currency + self.ref_currency](date.timestamp())


    def add_pair(self,pair):


        ex=get_cur_exchange(pair)
        data = ex[1]

        last_value = 0
        new = []
        for i in range(len(data)):
            if data[i] != None:
                new.append(data[i])
                last_value = data[i]
            else:
                new.append(last_value)




        self.pairs[pair]=interp1d(ex[0],new, kind='previous', fill_value=(0, new[-1]),
                                               bounds_error=False)
