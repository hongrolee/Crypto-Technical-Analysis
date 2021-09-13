from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from models.API_UPBIT import *
from models.API_BITHUMB import *
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn
from views.Chart_Manager import Chart_Manager

from datetime import date
from random import randint

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE

app = Flask(__name__)
bootstrap = Bootstrap(app)
quotation = Quotation()
exchange = Exchange("","")
bithumb = C_BITHUMB()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/one_chart')
def one_chart():   
    # BITHUMB
    # data = bithumb.call_data_from_bithumb('6h', ticker='DOGE', start_date='2021-07-30', end_date='2021-08-19')
    # chart_mng = Chart_Manager()
    # fig = chart_mng.get_candlestick_one_chart_with_volume(data, "adf.html", "Cripto Chart")

    # data1 = bithumb.call_data_from_bithumb('6h', ticker='DOGE', start_date='2021-06-07', end_date='2021-08-19')
    # data2 = bithumb.call_data_from_bithumb('6h', ticker='ETH', start_date='2021-06-07', end_date='2021-08-19')
    # chart_mng = Chart_Manager()
    # fig = chart_mng.get_candlestick_one_chart(data1, data2], ["BTC", "DOGE"],"close", "adf.html", "Cripto Chart")

    # data1 = quotation.get_ohlcv("KRW-BTC", interval="day")
    # data2 = quotation.get_ohlcv("KRW-DOGE", interval="day")
    # chart_mng = Chart_Manager()
    # fig = chart_mng.get_tab_chart([data1, data2], ["BTC", "DOGE"],"close", "adf.html", "Cripto Chart")

    # UPBIT
    ticker="KRW-DOGE"
    data = quotation.get_ohlcv(ticker, interval="day", count=200, to=None)
    chart_mng = Chart_Manager()
    fig = chart_mng.get_candlestick_one_chart_with_volume(data, "Cripto Chart")
    fig = chart_mng.get_candlestick_one_chart(data, ticker)
    return render_result(fig)


@app.route('/tab_chart')
def tab_chart():  
    # UPBIT
    data1 = quotation.get_ohlcv("KRW-BTC", interval="day", count=200, to=None)
    data2 = quotation.get_ohlcv("KRW-DOGE", interval="day", count=200, to=None)
    chart_mng = Chart_Manager()
    fig = chart_mng.get_candlestick_tab_chart([data1, data2], ["BTC", "DOGE"], "Cripto Chart")
    return render_result(fig)


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
    return render_result(data_table)

def render_result(fig):
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