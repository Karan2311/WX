#import xlwings
import pandas as pd
import requests
#import time
import warnings
warnings.filterwarnings('ignore')
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# update every 5 mins
st_autorefresh(interval=10000, key="dataframerefresh")

#to get data in excel sheet
#wb =  xlwings.Book('WX_live_data.xlsx').sheets('Sheet1')
#wb =  xlwings.Book('WX_live_data_2.xlsx').sheets('Sheet1')



def wx_live_data():
    
    #pd.set_option("display.precision", 8)
    pd.options.display.float_format = '{:.9f}'.format
    r = requests.get('https://api.wazirx.com/api/v2/market-status')         #wazirx
    #r = requests.get('https://api.binance.com/api/v3/ticker/price?')       #binance
    df = pd.json_normalize(r.json(),'markets')
    cols_to_retain = ['baseMarket','quoteMarket','status','last','type','volume','sell','buy']
    df1 = df[cols_to_retain]
    df2 = df1[(df1['quoteMarket']=='inr') | (df1['quoteMarket']=='usdt')]
    df3 = df2[(df2['status']=='active') & (df2['type']=='SPOT')]
    df4 = df3.drop(['status','type'],axis=1)
    df4.rename(columns = {'baseMarket':'Coin','quoteMarket':'Pair','last':'Price','volume':'Volume','sell':'Seller','buy':'Buyer'}, inplace = True)
    df4 = df4[['Coin','Pair','Price','Buyer','Seller','Volume']]
    df4['Price'] = df4['Price'].astype(float)
    df4['Buyer'] = df4['Buyer'].astype(float)
    df4['Seller'] = df4['Seller'].astype(float)
    df4['Volume'] = df4['Volume'].astype(float)
    df5 = df4[(df4['Pair']=='inr')]
    df5['Volume_INR'] = df5['Volume'] * df5['Price']
    usdtinr = df5.loc[df5['Coin'] == 'usdt','Price'].iloc[0]
    df6 = df4[(df4['Pair']=='usdt')]
    df6['Price'] = df6['Price'] * usdtinr
    df6['Buyer'] = df6['Buyer'] * usdtinr
    df6['Seller'] = df6['Seller'] * usdtinr
    df6['Volume_INR'] = df6['Volume'] * df6['Price']
    final_df = pd.merge(df5, df6, on="Coin")
    final_df['Buyer_diff'] = 100* (final_df['Buyer_x'] - final_df['Buyer_y'])/final_df['Buyer_y']
    final_df.sort_values('Volume_INR_y',ascending=False,inplace=True)
    return final_df 
    #to get data in excel sheet
    #wb.range('a1').options(pandas.DataFrame,index=False).value = df
    #wb.range('a1').options(pandas.DataFrame,index=False).value = pandas.json_normalize(r.json())

#if __name__ == '__main__':
    #while True:
st.header("WX Live Data")
st.dataframe(wx_live_data())
    #time.sleep(10)
