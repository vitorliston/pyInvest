import datetime
import json
import traceback
from functools import lru_cache
from os import path
from urllib.request import urlopen

import pandas as pd


def get_date_range(start, end):
    dates = [start]

    delta = round((end - start).days / 30)

    if start.weekday() > 4:
        start -= datetime.timedelta(days=3)
    if start.weekday() < 2:
        start += datetime.timedelta(days=2)

    while start < end:
        start += datetime.timedelta(days=delta)

        dates.append(start)

    del dates[-1]

    if end.weekday() == 5:
        end -= datetime.timedelta(days=1)
    if end.weekday() == 6:
        end -= datetime.timedelta(days=2)

    dates.append(end)

    return dates


@lru_cache(maxsize=None)
def get_ticker_history(ticker):
    if path.exists('cache/' + ticker + '.json'):

        try:
            a = json.load(open('cache/' + ticker + '.json', "r"))

            if datetime.datetime.fromtimestamp(a['chart']['result'][0]['timestamp'][-1]).date() < (
                    datetime.datetime.today() - datetime.timedelta(
                days=1)).date() and datetime.datetime.today().weekday() < 5:
                #	print('Get {}, cache date {} last date {}'.format(ticker,datetime.datetime.fromtimestamp(a['chart']['result'][0]['timestamp'][-1]).date(),(datetime.datetime.today()-datetime.timedelta(days=1)).date()))
                print('Downloading {} updated data, cache {}'.format(ticker, datetime.datetime.fromtimestamp(
                    a['chart']['result'][0]['timestamp'][-1]).date()))
                a = get_url(
                    "https://query2.finance.yahoo.com/v8/finance/chart/{}?range=50y&region=US&interval=1d&lang=en&events=div%2Csplit".format(
                        ticker))
                with open('cache/' + ticker + '.json', 'w') as outfile:
                    json.dump(a, outfile)
        except Exception as e:
            traceback.print_exc()
            print('Downloading {} data'.format(ticker))
            a = get_url(
                "https://query2.finance.yahoo.com/v8/finance/chart/{}?range=50y&region=US&interval=1d&lang=en&events=div%2Csplit".format(
                    ticker))
            with open('cache/' + ticker + '.json', 'w') as outfile:
                json.dump(a, outfile)

    else:
        print('Downloading {} data'.format(ticker))
        a = get_url(
            "https://query2.finance.yahoo.com/v8/finance/chart/{}?range=50y&region=US&interval=1d&lang=en&events=div%2Csplit".format(
                ticker))
        with open('cache/' + ticker + '.json', 'w') as outfile:
            json.dump(a, outfile)


    dat= pd.DataFrame(a)


    return dat


@lru_cache(maxsize=None)
def get_cpi(loc='BR'):
    if loc == 'BR':
        dates = '199407%7C199408%7C199409%7C199410%7C199411%7C199412'

        for y in range(1995, int(datetime.datetime.today().strftime('%Y')) + 1):
            for m in range(1, 13):
                dates += '%7C{}{:02d}'.format(y, m)

        url = 'https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{}/variaveis/2266?localidades=N1[all]'.format(
            dates)

    if loc == 'US':
        pass
    file_path = 'cache/{}_cpi.json'.format(loc)
    if path.exists(file_path):

        try:
            a = json.load(open(file_path, "r"))

            if list(a[0]['resultados'][0]['series'][0]['serie'].keys())[-1] != (
                    datetime.datetime.today() - datetime.timedelta(days=20)).strftime("%Y%m"):
                a = get_url(url)
                with open(file_path, 'w+') as outfile:
                    json.dump(a, outfile)
        except Exception as e:

            a = get_url(url)
            with open(file_path, 'w+') as outfile:
                json.dump(a, outfile)

    else:
        a = get_url(url)
        with open(file_path, 'w+') as outfile:
            json.dump(a, outfile)

    x = []
    y = []
    for k, v in a[0]['resultados'][0]['series'][0]['serie'].items():
        x.append(datetime.datetime.strptime(k, '%Y%m').timestamp())
        y.append(float(v))

    return x, y


def get_url(url):
    response = urlopen(url)

    a = json.loads(response.read().decode('utf8'))
    return a


def get_stock_price_live(ticker):
    a = get_url("https://query2.finance.yahoo.com/v7/finance/quote?region=US&lang=en&symbols={}".format(ticker))

    return a['quoteResponse']['result'][0]['regularMarketPrice'], datetime.datetime.fromtimestamp(
        a['quoteResponse']['result'][0]['regularMarketTime'])


@lru_cache(maxsize=None)
def get_cur_exchange(pair):
    if path.exists('cache/' + pair + '.json'):

        try:
            a = json.load(open('cache/' + pair + '.json', "r"))

            if datetime.datetime.fromtimestamp(a['chart']['result'][0]['timestamp'][-1]).date() < (
                    datetime.datetime.today() - datetime.timedelta(
                days=1)).date() and datetime.datetime.today().weekday() < 5:
                #	print('Get {}, cache date {} last date {}'.format(ticker,datetime.datetime.fromtimestamp(a['chart']['result'][0]['timestamp'][-1]).date(),(datetime.datetime.today()-datetime.timedelta(days=1)).date()))
                print('Downloading {} updated data, cache {}'.format(pair, datetime.datetime.fromtimestamp(
                    a['chart']['result'][0]['timestamp'][-1]).date()))
                a = get_url(
                    "https://query2.finance.yahoo.com/v8/finance/chart/{}=X?range=50y&region=US&interval=1d&lang=en&events=div%2Csplit".format(
                        pair))
                with open('cache/' + pair + '.json', 'w') as outfile:
                    json.dump(a, outfile)
        except Exception as e:
            traceback.print_exc()
            print('Downloading {} data'.format(pair))
            a = get_url(
                "https://query2.finance.yahoo.com/v8/finance/chart/{}=X?range=50y&region=US&interval=1d&lang=en&events=div%2Csplit".format(
                    pair))
            with open('cache/' + pair + '.json', 'w') as outfile:
                json.dump(a, outfile)

    else:
        print('Downloading {} data'.format(pair))
        a = get_url(
            "https://query2.finance.yahoo.com/v8/finance/chart/{}=X?range=50y&region=US&interval=1d&lang=en&events=div%2Csplit".format(
                pair))
        with open('cache/' + pair + '.json', 'w') as outfile:
            json.dump(a, outfile)

    return a['chart']['result'][0]['timestamp'], a['chart']['result'][0]['indicators']['quote'][0]['close']



