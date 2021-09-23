
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap

from views import Chart_Manager
from models import API_BITHUMB
from models.patterns import patterns
from models.API_UPBIT import Quotation
from process import Technical_Indicator, BackTesting

from datetime import date
from random import randint

from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn

import os, csv
import yfinance as yf
from yahoofinancials import YahooFinancials
import pandas as pd
import talib

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/snapshot_stock')
def snapshot_stock():
    with open('datasets_stock/companies_stock.csv') as f:
        companies = f.read().splitlines()
        for company in companies:
            symbol = company.split(',')[0]
            df = yf.download(symbol, start="2021-01-01", end="2021-09-15")
            df.to_csv('datasets/daily/{}.csv'.format(symbol))
    return {
        'code':'success'
    }

@app.route('/snapshot_crypto')
def snapshot_crypto():    
    with open('datasets_crypto/companies_crypto.csv') as f:
        tickers = f.read().splitlines()
        for oneLine in tickers:
            ticker = oneLine.split(',')[0]                        
            yahoo_financials = YahooFinancials(ticker+"-USD")
            data = yahoo_financials.get_historical_price_data(start_date='2019-01-01', 
                                                              end_date='2019-12-31', 
                                                              time_interval='weekly')                            
            df = pd.DataFrame(data[ticker+"-USD"]['prices'])            
            df.rename(columns={
                "date":"raw_date",
                "high":"High",
                "low":"Low",
                "open":"Open",
                "close":"Close",
                "volume":"Volume",
                "formatted_date":"Date"},inplace=True)            
            df.to_csv('datasets_crypto/daily/{}.csv'.format(ticker))

    return {
        'code':'success'
    }


@app.route('/recommend_pattern')
def recommend_pattern():
    type = request.args.get('type', None)
    pattern = request.args.get('pattern', None)
    stocks = {}        

    if pattern:
        companies_file_name = 'companies_'+type+'.csv'        
        with open('datasets_'+type+'/'+companies_file_name) as f:
            for row in csv.reader(f):
                stocks[row[0]]={'company': row[1]}

        datafiles = os.listdir('datasets_'+type+'/daily')
        for filename in datafiles:
            df = pd.read_csv('datasets_'+type+'/daily/{}'.format(filename))            
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0]            
            try :
                result = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])                
                last = result.tail(1).values[0]                
                if last > 0:
                    stocks[symbol][pattern] = 'Bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'Bearish'
                else:
                    stocks[symbol][pattern] = None
            except:
                pass          
    return render_template('recommend_pattern.html', patterns=patterns, stocks=stocks, current_pattern=pattern, type=type)


@app.route('/backtesting')
def backtesting():   
    ticker = 'DOGE'
    period_list= ['1h','6h','12h','24h']
    final_param = [0, 0, 0, 0, 0, 0]
    매수방법 = ["RSI"]
    매도방법 = ["RSI"]
    start_date='2021-04-01'
    end_date='2021-09-06'

    # 수수료율이 0.25%, 초기 투자금이 1백만원인 경우로 백테스트
    fee = 0.0025
    invest = 1_000_000

    coins_list = []
    arrow_list = []
    for period in period_list:

        """ 데이터 불러오기 """
        df = API_BITHUMB.call_data_from_bithumb(period=period, ticker=ticker, start_date=start_date, end_date=end_date)
        coins_list.append(df)

        method_set = set(매수방법+매도방법)
        methods = list(method_set)
        for 보조지표 in methods:
            param = [0, 0, 0, 0, 0, 0]
            if 보조지표 == "MACD":
                df = Technical_Indicator.get_MACD(df, 12, 26, 9)
            elif 보조지표 == "GoldenCross":
                df = Technical_Indicator.get_GoldenCross(df, 12, 26, 9)
            elif 보조지표 == "RSI":
                df = Technical_Indicator.get_RSI(df, 14, 30, 70)
            elif 보조지표 == "stochastic":
                df = Technical_Indicator.get_Stochastic(df, 14, 1, 3)
            elif 보조지표 == "bb":
                df = Technical_Indicator.get_BB(df)
            else:
                pass
    
        수익금, 수익률, 거래횟수, 매매결과 = BackTesting.backtesting(df, 보조지표, period, fee, invest)
        # df.to_excel(period+'.xlsx')
        coins_list.append(df)
        arrow_list.append(매매결과)
        print("<시작날짜 : {0},  {1}기간, {2}봉 백테스팅 결과> {3}만원 투자시 예상수익 : {4}원, 예상수익률 : {5}%, 거래횟수 : {6} ".format(df['date'].iloc[0], period, len(df), int(invest / 10000),format(int(수익금), ","),format(수익률, '.2f'), 거래횟수))

    fig = Chart_Manager.get_candlestick_tab_chart(coins_list, period_list, "a.html", ticker, arrow_list)
    return _render_result(fig)


@app.route('/one_chart')
def one_chart():   
    # UPBIT
    ticker="KRW-DOGE"
    data = Quotation.get_ohlcv(ticker, interval="day", count=200, to=None)    
    fig = Chart_Manager.get_candlestick_one_chart_with_volume(data, "Cripto Chart")
    fig = Chart_Manager.get_candlestick_one_chart(data, ticker)
    return _render_result(fig)

@app.route('/tab_chart')
def tab_chart():  
    # UPBIT
    data1 = Quotation.get_ohlcv("KRW-BTC", interval="day", count=200, to=None)
    data2 = Quotation.get_ohlcv("KRW-DOGE", interval="day", count=200, to=None)
    fig = Chart_Manager.get_candlestick_one_chart_with_volume([data1, data2], ["BTC", "DOGE"], "Cripto Chart")
    return _render_result(fig)

@app.route('/table_chart')
def table_chart():  
    data = dict(
        dates=[date(2014, 3, i+1) for i in range(20)],
        downloads=[randint(0, 100) for i in range(20)],
    )
    source = ColumnDataSource(data)

    columns = [
        TableColumn(field="dates", title="Date", formatter=DateFormatter()),
        TableColumn(field="downloads", title="Downloads"),
    ]
    data_table = DataTable(source=source, columns=columns, width=800, height=280)
    return _render_result(data_table)


def _render_result(fig):
    # render template
    script, div = components(fig)
    render_result = render_template(
        'chart.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')   

    return  render_result

if __name__ == '__name__':
    app.run()