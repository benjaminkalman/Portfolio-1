# -*- coding: utf-8 -*-
"""
Created on Sun Apr 11 18:52:09 2021

@author: drewglov
https://github.com/drewglov/Portfolio
"""
import tkinter as tk
from tkinter import *
import tkinter.font as font
import requests
import base64
import hmac
import hashlib
import datetime, time
import websocket, json, talib, numpy
import _thread as thread
import pandas as pd
import math

fields = ('Coin Symbol', 'Trade Currency', 'Candle Length', 'RSI Periods', 'RSI Overbought Threshold', 'RSI Oversold Threshold', 'Bollinger Bands Periods', 'Band Standard Deviations', 'Your Gemini API Key', 'Your Gemini API Secret')

field_dict = {
'Coin Symbol': ['BTC', 'ETH', 'BCH', 'LTC'], 'Trade Currency':['USD', 'BTC', 'EUR', 'GBP', 'SGD'],
'Candle Length': ['1m', '5m', '15m', '30m', '1h', '6h', '1d'],
'RSI Periods': [14, 25, 50, 100], 'RSI Overbought Threshold': [70, 60, 80],
'RSI Oversold Threshold': [30, 20, 40], 'Bollinger Bands Periods': [14,25,50,100],
'Band Standard Deviations': [1.5, 1.0, 2.0], 'Unique Instance': [11, 22, 33, 44, 55],
'Your Gemini API Key': '-',
'Your Gemini API Secret': '-'
}

closes = []
bought_prices = []
opening_balance = []
crypto_start_price = []
    
buys = 0
sells = 0


def makeform(root, fields):
    def environment():
        return envar.get()
    entries = {}
    envar = StringVar(root)
    R1 = Radiobutton(root, text="Sandbox", variable=envar, value=1,command=environment)
    R1.pack(anchor=W)
    R2 = Radiobutton(root, text="Live", variable=envar, value=2,command=environment)
    R2.pack(anchor=W)
    envar.set(1)
    entries['environment'] = envar
    for field in field_dict:
        if field != 'Your Gemini API Key' and field !='Your Gemini API Secret':
            row = tk.Frame(root)
            ent = tk.Entry(row)
            ent.insert(0, str(field_dict[field][0]))
            variable = StringVar(root)
            variable.set(str(field_dict[field][0]))
            row = OptionMenu(root, variable, *field_dict[field])
            #row.config(bg='ghost white')
            lab = tk.Label(row, width=22, text=field+": ", anchor='w')
            #lab.config(bg='grey')
            row.pack(side=tk.TOP, 
                     fill=tk.X, 
                     padx=5, 
                     pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, 
                     expand=tk.YES,
                     fill=tk.X)
            entries[field] = variable
        else:
            row = tk.Frame(root)
            lab = tk.Label(row, width=22, text=field+": ", anchor='w')
            if field =='Your Gemini API Secret':
                ent = tk.Entry(row, show='*')
            else:
                ent = tk.Entry(row)
            ent.insert(0, "")
            variable = StringVar(root)
            variable.set(str(field_dict[field][0]))
            row.pack(side=tk.TOP, 
                     fill=tk.X, 
                     padx=5, 
                     pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, 
                     expand=tk.YES, 
                     fill=tk.X)
            entries[field] = ent
    return entries
    
def run_app():    
    #Parameters HERE
    coin_symbol = ents['Coin Symbol'].get()
    currency = ents['Trade Currency'].get()
    crypto = (coin_symbol+currency).lower()
    #how long to look at each close period
    #can use _1m, _5m, _15m, _30m, _1h, _6h, _1d
    candle_length = ents['Candle Length'].get()
    candle_link = 'candles_'+str(candle_length)
    
    #RSI parameters
    RSI_PERIOD = int(ents['RSI Periods'].get())
    RSI_OVERBOUGHT = int(ents['RSI Overbought Threshold'].get())
    RSI_OVERSOLD = int(ents['RSI Oversold Threshold'].get())
    
    #BB parameters
    windows = int(ents['Bollinger Bands Periods'].get())
    no_of_std = float(ents['Band Standard Deviations'].get())
    
    API_KEY = ents['Your Gemini API Key'].get()
    API_SECRET = ents['Your Gemini API Secret'].get()
    
    #This changes the nonce so you can run multiple scripts at once
    UNIQUE_INSTANCE = int(ents['Unique Instance'].get())
    
    envar = ents['environment'].get()
    if envar == "2":
        environment = "https://api.gemini.com"
        SOCKET = "wss://api.gemini.com/v2/marketdata"
    else:
        environment = "https://api.sandbox.gemini.com"
        SOCKET = "wss://api.sandbox.gemini.com/v2/marketdata"
    
    def market_order(environment, symbol, amount, price, side):
            try:
                print('Sending order')
                base_url = environment
                endpoint = "/v1/order/new"
                url = base_url + endpoint
                
                gemini_api_key = API_KEY
                gemini_api_secret = API_SECRET.encode()
                
                gemini_nonce_code = UNIQUE_INSTANCE
                
                t = datetime.datetime.now()
                #need to change the nonce so an order will send without error
                payload_nonce =  str(int(time.mktime(t.timetuple())*1000)+gemini_nonce_code+2)
                
                payload = {
                   "request": "/v1/order/new",
                    "nonce": payload_nonce,
                    "symbol": symbol,
                    "amount": amount,
                    "price": price,
                    "side": side,
                    "type": "exchange limit",
                    #by pairing an immediate or cancel with an aggressively high price, I am doing a market price buy
                    "options": ["immediate-or-cancel"] 
                }
                
                encoded_payload = json.dumps(payload).encode()
                b64 = base64.b64encode(encoded_payload)
                signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()
                
                request_headers = { 'Content-Type': "text/plain",
                                    'Content-Length': "0",
                                    'X-GEMINI-APIKEY': gemini_api_key,
                                    'X-GEMINI-PAYLOAD': b64,
                                    'X-GEMINI-SIGNATURE': signature,
                                    'Cache-Control': "no-cache" }
                
                response = requests.post(url,
                                        data=None,
                                        headers=request_headers)
                
                new_order = response.json()
                print(new_order)
                return new_order
            
            except Exception as e:
                print("an exception occured - {}".format(e))
                return False
            
    
    def get_balance(symbol, currency_traded, environment):
            try:
                global opening_balance, crypto_start_price, closes
                coin_symbol = symbol
                currency = currency_traded
                base_url = environment
                endpoint = "/v1/notionalbalances/usd"
                url = base_url + endpoint
                
                gemini_api_key = API_KEY
                gemini_api_secret = API_SECRET.encode()
                
                gemini_nonce_code = UNIQUE_INSTANCE
                
                t = datetime.datetime.now()
                payload_nonce =  str(int((time.mktime(t.timetuple())*1000)+gemini_nonce_code))
                
                payload = {
                    "nonce": payload_nonce,
                    "request": "/v1/notionalbalances/usd"
                }
                
                encoded_payload = json.dumps(payload).encode()
                b64 = base64.b64encode(encoded_payload)
                signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()
                
                request_headers = { 'Content-Type': "text/plain",
                                    'Content-Length': "0",
                                    'X-GEMINI-APIKEY': gemini_api_key,
                                    'X-GEMINI-PAYLOAD': b64,
                                    'X-GEMINI-SIGNATURE': signature,
                                    'Cache-Control': "no-cache" }
                
                balance_response = requests.post(url,
                                        data=None,
                                        headers=request_headers)
                
                current_balance = balance_response.json()
                portfolio_amounts = []
                for i in range(0, len(current_balance)):
                    #currency = current_balance[i]['currency']
                    #amount = current_balance[i]['amount']
                    amountNotional = current_balance[i]['amountNotional']
                    portfolio_amounts.append(float(amountNotional))
                
                portfolio_balance = round(sum(portfolio_amounts),2)
                print("Bal: $"+str(portfolio_balance))
                if len(opening_balance) == 0:
                    opening_balance.append(portfolio_balance)
                else:
                    pass
                if len(closes) == 1:
                    crypto_start_price.append(closes[0])
                else:
                    pass
                change = round(((portfolio_balance - opening_balance[0])/opening_balance[0])*100,2)
                print("Port. change: "+str(change)+'%')
                market_change = round(((closes[-1] - crypto_start_price[0])/crypto_start_price[0])*100,2)
                print("Mark. change: "+str(market_change)+'%')
                usd = list(filter(lambda money: money['currency'] == currency, current_balance))
                usd = round_down(float(usd[0]['amount']),2)
                coin_owned = list(filter(lambda btc: btc['currency'] == coin_symbol, current_balance))
                coin_owned = float(coin_owned[0]['amount'])
                #returning these values to rebuy and sell
                return usd, coin_owned
            
            except Exception as e:
                print("an exception occured - {}".format(e))
                return False
    
    
    def round_down(n, decimals=0):
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier        
    
    def RSI_Vote(closes_list, periods=14, overbought=70, oversold=30):
        global holding_coin, holding_cash
        if len(closes_list) > periods:
            np_closes = numpy.array(closes_list)
            rsi = talib.RSI(np_closes, periods)
            last_rsi = rsi[-1]
    
            if last_rsi > overbought:
                if holding_coin:
                    print("RSI vote SELL")
                    return 'sell'
                else:
                    print("RSI vote SELL, can't")
            
            if last_rsi < oversold:
                if holding_cash:
                    print('RSI vote BUY')
                    return 'buy'
                else:
                    print("RSI vote BUY, can't.")
                
    
    def BB_Vote(closes_list, window_num=100, num_of_std=1.5):
        global holding_coin, holding_cash
        df = pd.DataFrame(data=closes, columns={'close': closes_list})
        rolling_mean = df['close'].rolling(window_num).mean()
        rolling_std = df['close'].rolling(window_num).std()
        
        # create two new DataFrame columns to hold values of upper and lower Bollinger bands
        df['Rolling Mean'] = rolling_mean
        df['Bollinger High'] = rolling_mean + (rolling_std * num_of_std)
        df['Bollinger Low'] = rolling_mean - (rolling_std * num_of_std)
        
        df = df.dropna(subset=['Rolling Mean'])
        
        if len(df)>1:
        
            if df['close'].iloc[-1] > df['Bollinger High'].iloc[-1]:
                if holding_coin:
                    print('BB vote SELL')
                    return 'sell'
                else:
                    print("BB vote SELL, can't")
            
            if df['close'].iloc[-1] < df['Bollinger Low'].iloc[-1]:
                if holding_cash:
                    print('BB vote BUY')
                    return 'buy'
                else:
                    print("BB vote BUY, can't")
    
    def on_open(ws):
        print('Opened connection')
        def run(*args):
            ws.send(logon_msg)
        thread.start_new_thread(run, ())
        
    def on_error(ws, error):
        print('Error')
    
    def on_close(ws):
        print('Closed connection')
    
    def on_message(ws, message):
        global closes, bought_prices, buys, sells, holding_coin, holding_cash, crypto_start_price
        print("received heartbeat")
        json_message = json.loads(message)
        candle = json_message['changes']
        close = candle[0][4]
        print(coin_symbol+': $'+str(close))
        closes.append(float(close))
        if len(closes) > 150:
            del closes[0]
        print('buys: '+str(buys)+'; sells: '+str(sells))
        
        balance = get_balance(coin_symbol, currency, environment)
        usd = balance[0]
        coin = balance[1]
        
        current_price = closes[-1]
        amount2buy = round_down((usd*0.985)/current_price, 5)
        
        if coin > 0.0001:
            holding_coin = True
        else:
            holding_coin = False
            
        if usd > 0.0001:
            holding_cash = True
        else:
            holding_cash = False
        
        BVote = BB_Vote(closes_list=closes, window_num = windows, num_of_std=no_of_std)            
        RVote = RSI_Vote(closes_list=closes, periods=RSI_PERIOD, overbought=RSI_OVERBOUGHT, oversold=RSI_OVERSOLD)
        
        #Sell logic below
        if BVote == "sell" and RVote == "sell" and len(bought_prices)>= 1:
            if closes[-1] > max(bought_prices)*1.015:
                print('Enough votes to sell')
                new_order = market_order(environment, crypto, str(coin), str(current_price-10), 'sell')
                if new_order["is_cancelled"]:
                    pass
                else:
                    print('Order Succeeded')
                    sells = sells+1
            
        elif BVote == 'buy' and RVote == 'buy':
            print('Enough votes to buy')
            new_order = market_order(environment, crypto, str(amount2buy), str(current_price+10), 'buy')
            if new_order["is_cancelled"]:
                pass
            else:
                print('Order Succeeded')
                bought_price = new_order["price"]
                bought_prices.append(float(bought_price))
                buys = buys+1
        else:
            print('No order sent.')
            pass
    
    logon_msg = '{"type": "subscribe","subscriptions":[{"name":"'+candle_link+'","symbols":["'+crypto.upper()+'"]}]}'
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('GemBot Crypto Portfolio Manager')
    root.geometry('700x525')
    ents = makeform(root, field_dict)
    #photo = PhotoImage(file = "gem.png")
    #root.iconphoto(False, photo)
    
    myFont = font.Font(weight="bold")
    b1 = tk.Button(root, text='Confirm and run', command=run_app, height=1, width=17, bd=4, )
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    b1['font'] = myFont
    b2 = tk.Button(root, text='Quit', command=root.quit, height=1, width=12, bd=4)
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    b2['font'] = myFont
    root.mainloop()
