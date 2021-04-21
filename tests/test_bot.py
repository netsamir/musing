# Standard Library
import unittest
from unittest.mock import MagicMock, patch

from crypto_bot import bot


class TestCommon(unittest.TestCase):
    def test_convert_epoch(self):
        epoch_ms = 1618987244277
        self.assertEqual(bot.convert_epoch(epoch_ms), "2021-04-21 08:40:44.277000")

    def test_round_point(self):
        self.assertEqual(bot.round_point("60827.25060827"), 60827.0)
        self.assertEqual(bot.round_point("60827.5060827"), 60827.5)
        self.assertEqual(bot.round_point("60827.7060827"), 60827.5)

    @patch("crypto_bot.bot.bybit")
    def test_exchange_factory(self, bybit_mock):
        self.assertIsInstance(bot.exchange_factory("bybit"), bot.BybitExchange)

    @patch("crypto_bot.bot.bybit")
    def test_exchange_factory_2(self, bybit_mock):
        with self.assertRaises(NotImplementedError):
            bot.exchange_factory("not_an_exchange")


class TestCharlieBot(unittest.TestCase):
    @patch("crypto_bot.bot.bybit")
    def test_simplebot(self, bybit_mock):
        bybit_mock.bybit.return_value = MagicMock()
        short_big_spread = 50
        short_small_spread = 10
        long_ratio = 500
        init_quantity = 1
        exchange_name = "bybit"
        sb = bot.CharlieBot(
            short_big_spread,
            short_small_spread,
            long_ratio,
            init_quantity,
            exchange_name,
        )
        self.assertEqual(sb.short_big_spread, 50)
        self.assertEqual(sb.short_small_spread, 10)
        self.assertEqual(sb.long_ratio, 500)
        self.assertEqual(sb.init_quantity, 1)
        self.assertEqual(sb.exchange_name, "bybit")


class TestBybitExchange(unittest.TestCase):
    @patch("crypto_bot.bot.bybit")
    def test_position(self, mock_bybit):
        ex = bot.BybitExchange()
        ex.position
        mock_bybit.bybit().Positions.Positions_myPosition.assert_called_with(
            symbol="BTCUSD"
        )

    @patch("crypto_bot.bot.bybit")
    def test_position_value(self, mock_bybit):
        ex = bot.BybitExchange()
        # mock_bybit.bybit().Positions.Positions_myPosition().result().__getitem__.return_value = (
        mock_bybit.bybit().Positions.Positions_myPosition().result = lambda: (
            {
                "ret_code": 0,
                "ret_msg": "OK",
                "ext_code": "",
                "ext_info": "",
                "result": {
                    "id": 0,
                    "position_idx": 0,
                    "mode": 0,
                    "user_id": 153179,
                    "risk_id": 1,
                    "symbol": "BTCUSD",
                    "side": "Buy",
                    "size": 1,
                    "position_value": "0.00001791",
                    "entry_price": "55834.72920156",
                    "is_isolated": False,
                    "auto_add_margin": 0,
                    "leverage": "100",
                    "effective_leverage": "100",
                    "position_margin": "0.00000021",
                    "liq_price": "2.5",
                    "bust_price": "2.5",
                    "occ_closing_fee": "0.0003",
                    "occ_funding_fee": "0",
                    "take_profit": "0",
                    "stop_loss": "0",
                    "trailing_stop": "0",
                    "position_status": "Normal",
                    "deleverage_indicator": 1,
                    "oc_calc_data": '{"blq":0,"slq":0,"bmp":0,"smp":0,"fq":-1,"bv2c":0.0115075,"sv2c":0.0114925}',
                    "order_margin": "0",
                    "wallet_balance": "0.5",
                    "realised_pnl": "0",
                    "unrealised_pnl": -1e-08,
                    "cum_realised_pnl": "0",
                    "cross_seq": 2898033321,
                    "position_seq": 0,
                    "created_at": "2021-04-21T16:27:37.947905736Z",
                    "updated_at": "2021-04-21T16:53:29.651160082Z",
                    "tp_sl_mode": "Full",
                },
                "time_now": "1619024009.787388",
                "rate_limit_status": 119,
                "rate_limit_reset_ms": 1619024009784,
                "rate_limit": 120,
            },
            None,
        )

        self.assertEqual(
            ex.position,
            bot.Position(
                entry_price=65000.5,
                real_entry_price=65000.902,
                quantity=1,
                rate_limit_status=119,
                rate_limit_reset="2021-04-21 14:48:02.614000",
                rate_limit=120,
            ),
        )

    @patch("crypto_bot.bot.bybit")
    def test_position_empty(self, mock_bybit):
        ex = bot.BybitExchange()
        # mock_bybit.bybit().Positions.Positions_myPosition().result().__getitem__.return_value = (
        mock_bybit.bybit().Positions.Positions_myPosition().result = lambda: (
            {
                "ret_code": 0,
                "ret_msg": "OK",
                "ext_code": "",
                "ext_info": "",
                "result": {
                    "id": 0,
                    "position_idx": 0,
                    "mode": 0,
                    "user_id": 2681267,
                    "risk_id": 1,
                    "symbol": "BTCUSD",
                    "side": "None",
                    "size": 0,
                    "position_value": "0",
                    "entry_price": "0",
                    "is_isolated": False,
                    "auto_add_margin": 1,
                    "leverage": "100",
                    "effective_leverage": "100",
                    "position_margin": "0",
                    "liq_price": "0",
                    "bust_price": "0",
                    "occ_closing_fee": "0",
                    "occ_funding_fee": "0",
                    "take_profit": "0",
                    "stop_loss": "0",
                    "trailing_stop": "0",
                    "position_status": "Normal",
                    "deleverage_indicator": 0,
                    "oc_calc_data": '{"blq":0,"slq":0,"bmp":0,"smp":0,"bv2c":0.0115075,"sv2c":0.0114925}',
                    "order_margin": "0",
                    "wallet_balance": "0.00698913",
                    "realised_pnl": "0",
                    "unrealised_pnl": 0,
                    "cum_realised_pnl": "-0.00025533",
                    "cross_seq": 6028527302,
                    "position_seq": 0,
                    "created_at": "2021-04-12T10:29:40.395983654Z",
                    "updated_at": "2021-04-21T00:00:02.116270109Z",
                },
                "time_now": "1619009282.617507",
                "rate_limit_status": 119,
                "rate_limit_reset_ms": 1619009282614,
                "rate_limit": 120,
            },
            None,
        )
        with self.assertRaises(bot.NotInCycle):
            ex.position

    @patch("crypto_bot.bot.bybit")
    def test_orders(self, mock_bybit):
        ex = bot.BybitExchange()
        ex.orders
        mock_bybit.bybit().Order.Order_getOrders.assert_called_with(
            symbol="BTCUSD", order_status="New"
        )

    @patch("crypto_bot.bot.bybit")
    def test_bid(self, mock_bybit):
        ex = bot.BybitExchange()
        ex.bid
        mock_bybit.bybit().Market.Market_symbolInfo.assert_called_once()

    @patch("crypto_bot.bot.bybit")
    def test_ask(self, mock_bybit):
        ex = bot.BybitExchange()
        ex.ask
        mock_bybit.bybit().Market.Market_symbolInfo.assert_called_once()

    @patch("crypto_bot.bot.bybit")
    def test_cancel_all(self, mock_bybit):
        ex = bot.BybitExchange()
        ex.cancel_all()
        mock_bybit.bybit().Order.Order_cancelAll.assert_called_with(symbol="BTCUSD")

    @patch("crypto_bot.bot.bybit")
    def test_long(self, mock_bybit):
        ex = bot.BybitExchange()
        ex.long(0, 0)
        mock_bybit.bybit().Order.Order_new.assert_called_with(
            side="Buy",
            symbol="BTCUSD",
            order_type="Limit",
            qty=0,
            price=0,
            time_in_force="PostOnly",
        )

    @patch("crypto_bot.bot.bybit")
    def test_short(self, mock_bybit):
        ex = bot.BybitExchange()
        ex.short(0, 0)
        mock_bybit.bybit().Order.Order_new.assert_called_with(
            side="Sell",
            symbol="BTCUSD",
            order_type="Limit",
            qty=0,
            price=0,
            time_in_force="PostOnly",
        )
