import unittest

from btcbot.simple_bot import SimpleBot, Exchange

class TestStringMethods(unittest.TestCase):
    def test_simplebot(self):
        price_ratio = 1
        quantity_ratio = 2
        expected_profit = 1000
        trade_frequency = 60
        exchange = 'bybit'
        sb = SimpleBot(price_ratio, quantity_ratio, expected_profit, trade_frequency, exchange)
        self.assertEqual(sb.price_ratio, 1)
        self.assertEqual(sb.quantity_ratio, 2)
        self.assertEqual(sb.expected_profit, 1000)
        self.assertEqual(sb.trade_frequency, 60)
        self.assertFalse(sb.in_cycle)
        self.assertEqual(sb.shorts, [])
        self.assertIsInstance(sb.exchange, Exchange)
        self.assertEqual(sb.exchange.tick, 500)
