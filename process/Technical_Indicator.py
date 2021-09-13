import ta
import numpy as np

def get_GoldenCross(df, gc_short=3, gc_long=20, ma_signal=2):
    df["GoldenCross_short"] = df["close"].rolling(gc_short).mean().shift(1)
    df["GoldenCross_long"] = df["close"].rolling(gc_long).mean().shift(1)
    df["GoldenCross"] = df["GoldenCross_short"]
    condition = (df['GoldenCross_short']>df['GoldenCross_long'])&(df['GoldenCross_long'].pct_change()>0)
    df["GoldenCross_sign"] =np.where(condition,"매수", "매도")
    df.iloc[-1,-1]="매도"
    return df


def get_MACD(df, short=12, long=26, signal=9):
    df["MACD_short"] = df["close"].ewm(span=short).mean()
    df["MACD_long"] = df["close"].ewm(span=long).mean()
    df["MACD"] = df.apply(lambda x: (x["MACD_short"] - x["MACD_long"]), axis=1)
    df["MACD_signal"] = df["MACD"].ewm(span=signal).mean()
    df["MACD_oscillator"] = df.apply(lambda x: (x["MACD"] - x["MACD_signal"]), axis=1)
    df["MACD_sign"] = df.apply(lambda x: ("매수" if x["MACD"] > x["MACD_signal"] else "매도"), axis=1)
    return df


def get_RSI(df, RSI_n=14, RSI_low=30, RSI_high=70):
    # # i가 0일때는 전일값이 없어서 제외함, i는 데이터프레임의 index값
    # df["등락"] = [df.loc[i, 'close'] - df.loc[i - 1, 'close'] if i > 0 else 0 for i in range(len(df))]
    # # U(up): n일 동안의 종가 상승 분
    # df["RSI_U"] = df["등락"].apply(lambda x: x if x > 0 else 0)
    # # D(down): n일 동안의 종가 하락 분 --> 음수를 양수로 바꿔줌
    # df["RSI_D"] = df["등락"].apply(lambda x: x * (-1) if x < 0 else 0)
    # # AU(average ups): U값의 평균
    # df["RSI_AU"] = df["RSI_U"].rolling(RSI_n).mean()
    # # DU(average downs): D값의 평균
    # df["RSI_AD"] = df["RSI_D"].rolling(RSI_n).mean()
    # df["RSI"] = df.apply(lambda x: x["RSI_AU"] / (x["RSI_AU"] + x["RSI_AD"]) * 100, 1)
    df["RSI"] = ta.momentum.RSIIndicator(df['close'], window=RSI_n).rsi()
    df["RSI_sign"] = df["RSI"].apply(lambda x: "매수" if x < RSI_low else ("매도" if x > RSI_high else "대기"))
    return df


def get_Stochastic(df, sto_N=14, sto_m=1, sto_t=3):

    # 스토캐스틱 %K (fast %K) = (현재가격-N일중 최저가)/(N일중 최고가-N일중 최저가) ×100
    df["max%d" % sto_N] = df["고가"].rolling(sto_N).max()  # 오타 수정 : 저가 --> 고가
    df["min%d" % sto_N] = df["저가"].rolling(sto_N).min()
    df["stochastic%K"] = df.apply(lambda x: 100 * (x["Close"] - x["min%d" % sto_N]) /
                                            (x["max%d" % sto_N] - x["min%d" % sto_N])
    if (x["max%d" % sto_N] - x["min%d" % sto_N]) != 0 else 50, 1)

    # 스토캐스틱 %D (fast %D) = m일 동안 %K 평균 = Slow %K
    # slow %K = 위에서 구한 스토캐스틱 %D
    df["slow_%K"] = df["stochastic%K"].rolling(sto_m).mean()

    # slow %D = t일 동안의 slow %K 평균
    df["slow_%D"] = df["slow_%K"].rolling(sto_t).mean()

    # 50일 이동평균선
    df["MA50"] = df["Close"].rolling(50).mean()

    # slow%K선이 slow%D를 골든크로스하고, 현재 종가가 MA50보다 클 때, 매수
    # 반대일 경우, 매도하도록 설정해보겠습니다.
    # df[["max%d"%sto_N,"min%d"%sto_N,"stochastic%K","slow_%K","slow_%D","MA50"]].fillna(0, inplace=True)

    stochastic_sign = []
    try:
        for i in range(len(df)):
            if df.loc[i, "slow_%K"] > df.loc[i, "slow_%D"]:  # and df.loc[i,"Close"]>df.loc[i,"MA50"] 조건 삭제
                if df.loc[i, "slow_%K"] < 20:
                    stochastic_sign.append("대기")
                else:
                    stochastic_sign.append("매수")
            elif df.loc[i, "slow_%K"] < df.loc[i, "slow_%D"]:  # and df.loc[i,"Close"]<df.loc[i,"MA50"] 조건 삭제
                if df.loc[i, "slow_%K"] > 80:
                    stochastic_sign.append("대기")
                else:
                    stochastic_sign.append("매도")
            else:
                stochastic_sign.append("대기")
    except Exception as ex:
        print(i, ex)
    df["stochastic_sign"] = stochastic_sign
    return df


def get_BB(df):  # 볼린저밴드 함수 추가

    w = 20  # 기준 이동평균일
    k = 2  # 기준 상수

    # 중심선 (MBB) : n일 이동평균선
    df["mbb"] = df["Close"].rolling(w).mean()
    df["MA20_std"] = df["Close"].rolling(w).std()

    # 상한선 (UBB) : 중심선 + (표준편차 × K)
    # 하한선 (LBB) : 중심선 - (표준편차 × K)
    df["ubb"] = df.apply(lambda x: x["mbb"] + k * x["MA20_std"], 1)
    df["lbb"] = df.apply(lambda x: x["mbb"] - k * x["MA20_std"], 1)

    # df[['Close','mbb', 'ubb', 'lbb']][-200:].plot.line()

    # df[["mbb","MA20_std","ubb","lbb"]].fillna(0, inplace=True)

    # 밴드를 이탈했다가 진입할 때 거래
    bb_sign = []
    for i in range(len(df)):
        if i < 20:
            bb_sign.append("대기")
        elif df.loc[i - 1, "Close"] >= df.loc[i - 1, "ubb"] and df.loc[i, "Close"] < df.loc[i, "ubb"]:
            bb_sign.append("매도")
        elif df.loc[i - 1, "Close"] < df.loc[i - 1, "lbb"] and df.loc[i, "Close"] < df.loc[i, "lbb"]:
            bb_sign.append("매수")
        else:
            bb_sign.append("대기")
    df["bb_sign"] = bb_sign

    return df


def get_MA(df, day):
    """이동 평균선 조회"""
    # <이동평균선>- 5, 20, 60, 120 이 좋음
    # 5~10일선 : 단기매매 시 중요하게 보아야하는 부분(심리선)
    # 20일선 : 투자자들과 세력들이 가장 중요하게 보아야하는 부분(생명선)
    # 60~120일선 : 중장기선
    # 200일선 : 코인의 대세 흐름선
    m = df['close'].rolling(day).mean().iloc[-1]
    return m


### 변동성 돌파전략 관련 함수들
def get_Best_K(df, k=0.5):
    """rate of returns(최선의 K값 구하기)"""
    # for k in np.arange(0.1, 1.0, 0.1):
    #     ror = get_Best_K(k)
    # print("%.1f %f" % (k, ror))
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    r = df['ror'].cumprod()[-2]
    return r

def get_target_price(df, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    tp = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return tp