import math
import jwt          # PyJWT
import uuid
import hashlib
from pyupbit import *
from pyupbit.request_api import _call_public_api
from pyupbit.request_api import _send_get_request, _send_post_request, _send_delete_request
from urllib.parse import urlencode
import datetime
import pandas as pd


class Quotation :
    def get_tickers(self, fiat="ALL", limit_info=False):
        """
        마켓 코드 조회 (업비트에서 거래 가능한 마켓 목록 조회)
        :param fiat: "ALL", "KRW", "BTC", "USDT"
        :param limit_info: 요청수 제한 리턴
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/market/all"

            # call REST API
            ret = _call_public_api(url)
            if isinstance(ret, tuple):
                contents, req_limit_info = ret
            else:
                contents = None
                req_limit_info = None

            tickers = None
            if isinstance(contents, list):
                markets = [x['market'] for x in contents]

                if fiat != "ALL":
                    tickers = [x for x in markets if x.startswith(fiat)]
                else:
                    tickers = markets

            if limit_info is False:
                return tickers
            else:
                return tickers, req_limit_info

        except Exception as x:
            print(x.__class__.__name__)
            return None


    def get_url_ohlcv(self, interval):
        """
        candle에 대한 요청 주소를 얻는 함수
        :param interval: day(일봉), minute(분봉), week(주봉), 월봉(month)
        :return: candle 조회에 사용되는 url
        """
        if interval in ["day", "days"]:
            url = "https://api.upbit.com/v1/candles/days"
        elif interval in ["minute1", "minutes1"]:
            url = "https://api.upbit.com/v1/candles/minutes/1"
        elif interval in ["minute3", "minutes3"]:
            url = "https://api.upbit.com/v1/candles/minutes/3"
        elif interval in ["minute5", "minutes5"]:
            url = "https://api.upbit.com/v1/candles/minutes/5"
        elif interval in ["minute10", "minutes10"]:
            url = "https://api.upbit.com/v1/candles/minutes/10"
        elif interval in ["minute15", "minutes15"]:
            url = "https://api.upbit.com/v1/candles/minutes/15"
        elif interval in ["minute30", "minutes30"]:
            url = "https://api.upbit.com/v1/candles/minutes/30"
        elif interval in ["minute60", "minutes60"]:
            url = "https://api.upbit.com/v1/candles/minutes/60"
        elif interval in ["minute240", "minutes240"]:
            url = "https://api.upbit.com/v1/candles/minutes/240"
        elif interval in ["week", "weeks"]:
            url = "https://api.upbit.com/v1/candles/weeks"
        elif interval in ["month", "months"]:
            url = "https://api.upbit.com/v1/candles/months"
        else:
            url = "https://api.upbit.com/v1/candles/days"

        return url


    def get_ohlcv(self, ticker="KRW-BTC", interval="day", count=200, to=None):
        """
        캔들 조회
        :return:
        """
        try:
            url = self.get_url_ohlcv(interval=interval)

            if to == None:
                to = datetime.datetime.now()
            elif isinstance(to, str):
                to = pd.to_datetime(to).to_pydatetime()
            elif isinstance(to, pd._libs.tslibs.timestamps.Timestamp):
                to = to.to_pydatetime()

            if to.tzinfo is None:
                to = to.astimezone()
            to = to.astimezone(datetime.timezone.utc)
            to = to.strftime("%Y-%m-%d %H:%M:%S")

            contents = _call_public_api(url, market=ticker, count=count, to=to)[0]
            # dt_list = [datetime.datetime.strptime(x['candle_date_time_kst'], "%Y-%m-%dT%H:%M:%S") for x in contents]
            # df = pd.DataFrame(contents, columns=['opening_price', 'high_price', 'low_price', 'trade_price',
            #                                      'candle_acc_trade_volume'],
            #                   index=dt_list)

            df = pd.DataFrame(contents, columns=['candle_date_time_kst','opening_price', 'high_price', 'low_price', 'trade_price','candle_acc_trade_volume'])
            df = df.rename(
                columns={"candle_date_time_kst": "time", "opening_price": "open", "high_price": "high", "low_price": "low", "trade_price": "close",
                         "candle_acc_trade_volume": "volume"})
            df['date'] = [datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S') for x in df['time']]
            df.sort_values("date", inplace=True)
            df.reset_index(drop=True, inplace=True)
            return df
        except Exception as x:
            print(x.__class__.__name__)
            return None


    def get_daily_ohlcv_from_base(self, ticker="KRW-BTC", base=0):
        """
        :param ticker:
        :param base:
        :return:
        """
        try:
            df = self.get_ohlcv(ticker, interval="minute60")
            df = df.resample('24H', offset=base).agg(
                {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
            return df
        except Exception as x:
            print(x.__class__.__name__)
            return None


    def get_current_price(self, ticker="KRW-BTC"):
        """
        최종 체결 가격 조회 (현재가)
        :param ticker:
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/ticker"
            contents = _call_public_api(url, markets=ticker)[0]
            if not contents:
                return None

            if isinstance(ticker, list):
                ret = {}
                for content in contents:
                    market = content['market']
                    price = content['trade_price']
                    ret[market] = price
                return ret
            else:
                return contents[0]['trade_price']
        except Exception as x:
            print(x.__class__.__name__)

    # def get_current_price(self, ticker):
    #     """현재가 조회"""
    #     return self.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]



    def get_orderbook(self, tickers="KRW-BTC"):
        '''
        호가(현재가) 정보 조회
        :param tickers: 티커 목록을 문자열
        :return:
        '''
        try:
            url = "https://api.upbit.com/v1/orderbook"
            contents = _call_public_api(url, markets=tickers)[0]
            return contents
        except Exception as x:
            print(x.__class__.__name__)
            return None


###############################################################
# EXCHANGE API
###############################################################
class Exchange:

    def __init__(self, access, secret):
        self.access = access
        self.secret = secret

    def _request_headers(self, query=None):
        payload = {
            "access_key": self.access,
            "nonce": str(uuid.uuid4())
        }

        if query is not None:
            m = hashlib.sha512()
            m.update(urlencode(query, doseq=True).replace("%5B%5D=", "[]=").encode())
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = "SHA512"

        # jwt_token = jwt.encode(payload, self.secret, algorithm="HS256").decode('utf-8')
        jwt_token = jwt.encode(payload, self.secret, algorithm="HS256")  # PyJWT >= 2.0
        authorization_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorization_token}
        return headers

    # --------------------------------------------------------------------------
    # 자산
    # --------------------------------------------------------------------------
    #     전체 계좌 조회
    def get_balances(self, contain_req=False):
        """
        전체 계좌 조회
        :param contain_req: Remaining-Req 포함여부
        :return: 내가 보유한 자산 리스트
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        url = "https://api.upbit.com/v1/accounts"
        headers = self._request_headers()
        result = _send_get_request(url, headers=headers)
        if contain_req:
            return result
        else:
            return result[0]

    def get_balance(self, ticker="KRW", contain_req=False):
        """
        특정 코인/원화의 잔고를 조회하는 메소드
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 제외)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # fiat-ticker
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            # search the current currency
            balance = 0
            for x in balances:
                if x['currency'] == ticker:
                    balance = float(x['balance'])
                    break

            if contain_req:
                return balance, req
            else:
                return balance
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def get_balance_t(self, ticker='KRW', contain_req=False):
        """
        특정 코인/원화의 잔고 조회(balance + locked)
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 포함)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            balance = 0
            locked = 0
            for x in balances:
                if x['currency'] == ticker:
                    balance = float(x['balance'])
                    locked = float(x['locked'])
                    break

            if contain_req:
                return balance + locked, req
            else:
                return balance + locked
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def get_avg_buy_price(self, ticker='KRW', contain_req=False):
        """
        특정 코인/원화의 매수평균가 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 매수평균가
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            avg_buy_price = 0
            for x in balances:
                if x['currency'] == ticker:
                    avg_buy_price = float(x['avg_buy_price'])
                    break
            if contain_req:
                return avg_buy_price, req
            else:
                return avg_buy_price

        except Exception as x:
            print(x.__class__.__name__)
            return None

    def get_amount(self, ticker, contain_req=False):
        """
        특정 코인/원화의 매수금액 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드 (ALL 입력시 총 매수금액 조회)
        :param contain_req: Remaining-Req 포함여부
        :return: 매수금액
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            amount = 0
            for x in balances:
                if x['currency'] == 'KRW':
                    continue

                avg_buy_price = float(x['avg_buy_price'])
                balance = float(x['balance'])
                locked = float(x['locked'])

                if ticker == 'ALL':
                    amount += avg_buy_price * (balance + locked)
                elif x['currency'] == ticker:
                    amount = avg_buy_price * (balance + locked)
                    break
            if contain_req:
                return amount, req
            else:
                return amount
        except Exception as x:
            print(x.__class__.__name__)
            return None

    # endregion balance

    # --------------------------------------------------------------------------
    # 주문
    # --------------------------------------------------------------------------
    #     주문 가능 정보
    def get_chance(self, ticker, contain_req=False):
        """
        마켓별 주문 가능 정보를 확인.
        :param ticker:
        :param contain_req: Remaining-Req 포함여부
        :return: 마켓별 주문 가능 정보를 확인
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            url = "https://api.upbit.com/v1/orders/chance"
            data = {"market": ticker}
            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    #    개별 주문 조회
    def get_order(self, ticker_or_uuid, state='wait', kind='normal', contain_req=False):
        """
        주문 리스트 조회
        :param ticker: market
        :param state: 주문 상태(wait, done, cancel)
        :param kind: 주문 유형(normal, watch)
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        # TODO : states, identifiers 관련 기능 추가 필요
        try:
            p = re.compile(r"^\w+-\w+-\w+-\w+-\w+$")
            # 정확히는 입력을 대문자로 변환 후 다음 정규식을 적용해야 함
            # - r"^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$"
            is_uuid = len(p.findall(ticker_or_uuid)) > 0
            if is_uuid:
                url = "https://api.upbit.com/v1/order"
                data = {'uuid': ticker_or_uuid}
                headers = self._request_headers(data)
                result = _send_get_request(url, headers=headers, data=data)
            else:

                url = "https://api.upbit.com/v1/orders"
                data = {'market': ticker_or_uuid,
                        'state': state,
                        'kind': kind,
                        'order_by': 'desc'
                        }
                headers = self._request_headers(data)
                result = _send_get_request(url, headers=headers, data=data)

            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def get_individual_order(self, uuid, contain_req=False):
        """
        주문 리스트 조회
        :param uuid: 주문 id
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        # TODO : states, uuids, identifiers 관련 기능 추가 필요
        try:
            url = "https://api.upbit.com/v1/order"
            data = {'uuid': uuid}
            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    #    주문 취소 접수
    def cancel_order(self, uuid, contain_req=False):
        """
        주문 취소
        :param uuid: 주문 함수의 리턴 값중 uuid
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/order"
            data = {"uuid": uuid}
            headers = self._request_headers(data)
            result = _send_delete_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    #     주문
    def buy_limit_order(self, ticker, price, volume, contain_req=False):
        """
        지정가 매수
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,
                    "side": "bid",
                    "volume": str(volume),
                    "price": str(price),
                    "ord_type": "limit"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def buy_market_order(self, ticker, price, contain_req=False):
        """
        시장가 매수
        :param ticker: ticker for cryptocurrency
        :param price: KRW
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,  # market ID
                    "side": "bid",  # buy
                    "price": str(price),
                    "ord_type": "price"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def sell_market_order(self, ticker, volume, contain_req=False):
        """
        시장가 매도 메서드
        :param ticker: 가상화폐 티커
        :param volume: 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,  # ticker
                    "side": "ask",  # sell
                    "volume": str(volume),
                    "ord_type": "market"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    def sell_limit_order(self, ticker, price, volume, contain_req=False):
        """
        지정가 매도
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/orders"
            data = {"market": ticker,
                    "side": "ask",
                    "volume": str(volume),
                    "price": str(price),
                    "ord_type": "limit"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    # --------------------------------------------------------------------------
    # 출금
    # --------------------------------------------------------------------------
    #     개별 출금 조회
    def get_individual_withdraw_order(self, uuid: str, currency: str, contain_req=False):
        """
        현금 출금
        :param uuid: 출금 UUID
        :param txid: 출금 TXID
        :param currency: Currency 코드
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/withdraw"
            data = {"uuid": uuid, "currency": currency}
            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    #     코인 출금하기
    def withdraw_coin(self, currency, amount, address, secondary_address='None', transaction_type='default',
                      contain_req=False):
        """
        코인 출금
        :param currency: Currency symbol
        :param amount: 주문 가격
        :param address: 출금 지갑 주소
        :param secondary_address: 2차 출금주소 (필요한 코인에 한해서)
        :param transaction_type: 출금 유형
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/withdraws/coin"
            data = {"currency": currency,
                    "amount": amount,
                    "address": address,
                    "secondary_address": secondary_address,
                    "transaction_type": transaction_type}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    #     원화 출금하기
    def withdraw_cash(self, amount: str, contain_req=False):
        """
        현금 출금
        :param amount: 출금 액수
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.upbit.com/v1/withdraws/krw"
            data = {"amount": amount}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            return None

    # --------------------------------------------------------------------------
    # 입금
    # --------------------------------------------------------------------------
    #     입금 리스트 조회
    #     개별 입금 조회
    #     입금 주소 생성 요청
    #     전체 입금 주소 조회
    #     개별 입금 주소 조회
    #     원화 입금하기

    # --------------------------------------------------------------------------
    # 서비스 정보
    # --------------------------------------------------------------------------
    #     입출금 현황
    def get_deposit_withdraw_status(self, contain_req=False):
        url = "https://api.upbit.com/v1/status/wallet"
        headers = self._request_headers()
        result = _send_get_request(url, headers=headers)
        if contain_req:
            return result
        else:
            return result[0]

    #     API키 리스트 조회
    def get_api_key_list(self, contain_req=False):
        url = "https://api.upbit.com/v1/api_keys"
        headers = self._request_headers()
        result = _send_get_request(url, headers=headers)
        if contain_req:
            return result
        else:
            return result[0]

    def get_tick_size(self, price, method="floor"):
        """원화마켓 주문 가격 단위
        Args:
            price (float]): 주문 가격
            method (str, optional): 주문 가격 계산 방식. Defaults to "floor".
        Returns:
            float: 업비트 원화 마켓 주문 가격 단위로 조정된 가격
        """

        if method == "floor":
            func = math.floor
        elif method == "round":
            func = round
        else:
            func = math.ceil

        if price >= 2000000:
            tick_size = func(price / 1000) * 1000
        elif price >= 1000000:
            tick_size = func(price / 500) * 500
        elif price >= 500000:
            tick_size = func(price / 100) * 100
        elif price >= 100000:
            tick_size = func(price / 50) * 50
        elif price >= 10000:
            tick_size = func(price / 10) * 10
        elif price >= 1000:
            tick_size = func(price / 5) * 5
        elif price >= 100:
            tick_size = func(price / 1) * 1
        elif price >= 10:
            tick_size = func(price / 0.1) / 10
        else:
            tick_size = func(price / 0.01) / 100

        return tick_size



# import re
# import requests
# import json
# from pyupbit.errors import (UpbitError,
#                            TooManyRequests,
#                            raise_error,
#                            RemainingReqParsingError)
#
# HTTP_RESP_CODE_START = 200
# HTTP_RESP_CODE_END   = 400
#
# class Request:
#     def _parse_remaining_req(self,remaining_req):
#         """parse the request limit data of the Upbit API
#         Args:
#             remaining_req (str): "group=market; min=573; sec=9"
#         Returns:
#             dict: {'group': 'market', 'min': 573, 'sec': 2}
#         """
#         try:
#             p = re.compile(r"group=([a-z\-]+); min=([0-9]+); sec=([0-9]+)")
#             m = p.search(remaining_req)
#             ret = {
#                 'group': m.group(1),
#                 'min': int(m.group(2)),
#                 'sec': int(m.group(3))
#             }
#             return ret
#         except:
#             raise RemainingReqParsingError
#
#
#     def _call_public_api(self,url, **params):
#         """call get type api
#         Args:
#             url (str): REST API url
#         Returns:
#             tuple: (data, req_limit_info)
#         """
#         resp = requests.get(url, params=params)
#         if HTTP_RESP_CODE_START <= resp.status_code < HTTP_RESP_CODE_END:
#             remaining_req = resp.headers.get('Remaining-Req')
#             limit = _parse_remaining_req(remaining_req)
#             data = resp.json()
#             return data, limit
#         else:
#             raise_error(resp)
#
#
#     def _send_post_request(self,url, headers=None, data=None):
#         resp = requests.post(url, headers=headers, data=data)
#         if HTTP_RESP_CODE_START <= resp.status_code < HTTP_RESP_CODE_END:
#             remaining_req = resp.headers.get('Remaining-Req')
#             limit = _parse_remaining_req(remaining_req)
#             contents = resp.json()
#             return contents,limit
#         else:
#             raise_error(resp)
#
#
#     def _send_get_request(self,url, headers=None, data=None):
#         resp = requests.get(url, headers=headers, data=data)
#         if HTTP_RESP_CODE_START <= resp.status_code < HTTP_RESP_CODE_END:
#             remaining_req = resp.headers.get('Remaining-Req')
#             limit = _parse_remaining_req(remaining_req)
#             contents = resp.json()
#             return contents, limit
#         else:
#             raise_error(resp)
#
#
#     def _send_delete_request(self,url, headers=None, data=None):
#         resp = requests.delete(url, headers=headers, data=data)
#         if HTTP_RESP_CODE_START <= resp.status_code < HTTP_RESP_CODE_END:
#             remaining_req = resp.headers.get('Remaining-Req')
#             limit = _parse_remaining_req(remaining_req)
#             contents = resp.json()
#             return contents,limit
#         else:
#             raise_error(resp)


# quotation = Quotation()
# exchange = Exchange(""," ")
# upbit = C_UPBIT()
# print(upbit.get_tickers(limit_info=True))
# print(upbit.get_ohlcv("KRW-BTC", interval="minute1", count=200, to="2020-01-01 00:00:00")) #minute1~240, day, week, month
# print(quotation.get_url_ohlcv("minutes1"))
# print(quotation.get_daily_ohlcv_from_base("KRW-BTC", base=9))
# print(upbit.get_current_price("KRW-BTC"))
# print(upbit.get_orderbook(tickers=["KRW-BTC"]))


#------------------------------------------------------
# 모든 티커 목록 조회
#all_tickers = get_tickers()
#print(all_tickers)

# 특정 시장의 티커 목록 조회
#krw_tickers = get_tickers(fiat="KRW")
#print(krw_tickers, len(krw_tickers))

#btc_tickers = get_tickers(fiat="BTC")
#print(btc_tickers, len(btc_tickers))

#usdt_tickers = get_tickers(fiat="USDT")
#print(usdt_tickers, len(usdt_tickers))

# 요청 수 제한 얻기
#all_tickers, limit_info = get_tickers(limit_info=True)
#print(limit_info)

# print(get_tickers(fiat="KRW"))
# print(get_tickers(fiat="BTC"))
# print(get_tickers(fiat="USDT"))

#------------------------------------------------------
#print(get_ohlcv("KRW-BTC"))
#print(get_ohlcv("KRW-BTC", interval="day", count=5))
#print(get_ohlcv("KRW-BTC", interval="day", to="2020-01-01 00:00:00"))

#to = datetime.datetime.strptime("2020-01-01", "%Y-%m-%d")
#df = get_ohlcv(ticker="KRW-BTC", interval="day", to=to)
#print(df)

# string Test
# df = quotation.get_ohlcv("KRW-BTC", interval="minute1", to="2018-08-25 12:00:00")
# print(df)

# time stamp Test
# df = get_ohlcv("KRW-BTC", interval="minute1")
# print(get_ohlcv("KRW-BTC", interval="minute1", to=df.index[0]))

# # DateTime Test
# now = datetime.datetime.now() - datetime.timedelta(days=1000)
# print(get_ohlcv("KRW-BTC", interval="minute1", to=now))
# print(get_ohlcv("KRW-BTC", interval="minute1", to="2018-01-01 12:00:00"))
# print(get_ohlcv("KRW-BTC", interval="minute3"))
# print(get_ohlcv("KRW-BTC", interval="minute5"))
# print(get_ohlcv("KRW-BTC", interval="minute10"))
#print(get_ohlcv("KRW-BTC", interval="minute15"))
#print(get_ohlcv("KRW-BTC", interval="minute30"))
#print(get_ohlcv("KRW-BTC", interval="minute60"))
#print(get_ohlcv("KRW-BTC", interval="minute240"))
#print(get_ohlcv("KRW-BTC", interval="week"))
#print(get_daily_ohlcv_from_base("KRW-BTC", base=9))
#print(get_ohlcv("KRW-BTC", interval="day", count=5))

# krw_tickers = get_tickers(fiat="KRW")
# print(len(krw_tickers))

# krw_tickers1 = krw_tickers[:100]
# krw_tickers2 = krw_tickers[100:]

# prices1 = get_current_price(krw_tickers1)
# prices2 = get_current_price(krw_tickers2)

#print(prices1)
# print(prices2)


#print(get_current_price("KRW-BTC"))
#print(get_current_price(["KRW-BTC", "KRW-XRP"]))

#print(get_orderbook(tickers=["KRW-BTC"]))
#print(get_orderbook(tickers=["KRW-BTC", "KRW-XRP"]))
