
def backtesting(df, method, period, fee, invest):
    매매결과 = []
    for i in range(len(df)):
        if i == 0:
            df.loc[i, "%s_KRW" % method] = invest
            df.loc[i, "%s_coin" % method] = 0
            df.loc[i, "%s_buy" % method] = None
            df.loc[i, "%s_sell" % method] = None
        elif df.loc[i, "%s_sign" % method] == "매수" and df.loc[i - 1, "%s_KRW" % method] > 5000:
            # 보유 현금이 5천원 이상일때 실행
            buy_coin = float(str(round(df.loc[i - 1, "%s_KRW" % method] / df.loc[i, "close"], 12))[:11])
            buy_unit_fee = buy_coin * (1 - fee)
            df.loc[i, "%s_KRW" % method] = df.loc[i - 1, "%s_KRW" % method] - buy_coin * df.loc[i, "close"]
            # 매수에 사용된 원화를 빼줌

            df.loc[i, "%s_coin" % method] = df.loc[i - i, "%s_coin" % method] + buy_unit_fee
            # 매수된 코인에서 수수료를 빼고, 보유 코인값에 더해줌

            df.loc[i, "%s_buy" % method] = df.loc[i, "close"]
            df.loc[i, "%s_sell" % method] = None
            매매결과.append([i, df.loc[i, "close"], df.loc[i, "%s" % method], "buy"])
        elif df.loc[i, "%s_sign" % method] == "매도" and df.loc[i, "close"] * df.loc[
            i - 1, "%s_coin" % method] > 5000:
            # 보유 코인가치가 5천원 이상일때 실행
            sell_coin = df.loc[i - 1, "%s_coin" % method]
            df.loc[i, "%s_KRW" % method] = round((df.loc[i, "close"] * sell_coin), 4) * (1 - fee) + df.loc[
                i - 1, "%s_KRW" % method]
            df.loc[i, "%s_coin" % method] = df.loc[i - 1, "%s_coin" % method] - sell_coin
            df.loc[i, "%s_buy" % method] = None
            df.loc[i, "%s_sell" % method] = df.loc[i, "close"]
            매매결과.append([i, df.loc[i, "close"], df.loc[i, "%s" % method], "sell"])
        else:  # 대기
            df.loc[i, "%s_KRW" % method] = df.loc[i - 1, "%s_KRW" % method]
            df.loc[i, "%s_coin" % method] = df.loc[i - 1, "%s_coin" % method]
            df.loc[i, "%s_buy" % method] = None
            df.loc[i, "%s_sell" % method] = None

    # 백테스팅 결과 수익률, 수익금액 계산
    수익금 = (df.loc[len(df) - 1, "%s_coin" % method] * df.loc[len(df) - 1, "open"]) \
          + df.loc[len(df) - 1, "%s_KRW" % method] - df.loc[0, "%s_KRW" % method]
    수익률 = 100 * (df.loc[len(df) - 1, "%s_coin" % method] * df.loc[len(df) - 1, "open"] \
                 + df.loc[len(df) - 1, "%s_KRW" % method]) / df.loc[0, "%s_KRW" % method] - 100
    거래횟수 = len(df[(df["%s_buy" % method] > 0) | (df["%s_sell" % method] > 0)][
                   ["open", "close", "%s_buy" % method, "%s_sell" % method]])

    return 수익금, 수익률, 거래횟수, 매매결과


def backtesting2(df, buy_method_list, sell_method_list, period, fee, invest):
    # fig = plt.figure()

    # 매수 및 매도방법 이름 합치기
    method = '_'.join(buy_method_list,sell_method_list)
    num_of_buy_method = len(buy_method_list)
    num_of_sell_method = len(sell_method_list)

    for i in range(len(df)):
        if i == 0:
            df.loc[i, "%s_KRW" % method] = invest
            df.loc[i, "%s_coin" % method] = 0
            df.loc[i, "%s_buy" % method] = None
            df.loc[i, "%s_sell" % method] = None
        else:
            # 보유 현금이 5천원 이상일때 실행
            if df.loc[i - 1, "%s_KRW" % method] > 5000:
                buy_cnt = 0
                for buy_method in buy_method_list:
                    if df.loc[i, "%s_sign" % buy_method] == "매수":
                        buy_cnt += 1
                if buy_cnt == num_of_buy_method:
                    buy_coin = float(str(round(df.loc[i - 1, "%s_KRW" % method] / df.loc[i, "Close"], 12))[:11])
                    buy_unit_fee = buy_coin * (1 - fee)

                    df.loc[i, "%s_KRW" % method] = df.loc[i - 1, "%s_KRW" % method] - buy_coin * df.loc[i, "Close"] # 매수에 사용된 원화를 빼줌
                    df.loc[i, "%s_coin" % method] = df.loc[i - i, "%s_coin" % method] + buy_unit_fee # 매수된 코인에서 수수료를 빼고, 보유 코인값에 더해줌
                    df.loc[i, "%s_buy" % method] = df.loc[i, "Close"]
                    df.loc[i, "%s_sell" % method] = None

            elif df.loc[i, "Close"] * df.loc[i - 1, "%s_coin" % method] > 5000:
                sell_cnt = 0
                for sell_method in sell_method_list:
                    if df.loc[i, "%s_sign" % sell_method] == "매도":
                        sell_cnt += 1
                if sell_cnt == num_of_sell_method:
                    sell_coin = df.loc[i - 1, "%s_coin" % method]
                    df.loc[i, "%s_KRW" % method] = round((df.loc[i, "Close"] * sell_coin), 4) * (1 - fee) + df.loc[i - 1, "%s_KRW" % method]
                    df.loc[i, "%s_coin" % method] = df.loc[i - 1, "%s_coin" % method] - sell_coin
                    df.loc[i, "%s_buy" % method] = None
                    df.loc[i, "%s_sell" % method] = df.loc[i, "Close"]

            else:  # 대기
                df.loc[i, "%s_KRW" % method] = df.loc[i - 1, "%s_KRW" % method]
                df.loc[i, "%s_coin" % method] = df.loc[i - 1, "%s_coin" % method]
                df.loc[i, "%s_buy" % method] = None
                df.loc[i, "%s_sell" % method] = None

    # 백테스팅 결과 수익률, 수익금액 계산
    수익금 = (df.loc[len(df) - 1, "%s_coin" % method] * df.loc[len(df) - 1, "Open"]) \
          + df.loc[len(df) - 1, "%s_KRW" % method] - df.loc[0, "%s_KRW" % method]
    수익률 = 100 * (df.loc[len(df) - 1, "%s_coin" % method] * df.loc[len(df) - 1, "Open"] \
                 + df.loc[len(df) - 1, "%s_KRW" % method]) / df.loc[0, "%s_KRW" % method] - 100
    거래횟수 = len(df[(df["%s_buy" % method] > 0) | (df["%s_sell" % method] > 0)][
                   ["Open", "Close", "%s_buy" % method, "%s_sell" % method]])

    return 수익금, 수익률, 거래횟수