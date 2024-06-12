#import xlwings
import pandas as pd
import requests
#import time
import warnings
warnings.filterwarnings('ignore')
import streamlit as st
import json

#st.header("App loaded")
#from streamlit_autorefresh import st_autorefresh

# update every 60 seconds
#st_autorefresh(interval=60*1000, key="dataframerefresh")

#to get data in excel sheet
#wb =  xlwings.Book('WX_live_data.xlsx').sheets('Sheet1')
#wb =  xlwings.Book('WX_live_data_2.xlsx').sheets('Sheet1')

def wx_live_data():
    #pd.options.display.float_format = '{:.9f}'.formats
    wrx_api = requests.get('https://api.wazirx.com/api/v2/market-status')
    wrx_all = pd.json_normalize(wrx_api.json(),'markets')
    cols_to_retain = ['baseMarket','quoteMarket','status','last','type','volume','sell','buy']
    wrx_filtered = wrx_all[cols_to_retain]
    wrx_filtered = wrx_filtered[(wrx_filtered['quoteMarket']=='inr') | (wrx_filtered['quoteMarket']=='usdt')]
    wrx_filtered = wrx_filtered[(wrx_filtered['status']=='active') & (wrx_filtered['type']=='SPOT')]
    wrx_filtered = wrx_filtered.drop(['status','type'],axis=1)
    wrx_filtered.rename(columns = {'baseMarket':'Coin','quoteMarket':'Pair','last':'Price','volume':'Volume','sell':'Seller','buy':'Buyer'}, inplace = True)
    wrx_filtered = wrx_filtered[['Coin','Pair','Price','Buyer','Seller','Volume']]
    wrx_filtered['Price'] = wrx_filtered['Price'].astype(float)
    wrx_filtered['Buyer'] = wrx_filtered['Buyer'].astype(float)
    wrx_filtered['Seller'] = wrx_filtered['Seller'].astype(float)
    wrx_filtered['Volume'] = wrx_filtered['Volume'].astype(float)
    wrx_inr = wrx_filtered[(wrx_filtered['Pair']=='inr')]
    wrx_inr['Volume_INR'] = wrx_inr['Volume'] * wrx_inr['Price']
    usdtinr = wrx_inr.loc[wrx_inr['Coin'] == 'usdt','Price'].iloc[0]
    wrx_usdt = wrx_filtered[(wrx_filtered['Pair']=='usdt')]
    wrx_usdt['Price'] = wrx_usdt['Price'] * usdtinr
    wrx_usdt['Buyer'] = wrx_usdt['Buyer'] * usdtinr
    wrx_usdt['Seller'] = wrx_usdt['Seller'] * usdtinr
    wrx_usdt['Volume_INR'] = wrx_usdt['Volume'] * wrx_usdt['Price']
    wrx_inr_usdt_compare = pd.merge(wrx_inr, wrx_usdt, on="Coin")
    wrx_inr_usdt_compare['Buyer_diff_%'] = 100* (wrx_inr_usdt_compare['Buyer_x'] - wrx_inr_usdt_compare['Buyer_y'])/wrx_inr_usdt_compare['Buyer_y']
    wrx_inr_usdt_compare.sort_values('Buyer_diff_%',ascending=False,inplace=True)
    wrx_inr_usdt_compare = wrx_inr_usdt_compare[['Coin','Buyer_diff_%','Price_x','Buyer_x','Seller_x','Volume_INR_x','Price_y','Buyer_y','Seller_y','Volume_INR_y']]
    wrx_inr_usdt_compare.rename(columns = {'Price_x':'Price(I)','Buyer_x':'Buyer(I)','Seller_x':'Seller(I)','Volume_INR_x':'Volume(I)','Price_y':'Price(U)','Buyer_y':'Buyer(U)','Seller_y':'Seller(U)','Volume_INR_y':'Volume(U)'}, inplace = True)

    ##_________________Binance___________________________
    
    # bnc_api_url = "https://api.binance.com/api/v3/ticker/price"
    # bnc_api = requests.get(bnc_api_url)
    # bnc = pd.json_normalize(bnc_api.json())
    # #st.dataframe(bnc)
    # bnc.rename(columns ={'symbol' : 'coinpair','price':'binance_price'},inplace=True)

    ##______________Coin Market Cap_____________________

    API_KEY = '8f69dacd-7013-4ce1-9207-13c9acca41d4'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

    HEADERS = {'Accepts': 'application/json','X-CMC_PRO_API_KEY': API_KEY}

    PARAMS = {'convert': 'USD','limit': 2000}

    resp = requests.get(url, headers=HEADERS, params=PARAMS)

    data = json.loads(resp.content)['data']
    rows = list()

    for item in data:
        rows.append([
              item['symbol'], 
              item['quote']['USD']['price'],
              #item['quote']['USD']['volume_24h'],
              #item['quote']['USD']['last_updated']
              ])

    cmc = pd.DataFrame(rows, columns=['symbol','cmc_price'])
    #cmc.groupby('symbol').apply(pd.DataFrame.sort_values, by='cmc_price').reset_index(drop=True)#.iloc[0,:]
    filtered_cmc = cmc.drop(cmc[cmc['symbol'] == 'QUICK'].index)
    filtered_cmc = filtered_cmc.drop(filtered_cmc[filtered_cmc['symbol'] == 'ONE'].index)
    cmc = filtered_cmc.drop(filtered_cmc[filtered_cmc['symbol'] == 'STRK'].index)
    #st.header("CMC")
    #st.write(cmc)
    wrx_usdt_1 = wrx_filtered[(wrx_filtered['Pair']=='usdt')]
    #wrx_usdt_1['coinpair'] = wrx_usdt_1['Coin'] + wrx_usdt_1['Pair']
    wrx_usdt_1['Coin'] = wrx_usdt_1['Coin'].str.upper()
    #st.write(wrx_usdt_1.columns.to_list())
    #st.write(bnc.columns.to_list())
    wrx_cmc_compare = wrx_usdt_1.merge(cmc, left_on = 'Coin',right_on = 'symbol', how = 'left')
    wrx_cmc_compare['cmc_price'] = wrx_cmc_compare['cmc_price'].astype(float)
    top_seller = wrx_cmc_compare[wrx_cmc_compare['Seller'] < wrx_cmc_compare['cmc_price']]
    top_seller['%_diff'] = 100 * (top_seller['cmc_price'] - top_seller['Seller'])/top_seller['cmc_price']
    top_seller.sort_values('%_diff',ascending=False,inplace=True)
    top_seller = top_seller[['Coin','%_diff','cmc_price','Price','Buyer','Seller','Volume']]
    top_seller.rename(columns = {'cmc_price':'CMC Price','Price':'WazirX Price'}, inplace = True)


    return wrx_inr_usdt_compare,top_seller

    #to get data in excel sheet
    #wb.range('a1').options(pandas.DataFrame,index=False).value = df
    #wb.range('a1').options(pandas.DataFrame,index=False).value = pandas.json_normalize(r.json())

#if __name__ == '__main__':
    #while True:
st.header("WX Live Data")
df1,df2 = wx_live_data()
st.write("Coins with large difference in INR vs USDT pair price")
st.dataframe(df1)
st.write("Coins with large difference in WazirX vs CMC price")
st.dataframe(df2)
    #time.sleep(10)