from bokeh.plotting import figure, show
from bokeh.palettes import Spectral11
from bokeh.io import show
from bokeh.sampledata.stocks import AAPL, GOOG, IBM, MSFT

import numpy as np
import pandas as pd
import yfinance as yf
from bokeh.models import Tabs, Panel

from bokeh.layouts import gridplot, layout, column, row
from bokeh.models.formatters import NumeralTickFormatter
from bokeh.models import FreehandDrawTool, Arrow, VeeHead, NormalHead, ArrowHead, BoxAnnotation, Toggle, MultiSelect, \
    CustomJS, Dropdown, PolyDrawTool


def create_figure(title="", plot_height=None, tools="no"):
    # 툴 메뉴 ("lasso_select," "poly_select," "tap," "box_select,")
    TOOLS = ("crosshair,"
             "xpan,"
             "ypan,"
             "pan,"
             "xwheel_pan,"             
             "xwheel_zoom,"             
             "box_zoom,"
             "hover,"
             "zoom_in,"
             "zoom_out,"             
             "undo,"
             "redo,"
             "reset,"
             "save,")

    # 툴팁
    TOOLTIPS = [
        ("index", "$index"),
        ("label", "@column_name"),
        ("label2", "@{multi-word column name}"),
        ("colour", "$color[hex, swatch]:fill_color")
    ]

    f = figure(
        sizing_mode="stretch_both",
        x_axis_type="datetime",
        tooltips=TOOLTIPS,
        tools=TOOLS,
        title=title,
        active_scroll="xwheel_zoom",
        active_drag="xpan",
        toolbar_location = "right",
    )
    if plot_height != None:
        f.height = plot_height

    # Auto Hide
    f.toolbar.autohide = False

    return f


def get_tab_chart(coins_list, coins_name, kind_of_price, file_name, title):
    panels = []
    for data, name, color in zip(coins_list, coins_name, Spectral11):
        f = create_figure(title)
        datetime = np.asarray(data['date'], dtype=np.datetime64)
        value = np.asarray(data[kind_of_price])
        f.line(datetime, value, line_width=2, color=color, alpha=1.0, legend_label=name)
        f.legend.location = "top_left"
        f.legend.click_policy = "hide"
        f.legend.title = title
        f.legend.title_text_font_style = "bold"
        f.legend.title_text_font_size = "20px"
        panel = Panel(child=f, title=name)
        panels.append(panel)
    tabs = Tabs(tabs=panels)
    return tabs


def get_one_chart(coins_list, coins_name, kind_of_price, file_name, title):

    f = create_figure(title)

    for data, name, color in zip(coins_list, coins_name, Spectral11):
        datetime = np.asarray(data['date'], dtype=np.datetime64)
        value = np.asarray(data[kind_of_price])
        f.line(datetime, value, line_width=2, color=color, alpha=1.0, legend_label=name)
        f.legend.location = "top_left"
        f.legend.click_policy = "hide"
        f.legend.title = title
        f.legend.title_text_font_style = "bold"
        f.legend.title_text_font_size = "20px"
    return f


def get_candlestick_tab_chart(coins_list, coins_name, file_name, title, arrow_list):
    panels = []
    for data, name, color, arrow in zip(coins_list, coins_name, Spectral11, arrow_list):
        f = _get_backtesting_dashboard(data, title, arrow)
        panel = Panel(child=f, title=name)
        panels.append(panel)

    tabs = Tabs(tabs=panels)
    return tabs

def _get_backtesting_dashboard(data, title, arrow):

    df = pd.DataFrame(data)[:]
    f = create_figure(title+" Coin", tools="yes")

    inc = df.close >= df.open
    dec = df.open > df.close

    f.segment(df.index[inc], df.high[inc], df.index[inc], df.low[inc], color="crimson")
    f.segment(df.index[dec], df.high[dec], df.index[dec], df.low[dec], color="mediumblue")
    f.vbar(df.index[inc], 0.5, df.open[inc], df.close[inc], fill_color="crimson", line_color="crimson")
    f.vbar(df.index[dec], 0.5, df.open[dec], df.close[dec], fill_color="mediumblue", line_color="mediumblue")
    f.yaxis[0].formatter = NumeralTickFormatter(format='0,0')
    major_label = {
        i: date.strftime('%Y.%m.%d') for i, date in enumerate(pd.to_datetime(df["date"]))
    }
    # major_label.update({len(df):''})
    f.xaxis.major_label_overrides = major_label
    f.xaxis.major_label_orientation = "horizontal"  # pi / 4
    f.xaxis.visible = True
    f.grid.grid_line_alpha = 1.0

    # add arrows to all spots where the lines are equal
    box_left = None
    box_right = None
    box_top = None
    box_bottom = None
    box = None
    boxes = []
    for i in range(len(arrow)):
        if arrow[i][3]=="buy":
            f.add_layout(Arrow(end=NormalHead(size=10, line_color="black", line_width=1, fill_color='lime'),
                               line_color='lime', line_width=4,
                               x_start=arrow[i][0]-1, y_start=arrow[i][1],
                               x_end=arrow[i][0], y_end=arrow[i][1]))
            box_left = arrow[i][0]
            box_bottom = arrow[i][1]
        elif arrow[i][3]=="sell":
            f.add_layout(Arrow(end=NormalHead(size=10, line_color="black", line_width=1, fill_color='yellow'),
                               line_color='yellow', line_width=4,
                               x_start=arrow[i][0]+1, y_start=arrow[i][1],
                               x_end=arrow[i][0], y_end=arrow[i][1]))
            box_right = arrow[i][0]
            box_top = arrow[i][1]
        if ((box_left != None)&(box_right != None)&(box_top != None)&(box_bottom != None)):
            if box_bottom < box_top:
                box = BoxAnnotation(left=box_left, right=box_right, bottom=box_bottom, top=box_top, fill_color='green', fill_alpha=0.2)
            else:
                box = BoxAnnotation(left=box_left, right=box_right, bottom=box_bottom, top=box_top, fill_color='red', fill_alpha=0.2)
            f.add_layout(box)
            boxes.append(box)
            box_left = None
            box_right = None
            box_top = None
            box_bottom = None
    toggle = Toggle(label="수익 및 손해 구간(활성/비활성)", button_type="success", active=True)
    for box in boxes:
        toggle.js_link('active', box, 'visible')

    p = create_figure(title+" RSI", plot_height=200)
    p.toolbar_location = None
    p.x_range = f.x_range
    p.line(df.index, df.RSI, line_width=2, color="blue", alpha=1.0, legend_label="RSI")
    p.line(df.index, 70, line_width=1, color="red", alpha=0.5, legend_label="HIGH")
    p.line(df.index, 30, line_width=1, color="red", alpha=0.5, legend_label="LOW")
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.legend.title = " "
    p.legend.title_text_font_style = "bold"
    p.legend.title_text_font_size = "20px"
    p.xaxis.major_label_overrides = major_label

    # add arrows to all spots where the lines are equal
    for i in range(len(arrow)):
        if arrow[i][3]=="buy":
            p.add_layout(Arrow(end=NormalHead(size=10, line_color="black", line_width=1, fill_color='lime'),
                               line_color='lime', line_width=4,
                               x_start=arrow[i][0]-1, y_start=arrow[i][2],
                               x_end=arrow[i][0], y_end=arrow[i][2]))
        elif arrow[i][3]=="sell":
            p.add_layout(Arrow(end=NormalHead(size=10, line_color="black", line_width=1, fill_color='yellow'),
                               line_color='yellow', line_width=4,
                               x_start=arrow[i][0]+1, y_start=arrow[i][2],
                               x_end=arrow[i][0], y_end=arrow[i][2]))

    menu = [["1", "ETH"], ["2", "BTC"], ["3", "DOGE"], ["4", "BCC"],["5", "ETH"], ["6", "BTC"], ["7", "DOGE"], ["8", "BCC"],["9", "ETH"], ["10", "BTC"], ["11", "DOGE"], ["12", "BCC"]]

    dropdowns = []
    for i in range(4):
        dropdown = Dropdown(label="Dropdown button", button_type="warning", menu=menu)
        dropdown.js_on_event("menu_item_click", CustomJS(code="console.log('dropdown: ' + this.item, this.toString())"))
        dropdowns.append(dropdown)
    all_chart = layout([
        dropdowns,
        [f],
        [p],
    ], sizing_mode="stretch_width")
    return all_chart


def get_candlestick_one_chart(data, file_name, title):

    df = pd.DataFrame(data)[:]

    f = create_figure(title)
    inc = df.close >= df.open
    dec = df.open > df.close
    f.segment(df.index[inc], df.high[inc], df.index[inc], df.low[inc], color="red")
    f.segment(df.index[dec], df.high[dec], df.index[dec], df.low[dec], color="blue")
    f.vbar(df.index[inc], 0.5, df.open[inc], df.close[inc], fill_color="red", line_color="red")
    f.vbar(df.index[dec], 0.5, df.open[dec], df.close[dec], fill_color="blue", line_color="blue")
    f.yaxis[0].formatter = NumeralTickFormatter(format='0,0')
    major_label = {
        i: date.strftime('%Y년 %m월 %d일') for i, date in enumerate(pd.to_datetime(df["date"]))
    }
    major_label.update({len(df): ''})
    f.xaxis.major_label_overrides = major_label
    f.xaxis.major_label_orientation = "horizontal"
    f.xaxis.visible = True
    f.grid.grid_line_alpha = 1.0

    return f


def get_candlestick_one_chart_with_volume(data, file_name, title):
    df = pd.DataFrame(data)[:200]

    f = create_figure(title)
    inc = df.close >= df.open
    dec = df.open > df.close
    f.segment(df.index[inc], df.high[inc], df.index[inc], df.low[inc], color="red")
    f.segment(df.index[dec], df.high[dec], df.index[dec], df.low[dec], color="blue")
    f.vbar(df.index[inc], 0.5, df.open[inc], df.close[inc], fill_color="red", line_color="red")
    f.vbar(df.index[dec], 0.5, df.open[dec], df.close[dec], fill_color="blue", line_color="blue")
    f.yaxis[0].formatter = NumeralTickFormatter(format='0,0')
    major_label = {
        i: date.strftime('%Y년 %m월 %d일') for i, date in enumerate(pd.to_datetime(df["date"]))
    }
    major_label.update({len(df): ''})
    f.xaxis.major_label_overrides = major_label
    f.xaxis.major_label_orientation = "horizontal"  # pi / 4
    f.xaxis.visible = True
    f.grid.grid_line_alpha = 1.0

    p_volumechart = create_figure("거래량 차트")
    p_volumechart.x_range = f.x_range
    p_volumechart.vbar(df.index, 0.5, df.volume, fill_color="cyan", line_color="blue")
    p_volumechart.xaxis.major_label_overrides = major_label
    p_volumechart.xaxis.major_label_orientation ="horizontal"
    p_volumechart.yaxis[0].formatter = NumeralTickFormatter(format='0,0')
    p_volumechart.grid.grid_line_alpha = 1.0

    p = gridplot([[f], [p_volumechart]], toolbar_location="left")

    return p

# def load_ticker(tickers, START, END):
#     df = yf.download(tickers, start=START, end=END)
#     print(df)
#     return df("close")

