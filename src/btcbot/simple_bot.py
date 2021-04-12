""" Simple implementation of a pincer strategy """
import argparse
import logging
from itertools import count
from os import environ
from time import sleep
from typing import List, NamedTuple



class NotInCycle(Exception):
    """ We are not yet in a cycle """


class Short(NamedTuple):
    """ The order that has been executed and added to the portfolio """

    price: float
    quantity: float


class Exchange:
    """ Representation of an Exchange """

    def __init__(self, crypto: str = "BTC"):
        self.crypto = "btc"

    def current_price(self) -> None:
        """ A wrapper arount the exchanche that will push the price to the Bot """
        return 60000.0

    def buy_order(self, price: float, quantity: float) -> None:
        """ Put a buy order to on the exchange """
        return None

    def sell_order(self, price: float, quantity: float) -> None:
        """ Put a buy order to on the exchange """
        return None


class ByBitExchange(Exchange):
    # spread to pass an order to be a maker
    tick = environ.get("BTCBOT_BYBIT_TICK", 500)
    pass


def exchange_factory(exchange: str) -> Exchange:
    """ Return the Wrapper around the exchange """
    if exchange == 'bybit':
        return ByBitExchange()


def set_trailingprice(tick_spread: int) -> float:
    """ Function that will provide me the new set price for the entry in the new cycle """
    current_price = exchange_price()
    return current_price - float(tick_spread) * float(TICK)


class SimpleBot:
    """ This is the simple implementation of the BOT given our strategy """

    def __init__(self,
            price_ratio: int,
            quantity_ratio: float,
            expected_profit: float,
            trade_frequency: int,
            exchange: str
        ):
        self.price_ratio = price_ratio
        self.quantity_ratio = quantity_ratio
        self.expected_profit = expected_profit
        self.trade_frequency = trade_frequency

        self.in_cycle = False
        self.shorts: List[Short] = []

        self.exchange = exchange_factory(exchange)


    def start_cycles(self):
        """ Start a busy loop """
        for _ in count():
            sleep(self.trade_frequency)
            self.update_trailing_price

    @property
    def average_price(self):
        """ Return the current average price given the dips """
        if not self.in_cycle:
            raise NotinCycle


def main():
    """ Entry point to the script """
    parser = argparse.ArgumentParser(
        description="Start the execution of the trading with the Bot"
    )
    parser.add_argument(
        "price_ratio",
        type=int,
        default=1,
        help="The number of tick we take from the current price at the start of cycle",
    )
    parser.add_argument(
        "quantity_ratio",
        type=float,
        default=1,
        help="they value we want to apply for every dips on the quantity",
    )
    parser.add_argument(
        "expected_profit",
        type=float,
        default=100,
        help="the profit that we want to take for each cycle",
    )
    parser.add_argument(
        "trade_frequency",
        type=int,
        default=60,
        help="The number in second we update the state of the Bot",
    )
    parser.add_argument(
        "exchange",
        choice=['bybit'],
        default='bybit',
        help="The exchange on which the bot should work",
    )
    args = parser.parse_args()
    bot = SimpleBot(
        args.price_ratio,
        args.quantity_ratio,
        args.expected_profit,
        args.trade_frequency
    )
    try:
        logging.info("Start of trading ...")
        bot.start_cycle()
    except KeyboardInterrupt:
        logging.info("End of trading")
