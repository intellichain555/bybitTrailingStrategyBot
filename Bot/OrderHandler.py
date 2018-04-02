from typing import List
import numpy as np
from datetime import datetime as dt

from Bot.FXConnector import FXConnector
from Bot.Trade import Trade
from Bot.Strategy.TargetsAndStopLossStrategy import TargetsAndStopLossStrategy


class OrderHandler:
    def __init__(self, trades: List[Trade], fx: FXConnector, order_updated_handler=None):
        # self.orders = {o.symbol: o for o in orders}
        self.fx = fx

        self.strategies = [TargetsAndStopLossStrategy(t, fx, order_updated_handler) for t in trades]
        self.strategies_dict = {}
        self.asset_dict = {}

        self.trade_info_buf = {}
        self.process_delay = 500
        self.last_ts = 0
        self.first_processing = True

    def process_initial_prices(self):
        if not self.first_processing:
            return

        self.first_processing = False

        tickers = self.fx.get_all_tickers()
        prices = {t['symbol']: float(t['price']) for t in tickers}
        self.execute_strategy(prices)

    def start_listening(self):
        self.process_initial_prices()

        self.strategies_dict = {s.symbol(): s for s in self.strategies}
        self.asset_dict = {s.trade.asset: s for s in self.strategies}

        self.fx.listen_symbols([s.symbol() for s in self.strategies], self.listen_handler, self.user_data_handler)

        self.trade_info_buf = {s.symbol(): [] for s in self.strategies}

        self.fx.start_listening()
        self.last_ts = dt.now()


    def stop_listening(self):
        self.fx.stop_listening()

    def user_data_handler(self, msg):
        # {'e': 'executionReport', 'E': 1522355745812, 's': 'QLCBTC', 'c': 'uSx99rvTfOy2DsAIIFWSs5', 'S': 'SELL',
        #  'o': 'STOP_LOSS_LIMIT', 'f': 'GTC', 'q': '999.00000000', 'p': '0.00001800', 'P': '0.00001800',
        #  'F': '0.00000000', 'g': -1, 'C': 'bI9emhAlDrqzc4SpddvleH', 'x': 'CANCELED', 'X': 'CANCELED', 'r': 'NONE',
        #  'i': 1216751, 'l': '0.00000000', 'z': '0.00000000', 'L': '0.00000000', 'n': '0', 'N': None, 'T': 1522355745811,
        #  't': -1, 'I': 2827141, 'w': False, 'm': False, 'M': False, 'O': -1, 'Z': '-0.00000001'}
        # {'e': 'outboundAccountInfo', 'E': 1522355745812, 'm': 10, 't': 10, 'b': 0, 's': 0, 'T': True, 'W': True,
        #  'D': True, 'u': 1522355745822,
        #  'B': [{'a': 'BTC', 'f': '0.04525778', 'l': '0.02064000'}, {'a': 'LTC', 'f': '0.00172525', 'l': '0.00000000'},
        #        {'a': 'ETH', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'BNC', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'ICO', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'NEO', 'f': '0.00721000', 'l': '5.99000000'},
        #        {'a': 'BNB', 'f': '0.00754975', 'l': '0.00000000'}, {'a': '123', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': '456', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'QTUM', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'EOS', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'SNT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'BNT', 'f': '0.91500000', 'l': '0.00000000'}, {'a': 'GAS', 'f': '0.02951265', 'l': '0.00000000'},
        #        {'a': 'BCC', 'f': '0.00097940', 'l': '0.00000000'}, {'a': 'BTM', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'USDT', 'f': '0.36170369', 'l': '0.00000000'}, {'a': 'HCC', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'HSR', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'OAX', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'DNT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'MCO', 'f': '0.00014000', 'l': '0.00000000'},
        #        {'a': 'ICN', 'f': '0.80000000', 'l': '0.00000000'}, {'a': 'ELC', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'PAY', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'ZRX', 'f': '0.42700000', 'l': '0.00000000'},
        #        {'a': 'OMG', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'WTC', 'f': '0.00047000', 'l': '0.00000000'},
        #        {'a': 'LRX', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'YOYO', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'LRC', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'LLT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'TRX', 'f': '6574.97500000', 'l': '3000.00000000'},
        #        {'a': 'FID', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'SNGLS', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'STRAT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'BQX', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'FUN', 'f': '0.63900000', 'l': '0.00000000'}, {'a': 'KNC', 'f': '0.86000000', 'l': '0.00000000'},
        #        {'a': 'CDT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'XVG', 'f': '0.94300000', 'l': '0.00000000'},
        #        {'a': 'IOTA', 'f': '0.19600000', 'l': '183.00000000'},
        #        {'a': 'SNM', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'LINK', 'f': '0.33900000', 'l': '0.00000000'},
        #        {'a': 'CVC', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'TNT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'REP', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'CTR', 'f': '0.35200000', 'l': '0.00000000'},
        #        {'a': 'MDA', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'MTL', 'f': '0.00950000', 'l': '10.05000000'},
        #        {'a': 'SALT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'NULS', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'SUB', 'f': '0.49600000', 'l': '0.00000000'}, {'a': 'STX', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'MTH', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'CAT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'ADX', 'f': '0.90000000', 'l': '0.00000000'}, {'a': 'PIX', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'ETC', 'f': '0.00840400', 'l': '0.00000000'}, {'a': 'ENG', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'ZEC', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'AST', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': '1ST', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'GNT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'DGD', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'BAT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'DASH', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'POWR', 'f': '0.47700000', 'l': '522.00000000'},
        #        {'a': 'BTG', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'REQ', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'XMR', 'f': '0.00012970', 'l': '0.00000000'}, {'a': 'EVX', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'VIB', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'ENJ', 'f': '0.61200000', 'l': '0.00000000'},
        #        {'a': 'VEN', 'f': '0.90000000', 'l': '0.00000000'}, {'a': 'CAG', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'EDG', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'ARK', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'XRP', 'f': '0.53990000', 'l': '0.00000000'}, {'a': 'MOD', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'AVT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'STORJ', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'KMD', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'RCN', 'f': '0.96500000', 'l': '0.00000000'},
        #        {'a': 'EDO', 'f': '0.00527000', 'l': '0.00000000'}, {'a': 'QASH', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'SAN', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'DATA', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'DLT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'GUP', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'MCAP', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'MANA', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'PPT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'OTN', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'CFD', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'RDN', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'GXS', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'AMB', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'ARN', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'BCPT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'CND', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'GVT', 'f': '0.00396000', 'l': '0.00000000'},
        #        {'a': 'POE', 'f': '0.08200000', 'l': '0.00000000'}, {'a': 'ALIS', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'BTS', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'FUEL', 'f': '0.87100000', 'l': '0.00000000'},
        #        {'a': 'XZC', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'QSP', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'LSK', 'f': '0.00453000', 'l': '25.82000000'}, {'a': 'BCD', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'TNB', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'GRX', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'STAR', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'ADA', 'f': '0.16200000', 'l': '0.00000000'},
        #        {'a': 'LEND', 'f': '0.38600000', 'l': '823.00000000'},
        #        {'a': 'IFT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'KICK', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'UKG', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'VOISE', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'XLM', 'f': '0.35000000', 'l': '0.00000000'}, {'a': 'CMT', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'WAVES', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'WABI', 'f': '0.69900000', 'l': '0.00000000'}, {'a': 'SBTC', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'BCX', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'GTO', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'ETF', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'ICX', 'f': '0.00340000', 'l': '0.00000000'},
        #        {'a': 'OST', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'ELF', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'AION', 'f': '0.00900000', 'l': '0.00000000'},
        #        {'a': 'WINGS', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'BRD', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'NEBL', 'f': '0.00120000', 'l': '19.98000000'}, {'a': 'NAV', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'VIBE', 'f': '0.48000000', 'l': '0.00000000'}, {'a': 'LUN', 'f': '0.00652300', 'l': '0.00000000'},
        #        {'a': 'TRIG', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'APPC', 'f': '0.90000000', 'l': '0.00000000'},
        #        {'a': 'CHAT', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'RLC', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'INS', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'PIVX', 'f': '0.00731000', 'l': '0.00000000'},
        #        {'a': 'IOST', 'f': '0.87000000', 'l': '0.00000000'},
        #        {'a': 'STEEM', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'NANO', 'f': '0.00682000', 'l': '0.00000000'}, {'a': 'AE', 'f': '0.00331000', 'l': '0.00000000'},
        #        {'a': 'VIA', 'f': '0.00352000', 'l': '0.00000000'}, {'a': 'BLZ', 'f': '0.10000000', 'l': '0.00000000'},
        #        {'a': 'SYS', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'RPX', 'f': '0.55700000', 'l': '916.00000000'},
        #        {'a': 'NCASH', 'f': '0.88700000', 'l': '0.00000000'}, {'a': 'POA', 'f': '0.65000000', 'l': '0.00000000'},
        #        {'a': 'ONT', 'f': '0.68106390', 'l': '0.00000000'}, {'a': 'ZIL', 'f': '0.15800000', 'l': '0.00000000'},
        #        {'a': 'STORM', 'f': '0.20300000', 'l': '6310.00000000'},
        #        {'a': 'XEM', 'f': '0.00000000', 'l': '0.00000000'}, {'a': 'WAN', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'WPR', 'f': '0.00000000', 'l': '0.00000000'},
        #        {'a': 'QLC', 'f': '999.90700000', 'l': '0.00000000'}]}

        if msg['e'] == 'outboundAccountInfo':
            assets = list(self.asset_dict.keys())
            for asset in msg['B']:
                if asset['a'] in assets:
                    asset_name = asset['a']
                    strategy = self.asset_dict[asset_name]

                    strategy.account_info(asset)
                    assets.remove(asset_name)

                    if len(asset) == 0:
                        break
        elif msg['e'] == 'executionReport':
            sym = msg['s']

            if sym in self.strategies_dict:
                self.strategies_dict[sym].execution_rpt(
                    {'orderId': msg['i'],
                     'status': msg['X'],
                     'symbol': sym,
                     'side': msg['S'],
                     'vol': msg['q'],
                     'price': msg['p']})

    def listen_handler(self, msg):
        # {
        #     "e": "trade",  # Event type
        #     "E": 123456789,  # Event time
        #     "s": "BNBBTC",  # Symbol
        #     "t": 12345,  # Trade ID
        #     "p": "0.001",  # Price
        #     "q": "100",  # Quantity
        #     "b": 88,  # Buyer order Id
        #     "a": 50,  # Seller order Id
        #     "T": 123456785,  # Trade time
        #     "m": true,  # Is the buyer the market maker?
        #     "M": true  # Ignore.
        # }
        d = msg['data']
        if d['e'] == 'error':
            print(msg['data'])
        else:
            self.trade_info_buf[d['s']].append(d['p'])
            delta = dt.now() - self.last_ts
            if (delta.seconds * 1000 + (delta).microseconds / 1000) > self.process_delay:
                self.last_ts = dt.now()
                mean_prices = self.aggreagate_fx_prices()
                self.execute_strategy(mean_prices)

    def aggreagate_fx_prices(self):
        mp = {}
        for sym, prices in self.trade_info_buf.items():
            if not prices:
                continue
            mean_price = np.mean(np.array(prices).astype(np.float))
            self.trade_info_buf[sym] = []

            mp[sym] = mean_price

        return mp

    def execute_strategy(self, prices):
        for s in self.strategies:
            if s.symbol() in prices:
                s.execute(prices[s.symbol()])

    def check_strategy_is_complete(self):
        for s in self.strategies[:]:
            if s.is_completed():
                self.strategies.remove(s)
                self.stop_listening()
                self.start_listening()
