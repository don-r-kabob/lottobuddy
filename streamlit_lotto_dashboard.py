import datetime

import streamlit as st
import argparse
import tda
import pandas as pd
from flask_buddy import Config

import flask_buddy as fb
from streamlit_autorefresh import st_autorefresh

## Settings commands

REFRESH_TIME_MS = 1000*120
refresh_count = 0
st.set_page_config(layout="wide")
st_autorefresh(REFRESH_TIME_MS, key=refresh_count)


#### Globals

CONFIG: Config = Config()
ACCOUNT_DATA: dict = fb.ACCOUNT_DATA


#@st.caching
def main(**argv):
    global CONFIG, ACCOUNT_DATA
    conf = CONFIG
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    fb.calc_account_data(client, conf, fb.ACCOUNT_DATA)
    acc_json = client.get_account(conf.accountnum, fields=[fb.FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    st.write("Updated - {}".format(datetime.datetime.now()))

    with st.sidebar:
        with st.expander(
                "Account Stats",
                expanded=True
        ):
            #st.write("Account Stats")
            #st.write("NLV: {}".format(fb.ACCOUNT_DATA['NLV']))
            #st.write("BP: {}".format(fb.ACCOUNT_DATA['BP_Available']))
            #st.write("BPu: {}".format(fb.ACCOUNT_DATA['BPu']))
            #acc_df = pd.DataFrame.from_dict(fb.ACCOUNT_DATA, orient='columns', index=[0])
            acc_df = pd.DataFrame(fb.ACCOUNT_DATA, index=["Stats"])
            sidebar_df = acc_df.drop(columns=['Starting_NLV', 'Starting_BP', 'Starting_BPu', "Max_Short_Units"])
            sidebar_df['BPu'] = sidebar_df['BPu'].astype(int)
            st.table(sidebar_df.T)

    st.title("Lotto Dashboard")
    #with st.expander("Account"):
    #    pass
    #    st.write(fb.ACCOUNT_DATA)
    #ee    #sutdf = fb.sut_test()

    with st.expander(
        "Today's stats",
        expanded=True
    ):
        st.header("Today's Stats")
        try:
            todays_premium = round(fb.get_premium_today(client, conf.accountnum)*100,2)
            if todays_premium is None:
                todays_premium = 0
            todays_pct = round(todays_premium/fb.ACCOUNT_DATA['NLV']*100,2)
            order_counts = fb.get_order_count(client, conf, conf.accountnum)
        except Exception as e:
            print(e)
            raise e
        col1, col_2 = st.columns(2)
        col1.write("Today's Premium:")
        col_2.write("\t{} ({}%)".format(todays_premium, todays_pct))
        col1.write("Today's Orders:")
        col_2.write("\t{}".format(order_counts))
    with st.expander(
        "Short Unit Test",
        expanded=True
    ):
        st.header("Short Unit Test", )
        sutdf = fb.sut_test(positions, ACCOUNT_DATA['Max_Short_Units'])
        sdf = pd.DataFrame(sutdf, index=[0])
        sdf.index = sdf['type'].astype(str)
        sdf = sdf.drop(columns=['type'])
        method_list = sdf.index
        method = st.selectbox(
            "Calculation Method",
            method_list,
            index=0
        )
        st.write("SUT Max: {}".format(fb.ACCOUNT_DATA['Max_Short_Units']))

        sut_col1, sut_col2 = st.columns(2)
                #print(idx)
                #print(sdf.loc[idx,:])
        mdf = sdf.loc[method,:]
        calls = [
            #["SUT Max", fb.ACCOUNT_DATA['Max_Short_Units']],
            ["Unit Count", int(mdf['CALL_COUNT'])],
            ["Units remaining", int(mdf['CALL_REMAINING'])],
            ["Call Percent Used", (int(mdf['CALL_PCT_USED']))]
            #["Call Percent Used", "{}%%".format(int(mdf['CALL_PCT_USED']))]
        ]
        puts = [
            ["Unit Count", int(mdf['PUT_COUNT'])],
            ["Units remaining", int(mdf['PUT_REMAINING'])],
            ["Percent Used", int(mdf['PUT_PCT_USED'])]
        ]
        #sut_col1.write(method)
        sut_col1.subheader("Call SUT")
        sut_col1.table(calls)
        sut_col2.subheader("Put SUT")
        sut_col2.table(puts)
        #sut_col2.table(sdf.loc[method,:].T)



        #print(sdf)
        #sut_col1.write("Moo")
        #sut_col2.table(sdf.T)
        #for sut_calc in sutdf:
        #    method = sut_calc['type']
        #    del(sut_calc['type'])
        #    print(sut_calc)
        #    sdf = pd.DataFrame(sut_calc)
        #    sut_col1.write("{}:".format(method))
        #    sut_col2.table(sdf, index=[0])

    with st.expander(
        "Red Alert! - Threatened Postions",
        expanded=True
    ):
        otm_select_values = ("40", "35", "30", "25", "20", "15", "10")
        min_otm_select_value = st.selectbox(
            "Min Percent OTM",
            otm_select_values,
            index=2
        )
        min_otm = int(min_otm_select_value)/100.0
        print(min_otm)
        red_alert_df = fb.get_red_alert_df(client, positions)
        st.dataframe(
            red_alert_df.loc[red_alert_df['otm'] < min_otm, :]
        )



if __name__ == '__main__':
    print("Starting LottoBuddy")
    CONFIG = Config()
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--configfile",
        dest='configfile',
        default='./lotto_config.json',
        metavar="[lotto_config.json]",
        help="Configuration file with TDA APP data created with --setup"
    )
    #ap.add_argument("--tdaconfig", dest="tdaconfig", default=None)
    ap.add_argument(
        "--tdaconfig",
        dest="tdaconfig",
        default="./tda-config.json",
        metavar="[tda-config.json]",
        help="Config file name for where to store TDA API token. Default: ./tda-config.json")
    ap.add_argument(
        "--port",
        dest="port",
        default=5000,
        metavar="int",
        help="Change flask port from default 5000. This is important for Mac's because 5000 is taken by airply by default"
    )
    # This is intended to enabling/disabling auto-refresh on dashboard
    # Currently not implemented and is hard coded to be true
    ap.add_argument("--update", default=False, action="store_true")
    args = vars(ap.parse_args())
    CONFIG.read_config(args['configfile'])
    st.session_state['configfile'] = args['configfile']
    st.session_state['tdaconfig'] = args['tdaconfig']
    main(**args)

