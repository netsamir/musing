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

    @patch("crypto_bot.bot.BybitWebsocket")
    @patch("crypto_bot.bot.bybit")
    def test_exchange_factory(self, bybit_mock, ws_mock):
        self.assertIsInstance(bot.exchange_factory("bybit"), bot.BybitExchange)

    @patch("crypto_bot.bot.BybitWebsocket")
    @patch("crypto_bot.bot.bybit")
    def test_exchange_factory_2(self, bybit_mock, ws_mock):
        with self.assertRaises(NotImplementedError):
            bot.exchange_factory("not_an_exchange")

    def test_orders_head(self):
        orders = bot.Orders(
            longs={
                "924a7a02-1c95-4328-b306-d154fe7db074": bot.Order(
                    order_id="924a7a02-1c95-4328-b306-d154fe7db074",
                    side="Buy",
                    price=53585.5,
                    quantity=1,
                    order_status="New",
                ),
                "2d81bc14-d738-4952-8036-1a996437d6e9": bot.Order(
                    order_id="2d81bc14-d738-4952-8036-1a996437d6e9",
                    side="Buy",
                    price=53467.0,
                    quantity=2,
                    order_status="New",
                ),
                "6939be11-b806-425c-bd63-ca2aef5d786d": bot.Order(
                    order_id="6939be11-b806-425c-bd63-ca2aef5d786d",
                    side="Buy",
                    price=53313.0,
                    quantity=4,
                    order_status="New",
                ),
                "ea93f451-b559-4daa-9616-4d97e7465926": bot.Order(
                    order_id="ea93f451-b559-4daa-9616-4d97e7465926",
                    side="Buy",
                    price=52853.0,
                    quantity=16,
                    order_status="New",
                ),
                "b7f3c04e-066f-45a0-a9f0-bdf1061310c1": bot.Order(
                    order_id="b7f3c04e-066f-45a0-a9f0-bdf1061310c1",
                    side="Buy",
                    price=52515.0,
                    quantity=32,
                    order_status="New",
                ),
                "0c4fd7e7-4754-40a2-bc1c-8660602f1872": bot.Order(
                    order_id="0c4fd7e7-4754-40a2-bc1c-8660602f1872",
                    side="Buy",
                    price=52075.5,
                    quantity=64,
                    order_status="New",
                ),
                "d39db473-3a23-49b3-91d9-f971f881ad17": bot.Order(
                    order_id="d39db473-3a23-49b3-91d9-f971f881ad17",
                    side="Buy",
                    price=53113.0,
                    quantity=8,
                    order_status="New",
                ),
                "defdb93e-4e7f-439a-8547-a825cc4a19fa": bot.Order(
                    order_id="defdb93e-4e7f-439a-8547-a825cc4a19fa",
                    side="Buy",
                    price=51504.5,
                    quantity=128,
                    order_status="New",
                ),
                "dfc715e3-39ea-49ef-a595-de0699434fac": bot.Order(
                    order_id="dfc715e3-39ea-49ef-a595-de0699434fac",
                    side="Buy",
                    price=50762.0,
                    quantity=256,
                    order_status="New",
                ),
                "077c1205-16a5-4839-9073-922f65fe1968": bot.Order(
                    order_id="077c1205-16a5-4839-9073-922f65fe1968",
                    side="Buy",
                    price=48542.5,
                    quantity=1024,
                    order_status="New",
                ),
            },
            shorts={
                "18e39252-de1b-45d8-a671-a3cad422bc11": bot.Order(
                    order_id="18e39252-de1b-45d8-a671-a3cad422bc11",
                    side="Sell",
                    price=53706.5,
                    quantity=1,
                    order_status="New",
                ),
                "19e39252-de1b-45d8-a671-a3cad422bc11": bot.Order(
                    order_id="19e39252-de1b-45d8-a671-a3cad422bc11",
                    side="Sell",
                    price=53706.5,
                    quantity=2,
                    order_status="New",
                ),
            },
        )
        self.assertEqual(
            orders.head_longs(),
            bot.Order(
                order_id="924a7a02-1c95-4328-b306-d154fe7db074",
                side="Buy",
                price=53585.5,
                quantity=1,
                order_status="New",
            ),
        )

        self.assertEqual(orders.shorts_qty(), 3)
        self.assertEqual(orders.head_longs().quantity, 1)

    def test_bankruptcy_price(self):
        self.assertEqual(
            bot.bankruptcy_price(10000 / 8000, 10000, 0.5, 0, 0), 5718.571428571428
        )

    def test_liquidation_price(self):
        self.assertEqual(
            bot.liquidation_price(10000, 8000, 0.5, 0, 0, 0.005), 5739.083528002316
        )

    def test_allocate_longs(self):
        self.assertEqual(
            list(
                bot.allocate_longs(
                    60000, 1, idx=1, multiplicator=10, intercept=7, growth_factor=1.3
                )
            ),
            [
                (59909.0, 1, -91),
                (59790.5, 2, -118),
                (59636.5, 4, -154),
                (59436.5, 8, -200),
                (59176.5, 16, -260),
                (58838.5, 32, -338),
                (58399.0, 64, -440),
                (57828.0, 128, -571),
                (57085.5, 256, -742),
                (56120.5, 512, -965),
                (54866.0, 1024, -1254),
                (53235.0, 2048, -1631),
            ],
        )


@patch("crypto_bot.bot.BybitWebsocket")
@patch("crypto_bot.bot.bybit")
class TestCharlieBot(unittest.TestCase):
    def test_simplebot(self, bybit_mock, ws_mock):
        bybit_mock.bybit.return_value = MagicMock()
        ws_mock.BybitWebsocket.return_value = MagicMock()
        short_big_spread = 50
        short_small_spread = 10
        init_quantity = 1
        exchange_name = "bybit"
        sb = bot.CharlieBot(
            short_big_spread,
            short_small_spread,
            init_quantity,
            exchange_name,
        )
        self.assertEqual(sb.short_big_spread, 50)
        self.assertEqual(sb.short_small_spread, 10)
        self.assertEqual(sb.init_quantity, 1)
        self.assertEqual(sb.exchange_name, "bybit")


@patch("crypto_bot.bot.BybitWebsocket")
@patch("crypto_bot.bot.bybit")
class TestBybitExchange(unittest.TestCase):
    def test_position(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.position
        bybit_mock.bybit().Positions.Positions_myPosition.assert_called_with(
            symbol="BTCUSD"
        )

    def test_position_value(self, mock_bybit, ws_mock):
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
                entry_price=55834.5,
                real_entry_price=55834.72920156,
                quantity=1,
                rate_limit_status=119,
                rate_limit_reset="2021-04-21 18:53:29.784000",
                rate_limit=120,
            ),
        )

    def test_position_empty(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        # mock_bybit.bybit().Positions.Positions_myPosition().result().__getitem__.return_value = (
        bybit_mock.bybit().Positions.Positions_myPosition().result = lambda: (
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

    @unittest.skip
    def test_rest_orders(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.orders
        bybit_mock.bybit().Order.Order_getOrders.assert_called_with(
            symbol="BTCUSD", order_status="New"
        )

    def test_orders_empty(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()

        ws_mock.get_data.return_value = []
        self.assertEqual(ex.orders, bot.Orders(longs={}, shorts={}))

    def test_orders(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()

        ws_mock.BybitWebsocket().get_data.return_value = [
            {
                "user_id": 2681267,
                "position_idx": 0,
                "order_status": "New",
                "symbol": "BTCUSD",
                "side": "Buy",
                "order_type": "Limit",
                "price": "55600",
                "qty": "2",
                "time_in_force": "PostOnly",
                "order_link_id": "",
                "order_id": "d0aa620e-bcbd-41c6-9315-f1be7570bfe3",
                "created_at": "2021-04-20T12:35:28.941Z",
                "updated_at": "2021-04-20T12:35:28.941Z",
                "leaves_qty": "2",
                "leaves_value": "0.00003597",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "reject_reason": "EC_NoError",
            },
            {
                "user_id": 2681267,
                "position_idx": 0,
                "order_status": "New",
                "symbol": "BTCUSD",
                "side": "Buy",
                "order_type": "Limit",
                "price": "55600",
                "qty": "1",
                "time_in_force": "PostOnly",
                "order_link_id": "",
                "order_id": "d3aa620e-bcbd-41c6-9315-f1be7570bfe3",
                "created_at": "2021-04-20T12:35:28.941Z",
                "updated_at": "2021-04-20T12:35:28.941Z",
                "leaves_qty": "1",
                "leaves_value": "0.00003597",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "reject_reason": "EC_NoError",
            },
            {
                "user_id": 2681267,
                "position_idx": 0,
                "order_status": "New",
                "symbol": "BTCUSD",
                "side": "Sell",
                "order_type": "Limit",
                "price": "56300",
                "qty": "1",
                "time_in_force": "PostOnly",
                "order_link_id": "",
                "order_id": "5b7eebcf-c43c-4396-8aea-07c6d9dad76e",
                "created_at": "2021-04-20T12:35:09.135Z",
                "updated_at": "2021-04-20T12:35:09.135Z",
                "leaves_qty": "1",
                "leaves_value": "0.00001776",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "reject_reason": "EC_NoError",
            },
            {
                "user_id": 2681267,
                "position_idx": 0,
                "order_status": "New",
                "symbol": "BTCUSD",
                "side": "Sell",
                "order_type": "Limit",
                "price": "56500",
                "qty": "1",
                "time_in_force": "PostOnly",
                "order_link_id": "",
                "order_id": "88d6be9c-c6f4-4c2b-87c4-05cb67d2bfc4",
                "created_at": "2021-04-20T12:35:00.350Z",
                "updated_at": "2021-04-20T12:35:00.350Z",
                "leaves_qty": "1",
                "leaves_value": "0.00001769",
                "cum_exec_qty": "0",
                "cum_exec_value": "0",
                "cum_exec_fee": "0",
                "reject_reason": "EC_NoError",
            },
        ]

        self.assertEqual(
            ex.orders,
            bot.Orders(
                longs={
                    "d3aa620e-bcbd-41c6-9315-f1be7570bfe3": bot.Order(
                        order_id="d3aa620e-bcbd-41c6-9315-f1be7570bfe3",
                        side="Buy",
                        price=55600.0,
                        quantity=1,
                        order_status="New",
                    ),
                    "d0aa620e-bcbd-41c6-9315-f1be7570bfe3": bot.Order(
                        order_id="d0aa620e-bcbd-41c6-9315-f1be7570bfe3",
                        side="Buy",
                        price=55600.0,
                        quantity=2,
                        order_status="New",
                    ),
                },
                shorts={
                    "5b7eebcf-c43c-4396-8aea-07c6d9dad76e": bot.Order(
                        order_id="5b7eebcf-c43c-4396-8aea-07c6d9dad76e",
                        side="Sell",
                        price=56300.0,
                        quantity=1,
                        order_status="New",
                    ),
                    "88d6be9c-c6f4-4c2b-87c4-05cb67d2bfc4": bot.Order(
                        order_id="88d6be9c-c6f4-4c2b-87c4-05cb67d2bfc4",
                        side="Sell",
                        price=56500.0,
                        quantity=1,
                        order_status="New",
                    ),
                },
            ),
        )

    def test_bid(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.bid
        bybit_mock.bybit().Market.Market_symbolInfo.assert_called_once()

    def test_ask(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.ask
        bybit_mock.bybit().Market.Market_symbolInfo.assert_called_once()

    def test_cancel_all(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.cancel_all()
        bybit_mock.bybit().Order.Order_cancelAll.assert_called_with(symbol="BTCUSD")

    def test_cancel(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.cancel("88d6be9c-c6f4-4c2b-87c4-05cb67d2bfc4")
        bybit_mock.bybit().Order.Order_cancel.assert_called_with(
            symbol="BTCUSD", order_id="88d6be9c-c6f4-4c2b-87c4-05cb67d2bfc4"
        )

    def test_long(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.long(0, 0)
        bybit_mock.bybit().Order.Order_new.assert_called_with(
            side="Buy",
            symbol="BTCUSD",
            order_type="Limit",
            qty=0,
            price=0,
            time_in_force="PostOnly",
        )

    def test_short(self, bybit_mock, ws_mock):
        ex = bot.BybitExchange()
        ex.short(0, 0)
        bybit_mock.bybit().Order.Order_new.assert_called_with(
            side="Sell",
            symbol="BTCUSD",
            order_type="Limit",
            qty=0,
            price=0,
            time_in_force="PostOnly",
        )
