# Standard Library
import logging
from argparse import ArgumentParser
from datetime import datetime
from itertools import count
from os import environ
from time import sleep
from typing import List, NamedTuple, Tuple

import bybit  # type: ignore

IDLE_TRIGGER = 10
THRESHOLD = 5

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
LOGGER.addHandler(ch)


class NotInCycle(Exception):
    """ We are not yet in a cycle """


class OrderFailed(Exception):
    """ We are not yet in a cycle """


class Position(NamedTuple):
    """ The order that has been executed and added to the portfolio """

    entry_price: float
    real_entry_price: float
    quantity: int
    # rate_limit_status: int
    # rate_limit_reset: str
    # rate_limit: int


class Orders(NamedTuple):
    longs: List[Tuple[float, int]]
    shorts: List[Tuple[float, int]]


class Exchange:  # pragma: no cover
    def bid(self) -> float:
        ...

    def ask(self) -> float:
        ...

    def long(self) -> float:
        ...

    def short(self) -> float:
        ...

    def position(self) -> Position:
        ...

    def orders(self) -> Orders:
        ...

    def cancel_all(self) -> None:
        ...


def convert_epoch(epoch_ms: int) -> str:
    """ Convert a ms epoch to a human readable format """
    return datetime.fromtimestamp(epoch_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S.%f")


def round_point(entry: str) -> float:
    """ Round the float number to 0 or 5 """
    left, right = str(round(float(entry), 1)).split(".")
    floor = "5" if int(right) // 5 == 1 else "0"
    return float(left + "." + floor)


class BybitExchange(Exchange):
    def __init__(self, symbol: str = "BTCUSD"):
        self.symbol = symbol
        self.client = bybit.bybit(
            test=False,
            api_key=environ["BYBIT_MAINNET_API_KEY"],
            api_secret=environ["BYBIT_MAINNET_API_SECRET"],
        )

    @property
    def bid(self) -> float:
        """
        # [ins] In [41]: %time client.Market.Market_symbolInfo().result()[0]['result'][0]['bid_price'] # CPU times: user 3.06 ms, sys: 220 µs, total: 3.28 ms
        # Wall time: 329 ms
        # Out[41]: '56742.00'
        """
        return float(
            self.client.Market.Market_symbolInfo().result()[0]["result"][0]["bid_price"]
        )

    @property
    def ask(self) -> float:
        return float(
            self.client.Market.Market_symbolInfo().result()[0]["result"][0]["ask_price"]
        )

    @property
    def orders(self) -> Orders:
        """Return the active orders"""
        all_orders = self.client.Order.Order_getOrders(
            symbol=self.symbol, order_status="New"
        ).result()[0]["result"]["data"]

        return Orders(
            longs=[
                (float(order["price"]), int(order["qty"]))
                for order in all_orders
                if order["side"] == "Buy"
            ],
            shorts=[
                (float(order["price"]), int(order["qty"]))
                for order in all_orders
                if order["side"] == "Sell"
            ],
        )

    @property
    def position(self) -> Position:
        """ Return the position """
        my_position = self.client.Positions.Positions_myPosition(
            symbol=self.symbol
        ).result()[0]
        LOGGER.info(f"Position: {my_position}")

        if my_position['result']["size"] == 0:
            raise NotInCycle

        return Position(
            round_point(my_position['result']["entry_price"]),
            my_position['result']["entry_price"],
            my_position['result']["size"],
        )

    def cancel_all(self):
        return self.client.Order.Order_cancelAll(symbol=self.symbol).result()

    def long(self, price: float, quantity: int) -> None:
        """ Put a buy order to on the exchange """
        return self.client.Order.Order_new(
            side="Buy",
            symbol=self.symbol,
            order_type="Limit",
            qty=quantity,
            price=price,
            time_in_force="PostOnly",
        ).result()

    def short(self, price: float, quantity: int) -> None:
        """ Put a buy order to on the exchange """
        return self.client.Order.Order_new(
            side="Sell",
            symbol=self.symbol,
            order_type="Limit",
            qty=quantity,
            price=price,
            time_in_force="PostOnly",
        ).result()


def exchange_factory(exchange_name: str) -> Exchange:
    """ Return the Wrapper around the exchange """
    if exchange_name == "bybit":
        return BybitExchange()
    raise NotImplementedError("Exchange not implemented: {exchange_name}")


class CharlieBot:
    """The CharlieBot is an algorithme that follow Charlie strategy
    of trading on future BCDUSD"""

    def __init__(
        self,
        short_big_spread: int,
        short_small_spread: int,
        long_spread: int,
        init_quantity: int,
        exchange_name: str,
    ) -> None:
        self.short_small_spread = short_small_spread
        self.short_big_spread = short_big_spread
        self.long_spread = long_spread
        self.init_quantity = init_quantity

        self.exchange_name = exchange_name
        self.exchange = exchange_factory(exchange_name)

    def trigger_long(self) -> None:
        """ trigger the start of a trading with the best long """

        current_bid = self.exchange.bid
        LOGGER.info(f"Starting by taking a position: {current_bid}, {self.init_quantity} ...")
        LOGGER.info(self.exchange.long(current_bid, self.init_quantity))
        for _ in count():
            sleep(IDLE_TRIGGER)
            try:
                LOGGER.info("Checking for position ...")
                position = self.exchange.position
            except NotInCycle:
                # LOGGER.info(f'No position, trying to take position: {self.init_quantity}, {new_bid}')
                new_bid = self.exchange.bid
                info_msg = (
                    f"No position found current_bid/new_bid: {current_bid}/{new_bid}."
                )
                info_msg += f" Spread current_bid/new_bid: ({new_bid - current_bid})"
                LOGGER.info(info_msg)
                if current_bid + THRESHOLD < new_bid:
                    LOGGER.info("Cancel previous orders")
                    LOGGER.info(self.exchange.cancel_all())
                    current_bid = new_bid
                    info_msg += (
                        f"Trying to take position: {self.init_quantity}, {current_bid}"
                    )
                    LOGGER.info(info_msg)
                    # LOGGER.info('Cancel all position')

                    LOGGER.info(self.exchange.long(current_bid, self.init_quantity))
                    # LOGGER.info(f'Sleeping {IDLE_TRIGGER} second')
                    LOGGER.info(f"Sleeping {IDLE_TRIGGER} second.")

            else:
                info_msg = f"Position found: {position}. Spread {current_bid}/{position.real_entry_price}: "
                info_msg += f"{float(position.real_entry_price) - current_bid}"
                LOGGER.info(info_msg)
                break

    def trigger_complete(self, position: Position) -> None:
        """ Complete the trigger with a short and a long """
        # LOGGER.info(f'Position found: {position}')
        short_price = position.entry_price + self.short_big_spread
        # LOGGER.info(f'Take a short position: {short_price}, {self.init_quantity}')
        LOGGER.info(f"Take a short order: {short_price}, {self.init_quantity}")
        LOGGER.info(self.exchange.short(short_price, self.init_quantity))

        long_price = position.entry_price - self.long_spread
        # LOGGER.info(f'Take a long position: {long_price}, {self.init_quantity}')
        LOGGER.info(f"Take a long order: {long_price}, {self.init_quantity}")
        LOGGER.info(self.exchange.long(long_price, self.init_quantity))
        return

    def cycle(self) -> None:
        for _ in count():
            try:
                position = self.exchange.position
            except NotInCycle:
                return self.exchange.cancel_all()
            else:
                orders = self.exchange.orders
                if len(orders.longs) == 0:
                    self.exchange.cancel_all()
                    self.exchange.short(
                        position.entry_price + self.short_small_spread,
                        position.quantity - 1,
                    )
                    self.exchange.short(position.entry_price + self.short_big_spread, 1)
                    self.exchange.long(
                        position.entry_price - self.long_spread, position.quantity * 2
                    )
                sleep(IDLE_TRIGGER)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.dict__)


def main():
    """ Entry point to the script """
    parser = ArgumentParser(
        description="Start the execution of the trading with the Bot"
    )

    parser.add_argument(
        "short_big_spread",
        type=int,
        default=1,
        help="The number of point we take from the entry price for the next short order to make a profit",
    )

    parser.add_argument(
        "short_small_spread",
        type=int,
        default=1,
        help="The number of point we take from the entry price for the next short order to reduce our exposure",
    )

    parser.add_argument(
        "long_spread",
        type=int,
        default=1,
        help="The number of point we take from the entry price for the next long order",
    )

    parser.add_argument(
        "initial_quantity",
        type=int,
        default=1,
        help="The initial number of contract to buy (one contract cost one dollar)",
    )

    parser.add_argument(
        "exchange_name",
        choices=["bybit"],
        default="bybit",
        help="The exchange on which the bot should run",
    )

    args = parser.parse_args()
    bot = CharlieBot(
        args.short_big_spread,
        args.short_small_spread,
        args.long_spread,
        args.init_quantity,
        args.exchange_name,
    )

    try:
        logging.info("Start of trading ...")
        logging.info(args)
        bot.start_cycle()
    except KeyboardInterrupt:
        logging.info("End of trading")
