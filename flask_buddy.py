#!/usr/bin/env python3
import datetime
import sys
import json
import argparse
import pandas as pd
import os.path

import tda
from tda.client import Client as TDClient
from flask import Flask, request, render_template, redirect

#tda.debug.enable_bug_report_logging()

class Config(object):
    def __init__(self):
        self.apikey = None
        self.callbackuri = None
        self.accountnum = None
        self.tokenpath = None

    def read_config(self, config_file):
        print("Reading config")
        fh = open(config_file, 'r')
        c = json.load(fh)
        fh.close()
        self.apikey = c["apikey"]
        self.callbackuri = c["callbackuri"]
        self.tokenpath = c['tokenpath']
        self.accountnum = c['accountnum']

    def write_config(self, cfile):
        fh = open(cfile, 'w')
        fh.write(json.dumps(self.__dict__))
        fh.close()

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)

CONFIG = Config()

CONTRACT_TYPE = tda.client.Client.Options.ContractType
ORDER_STATUS = tda.client.Client.Order.Status
FIELDS = tda.client.Client.Account.Fields
TRANSACTION_TYPES = tda.client.Client.Transactions.TransactionType
TODAY = datetime.date.today()
YESTERDAY = TODAY - datetime.timedelta(days=1)

ACCOUNT_DATA = {
    "Starting_NLV": 0,
    "Starting_BP": 0,
    "Starting_BPu": 1,
    "NLV": 0,
    "BP_Available": 0,
    "BPu": 1,
    "Max_Short_Units": -1
}

app = Flask(__name__)
@app.route("/")
def dashboard():
    global ACCOUNT_DATA
    conf = CONFIG
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    calc_account_data(client, conf, ACCOUNT_DATA)
    acc_json = client.get_account(conf.accountnum).json()
    fh=open("account_dump.json",'w')
    fh.write(json.dumps(acc_json))
    fh.close()
    acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    #print(accounts.text)
    accdata = acc_json['securitiesAccount']
    aid = accdata['accountId']
    positions = accdata['positions']
    try:
        todays_premium = round(get_premium_today(client, conf.accountnum)*100,2)
        todays_pct = round(todays_premium/ACCOUNT_DATA['NLV']*100,2)
    except Exception as e:
        print(e)
        todays_premium = None
        todays_pct = None

    sut = sut_test(positions, ACCOUNT_DATA['Max_Short_Units'])
    order_counts = get_order_count(client,conf, conf.accountnum)
    exp_prem = pd.DataFrame(get_premium(positions)).transpose().sort_index()
    #print(json.dumps(order_counts, indent=4))
    sutdf = pd.DataFrame(sut)
    red_df = get_red_alert_df(client, positions)

    return render_template(
        "lotto_stats.html",
        sut=sut,
        ACCDATA=ACCOUNT_DATA,
        TIME=datetime.datetime.now(),
        SUTDF=sutdf.to_html(index=False),
        ORDER_COUNT=order_counts,
        PREMIUM_BY_EXP=exp_prem.to_html(),
        REDALERT=red_df.head(20).to_html(),
        PREMIUM_TODAY = todays_premium,
        PREMIUM_TODAY_PCT = todays_pct
    )


@app.route("/redalert")
def redalert(**argv):
    pass
    conf = CONFIG
    client = get_client(conf)
    acc_json = client.get_account(conf.accountnum, fields=[FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    aid = accdata['accountId']
    positions = accdata['positions']
    red_df = get_red_alert_df(client, positions)
    #get_net_premium_by_expiration(client, conf)

    return render_template(
        "red_alert.html",
        RED_ALERT=red_df.loc[red_df['otm'] < .4,:].to_html()
    )

def get_red_alert_df(client: TDClient, position_data):
    #print(json.dumps(position_data, indent=4))
    flatten_positions(position_data)
    pdf = pd.DataFrame(position_data)
    pdf['currentPrice'] = 0
    symbols = pdf.loc[pdf['underlyingSymbol'].notnull(), 'underlyingSymbol'].unique()
    #print(len(symbols))
    #print(list(symbols))
    quotesj = client.get_quotes(symbols).json()
    curr_price = {}
    for ticker in quotesj:
        tdata = quotesj[ticker]
        curr_price[ticker] = tdata['lastPrice']
        pdf.loc[pdf['underlyingSymbol']==ticker, 'currentPrice'] = tdata['lastPrice']
    #print(json.dumps(quotes.json(), indent=4))
    #print(pdf.head())
    pdf['quantity'] = (pdf['longQuantity'] - pdf['shortQuantity'])
    pdf['currentValue'] = (pdf['marketValue']/abs(pdf['quantity']))/100
    pdf['pnl'] = pdf['averagePrice']/pdf['currentValue']
    pdf['otm'] = -1

    pdf['percentChange'] = (pdf['averagePrice']+pdf['currentValue'])/pdf['averagePrice']*100
    x = pdf['symbol'].str.split("_", expand=True).iloc[:,1].str.slice(start=7).astype(float)
    pdf['strikePrice'] = x
    # This is me wrestling with datetime in matrix form to calculate dte
    #pdf['emonth'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=0, stop=1).astype(int)
    #pdf['eday'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=2, stop=3).astype(int)
    #pdf['eyear'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=4, stop=5).astype(int)
    pdf['ctype'] = pdf['symbol'].str.split("_", expand=True).iloc[:, 1].str.slice(start=6, stop=7).astype(str)
    #pdf['edate'] = pd.to_datetime(pdf['symbol'].str.split("_", expand=True).iloc[:,1].str.slice(start=0, stop=6), format='%m%d%y', errors='ignore')
    #pdf['dte'] = (pdf['edate']-datetime.date.today()).dt.days
    pdf['otm'] = abs((pdf['strikePrice']/pdf['currentPrice'])-1)
    subdf = pdf.loc[
        (pdf['assetType']=="OPTION")
        & (pdf['quantity'] < 0),
        [
            'underlyingSymbol',
            'description',
            'quantity',
            'averagePrice',
            'currentValue',
            'percentChange',
            'currentPrice',
            'strikePrice',
            'otm'
        ]
    ].sort_values(['otm'])
    return subdf


def flatten_positions(pjson):
    for pdict in pjson:
        for k in pdict['instrument']:
            pdict[k] = pdict['instrument'][k]
        del(pdict['instrument'])
    #print(json.dumps(pdict[k], indent=4))
    return

def get_client(conf: Config, newtoken=False):
    if newtoken:
        client = tda.auth.client_from_manual_flow(conf.apikey, conf.callbackuri, conf.tokenpath)
    else:
        client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    return client

def get_premium(pjson):
    exp = {}
    #print(json.dumps(pjson, indent=4))
    for pos in pjson:
        if pos['instrument']['assetType'] != "OPTION":
            continue
        raw = pos["instrument"]['symbol'].split("_")[1][0:6]
        raw_exp = raw[5] + raw[4] + raw[0] + raw[1] + raw[2] + raw[3]
        if raw_exp not in exp:
            exp[raw_exp] = {
                "premium": 0.0,
                "mark": 0.0
            }
        total_premium = pos['shortQuantity'] * pos['averagePrice'] \
                        - pos['longQuantity'] * pos['averagePrice']
        exp[raw_exp]['premium'] += total_premium
        #pos['shortQuantity'] * pos['averagePrice']
        total_mark = pos['marketValue']
        #expiration = datetime.datetime.strptime(raw_exp, "%m%d%y").date()
        exp[raw_exp]['premium'] += total_premium*100
        exp[raw_exp]['mark'] += total_mark
    dlist = []
    for e in exp:
        if exp[e]['premium'] == 0:
            dlist.append(e)
    for d in dlist:
        del(exp[d])
    #print(exp)
    return exp

def get_premium_today(client: TDClient, aid):
    global TODAY
    bod = datetime.datetime.combine(TODAY, datetime.time.min)
    eod = datetime.datetime.combine(TODAY, datetime.time.max)
    orders = client.get_orders_by_path(
        aid,
        to_entered_datetime=eod,
        from_entered_datetime=bod
    )
    orders = json.loads(orders.text)
    t = 0
    for order in orders:
        try:
            ot = order['orderType']
            if ot == "TRAILING_STOP":
                continue
            price = order['price']
            quant = order['filledQuantity']
            tot = price * quant
            olc = order['orderLegCollection']
            if olc[0]['orderLegType'] != "OPTION":
                continue
            pe = None
            cot = order['complexOrderStrategyType']
            if cot == "NONE":
                for olcd in olc:
                    pe = olcd['positionEffect']
                    instruct = olcd['instruction']
                    if instruct == "SELL_TO_OPEN":
                        pass
                    elif instruct == "BUY_TO_OPEN":
                        tot *= -1
                    elif instruct == "SELL_TO_CLOSE":
                        pass
                    elif instruct == "BUY_TO_CLOSE":
                        tot *= -1
            else:
                ot = order['orderType']
                if ot == "NET_DEBIT":
                    tot *= -1
                elif ot == "NET_CREDIT":
                    pass
                else:
                    raise Exception("invalid order found {}".format(json.dumps(order, indent=4)))
            t += tot
        except Exception as e:
            print(order)
            print(e)
            pass
    #print(json.dumps(orders, indent=4))
    return t

def get_net_premium_by_expiration(client: TDClient, conf: Config):
    global ORDER_STATUS
    orders = client.get_orders_by_path(
        conf.accountnum,
        status=ORDER_STATUS.FILLED,
        max_results=10000
    )
    orders = json.loads(orders.text)
    for order in orders:
        print(json.dumps(order, indent=4))
    return

def get_order_count(client: TDClient, conf: Config,aid):
    ocount = 0
    bod = datetime.datetime.combine(TODAY, datetime.time.min)
    eod = datetime.datetime.combine(TODAY, datetime.time.max)
    orders = client.get_orders_by_path(
        conf.accountnum,
        to_entered_datetime=eod,
        from_entered_datetime=bod
    )
    orders = json.loads(orders.text)
    for order in orders:
        et = order['enteredTime']
        submit_time = datetime.datetime.strptime(et, "%Y-%m-%dT%H:%M:%S%z")
        if submit_time.date()==TODAY:
            ocount += 1
    #print(json.dumps(orders, indent=4))
    return ocount

def sut_test(pjson, sutmax=-1):
    res = []
    unweighed_calc = {
        'CALL_COUNT': 0,
        'CALL_REMAINING': sutmax,
        'CALL_PCT': 0,
        'PUT_COUNT': 0,
        'PUT_REMAINING': sutmax,
        'PUT_PCT': 0,
        "type": "unweighted"
    }
    #print(json.dumps(unweighed_calc, indent=4))
    for pos in pjson:
        p_ins = pos['instrument']
        if p_ins['assetType'] != "OPTION":
            continue
        try:
            otype = pos['instrument']['putCall']
            count_type = otype  + "_COUNT"
            remaining_type =  otype + "_REMAINING"
        except KeyError as ke:
            print(json.dumps(pos, indent=4))
            print(ke)
            sys.exit(1)
        unweighed_calc[count_type] -= pos['shortQuantity']
        unweighed_calc[count_type] += pos['longQuantity']
        unweighed_calc[remaining_type] -= pos['shortQuantity']
        unweighed_calc[remaining_type] += pos['longQuantity']
    #print(unweighed_calc)
    if unweighed_calc["CALL_REMAINING"] > sutmax:
        unweighed_calc["CALL_REMAINING"] = sutmax
    if unweighed_calc["PUT_REMAINING"] > sutmax:
        unweighed_calc["PUT_REMAINING"] = sutmax
    unweighed_calc["CALL_PCT"] = round((unweighed_calc['CALL_COUNT']/sutmax)*100, 2)
    unweighed_calc["PUT_PCT"] = round((unweighed_calc['PUT_COUNT']/sutmax)*100, 2)
    res.append(unweighed_calc)
    return res

def calc_account_data(client:TDClient, conf: Config, adata):
    acc = client.get_account(conf.accountnum).json()['securitiesAccount']
    adata['NLV'] = acc['currentBalances']['liquidationValue']
    adata['Available_BP'] = acc['currentBalances']['buyingPowerNonMarginableTrade']
    adata['BPu'] = 1-adata['Available_BP']/float(adata['NLV'])
    adata['BPu'] = round(adata['BPu']*100, 2)

    adata['Starting_NLV'] = acc['initialBalances']['liquidationValue']
    adata['Starting_BP'] = acc['initialBalances']['buyingPower']
    adata['Starting_BPu'] = 1-adata['Starting_BP']/float(adata['Starting_NLV'])
    adata['Starting_BPu'] = round(adata['Starting_BPu']*100, 2)

    adata['Max_Short_Units'] = int((adata['NLV']/float(1000)))*5
    #print(json.dumps(acc, indent=4))
    #print(json.dumps(adata, indent=4))
    pass

def setup(conf: Config, tokenpath, cfile):
    cf = {}
    print("Let's setup the configuration!")
    print("What was your APP API KEY?: ")
    conf.apikey = input()
    print("What is you callback URL?")
    conf.callbackuri = input()
    print("What is your primary account number?")
    conf.accountnum = input()
    conf.tokenpath = tokenpath
    conf.write_config(cfile)


def setup_client(conf: Config):
    #print(conf.apikey, conf.callbackuri, conf.tokenpath)
    client = tda.auth.client_from_manual_flow(conf.apikey, conf.callbackuri, conf.tokenpath)
    return client


# This is mostly dead code without a get/post form to provide a symbol.
# Leaving in case others find useful

def get_funda(client: TDClient, symbol = None):
    PROJECTIONS = TDClient.Instrument.Projection
    if symbol is None:
        symbol = ".*"
    res = client.search_instruments([symbol], PROJECTIONS.SYMBOL_REGEX)
    print(json.dumps(res.json(), indent=4))
    res = client.search_instruments([symbol], PROJECTIONS.FUNDAMENTAL)
    print(json.dumps(res.json(), indent=4))
    return


if __name__ == '__main__':
    print("Starting LottoBuddy")
    ap = argparse.ArgumentParser()
    ap.add_argument("--newtoken", action="store_true", dest='newtoken', default=False)
    ap.add_argument("--setup", action="store_true", dest="setup", default=False)
    #ap.add_argument("--configfile", dest='configfile', default=None)
    ap.add_argument("--configfile", dest='configfile', default='./lotto_config.json')
    #ap.add_argument("--tdaconfig", dest="tdaconfig", default=None)
    ap.add_argument("--tdaconfig", dest="tdaconfig", default="./tda-config.json")
    ap.add_argument("--port", dest="port", default=5000)
    # This is intended to enabling/disabling auto-refresh on dashboard
    # Currently not implemented and is hard coded to be true
    ap.add_argument("--update", default=False, action="store_true")
    args = vars(ap.parse_args())
    if args['setup']:
        if args['configfile'] is None:
            raise Exception("Config file not specified")
        args['newtoken'] = True
        setup(CONFIG, args['tdaconfig'], args['configfile'])
        #print(CONFIG)
        #setup_client()
        sys.exit()
    else:
        CONFIG.read_config(args['configfile'])
        #print(CONFIG)
    if args['newtoken'] is True:
        client = setup_client(CONFIG)
        sys.exit(0)
    app.run(
        host="0.0.0.0", port=args['port']
    )
