import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import tda
import streamlit_lotto_dashboard as sb
import flask_buddy as fb
from flask_buddy import Config

print(__name__)
print(st.session_state['configfile'])

CONFIG = Config()
CONFIG.read_config(
    config_file=st.session_state['configfile']
)

plot = "Open Contracts"
by = "Expiration"
ptype = "Barplot"

def plot_open_contracts_by_expiration(plot_type):
    global CONFIG
    conf = CONFIG
    print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[fb.FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    p = {}
    d = []
    #df = pd.DataFrame()
    #df.columns = ['exp', 'ptype', 'count']
    for pentry in positions:
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            raw = pentry["instrument"]['symbol'].split("_")[1][0:6]
            raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
            if raw_exp not in p:
                p[raw_exp] = {
                "long": 0.0,
                "short": 0.0
            }
            p[raw_exp]['long'] += pentry['longQuantity']
            p[raw_exp]['short'] += pentry['shortQuantity']
    for exp in p:
        for ptype in p[exp]:
            d.append([exp, ptype, p[exp][ptype]])
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['exp', 'ptype', 'count']
    print(df.head())
    if plot_type == "Barplot":
        fig, ax = plt.subplots()
        sns.barplot(
            ax=ax,
            data=df,
            x="exp",
            y="count",
            hue="ptype"
        )
        ax.set_title("Contract count by expiration")
        for xtl in ax.get_xticklabels():
            xtl.set_rotation(90)
        fig.tight_layout()
        return fig,ax

def get_outstanding_premium_by_expiration(plot_type):
    global CONFIG
    conf = CONFIG
    #print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[fb.FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    p = {}
    d = []
    #df = pd.DataFrame()
    #df.columns = ['exp', 'ptype', 'count']
    for pentry in positions:
        pins = pentry['instrument']
        if pins['assetType'] == "OPTION":
            raw = pentry["instrument"]['symbol'].split("_")[1][0:6]
            raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
            if raw_exp not in p:
                p[raw_exp] = {
                "Current Mark": 0.0,
                "Opening Price": 0.0
            }
            p[raw_exp]['Current Mark'] += abs(pentry['marketValue'])
            p[raw_exp]['Opening Price'] += (
                (pentry['longQuantity'] + pentry['shortQuantity']) * pentry['averagePrice']*100
            )
    for exp in p:
        for ptype in p[exp]:
            d.append([exp, ptype, p[exp][ptype]])
    #df = pd.DataFrame.from_dict(p, orient='columns')
    df = pd.DataFrame(d)
    df.columns = ['Expiration', 'Measure', 'Value']
    return df
    #print(df.head())

def get_otm_df():
    global CONFIG
    conf = CONFIG
    #print(conf)
    client = tda.auth.easy_client(conf.apikey, conf.callbackuri, conf.tokenpath)
    acc_json = client.get_account(conf.accountnum, fields=[fb.FIELDS.POSITIONS]).json()
    accdata = acc_json['securitiesAccount']
    positions = accdata['positions']
    df = fb.get_red_alert_df2(client, positions)
    df['expiration'] = "000101"
    for idx in df.index:
        sym = df.loc[idx,'symbol']
        raw = sym.split("_")[1][0:6]
        raw_exp = raw[4] + raw[5] + raw[0] + raw[1] + raw[2] + raw[3]
        df.loc[idx, 'expiration'] = raw_exp
    return df.drop(columns='symbol')

fig = None
ax = None
table = None

with st.expander(
    "Plot Selection",
    expanded=True
):
    plot_what = st.selectbox(
        "Plot what?",
        (
            "None",
            "Percent OTM",
            "Open Contracts",
            "Outstanding premium from open positions"
        ),
        index=0
    )
    if plot_what == "Percent OTM":
        plot_by = st.selectbox(
            "Show - Percent OTM by?",
            (
                "None",
                "Table",
                "Total",
                "By Expiration and type"
            )
        )
    if plot_what == "Open Contracts":
        plot_by = st.selectbox(
            "Open Contract - By:",
            (
                "None",
                "Expiration"
            )
        )
        if plot_by == "Expiration":
            plot_type = st.selectbox(
                "Open Contracts by Expiration - How?",
                (
                    "None",
                    "Barplot",
                    "Table"
                ),
                index=0
            )
            #if plot_type == "Barplot":
            #    plot_by = st.selectbox(
            #        "Plot - Open Contracts barplot by expiration:",
                    #(
                     #   "None",
                     #   "Expiration"
                    #)
                #)
                #if plot_by == "Expiration":
                #    plot_type = st.selectbox(
                #    "Plot Type",
                #    (
                #        "None",
                #        "Barplot"
                #    ),
                #    index=0
                #)
    if plot_what == "Outstanding premium from open positions":
        plot_by = st.selectbox(
            "Plot - Outstanding premium By?",
            (
                "None",
                "Expiration"
            )
        )
        if plot_by == "Expiration":
            plot_type = st.selectbox(
                "Plot - Outstanding Premium by expiration how?",
                (
                    "None",
                    "Barplot",
                    "Table"
                ),
                index=0
            )
            if plot_type == "Barplot":
                hue_set = st.selectbox(
                    "Measures to show",
                    (
                        "All",
                        "Opening Price",
                        "Current Mark"
                    ),
                    index=0
                )



with st.container():
    with st.spinner("Loading plot"):
        if plot_what == "Open Contracts":
            if plot_by == "Expiration":
                if plot_type == "Barplot":
                    fig, ax = plot_open_contracts_by_expiration(plot_type)
        elif plot_what == "Outstanding premium from open positions":
            if plot_by == "Expiration":
                if plot_type == "Barplot":
                    print("Making plot")
                    datadf = get_outstanding_premium_by_expiration(plot_type).sort_values("Expiration")
                    if hue_set != "All":
                        datadf = datadf.loc[datadf['Measure']==hue_set,:]
                    fig, ax = plt.subplots()
                    sns.barplot(ax=ax, data=datadf, x="Value", y="Expiration", hue="Measure")
                    ax.set_title("Outstanding Premium barplot by expiration")
                    for container in ax.containers:
                        ax.bar_label(container)
                if plot_type == "Table":
                    table = get_outstanding_premium_by_expiration(plot_type).sort_values("Expiration")
                    print(type(table))
        elif plot_what == "Percent OTM":
            if plot_by != "None":
                table = get_otm_df()
                if plot_by == "Total":
                    table['otm'] = table['otm']*100
                    fig, ax = plt.subplots()
                    sns.histplot(ax=ax, data=table, x='otm')
                    fig.suptitle("Histogram of position %OTM")
                    ax.set_xlabel("% OTM")
                if plot_by == "By Expiration and type":
                    table['otm'] = table['otm']*100
                    table.loc[table['ctype']=='C','ctype'] = "Call"
                    table.loc[table['ctype']=='P','ctype'] = "Put"
                    fg = sns.FacetGrid(data=table, col='expiration', row='ctype')
                    fig = fg.fig
                    fg.map_dataframe(sns.histplot, x="otm")
                    fig.suptitle("Position %OTM histogram for each contract type and expiration")
                    fig.tight_layout()


if fig is not None:
    st.pyplot(fig)
elif table is not None:
    st.dataframe(table)
else:
    st.write("No Plot To Show")
