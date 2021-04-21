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

LOGGER = logging.getLogger("crypto_bot")
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER.setLevel(logging.DEBUG)


class NotInCycle(Exception):
    """ We are not yet in a cycle """


class OrderFailed(Exception):
    """ We are not yet in a cycle """


class Position(NamedTuple):
    """ The order that has been executed and added to the portfolio """

    entry_price: float
    real_entry_price: float
    quantity: int
    rate_limit_status: int
    rate_limit_reset: str
    rate_limit: int


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
            test=True,
            api_key=environ["BYBIT_MAINNET_API_KEY"],
            api_secret=environ["BYBIT_MAINNET_API_SECRET"],
        )

    @property
    def bid(self) -> float:
        """ return the bid price """
        return float(
            self.client.Market.Market_symbolInfo().result()[0]["result"][0]["bid_price"]
        )

    @property
    def ask(self) -> float:
        """ return the bid price """
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

        LOGGER.debug(f"Position: {my_position}")

        if my_position["result"]["size"] == 0:
            raise NotInCycle

        return Position(
            round_point(my_position["result"]["entry_price"]),
            float(my_position["result"]["entry_price"]),
            my_position["result"]["size"],
            my_position["rate_limit_status"],
            convert_epoch(my_position["rate_limit_reset_ms"]),
            my_position["rate_limit"],
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
        long_ratio: float,
        init_quantity: int,
        exchange_name: str,
    ) -> None:
        self.short_small_spread = short_small_spread
        self.short_big_spread = short_big_spread
        self.long_ratio = long_ratio
        self.init_quantity = init_quantity

        self.exchange_name = exchange_name
        self.exchange = exchange_factory(exchange_name)

    def trigger_long(self) -> Position:
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
                position_spread = float(position.real_entry_price) - current_bid
                info_msg = f"Position found: {position}. Spread: {current_bid}/{position.real_entry_price}: "
                info_msg += f"{position_spread} ({position_spread / current_bid * 100} %)"
                LOGGER.info(info_msg)
                return position

    def trigger_complete(self) -> Position:
        """ Complete the trigger with a short and a long """
        position = self.position
        short_price = position.entry_price + self.short_big_spread
        LOGGER.info(f"Take a short order: {short_price}, {self.init_quantity}")
        LOGGER.info(self.exchange.short(short_price, self.init_quantity))

        long_price = position.entry_price - self.long_ratio / 100
        LOGGER.info(f"Take a long order: {long_price}, {self.init_quantity}")
        LOGGER.info(self.exchange.long(long_price, self.init_quantity))
        return position

    def start_cycle(self) -> None:
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
                        position.entry_price - self.long_ratio, position.quantity * 2
                    )
                sleep(IDLE_TRIGGER)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.dict__)


def main():
    """ Entry point to the script """
    parser = ArgumentParser(
        description="CharlieBot"
    )

    default_short_big_spread = 100
    help_bs = "The number of point we take from the entry price for the next short order to make a profit,"
    help_bs += f" default: {default_short_big_spread}"
    parser.add_argument(
        "short_big_spread",
        type=int,
        default=default_short_big_spread,
        help=help_bs
    )

    default_short_small_spread = 25
    help_ss = "The number of point we take from the entry price for the next short order to reduce our exposure,"
    help_ss += f" default: {default_short_small_spread}"
    parser.add_argument(
        "short_small_spread",
        type=int,
        default=default_short_small_spread,
        help=help_ss,
    )

    default_long_ratio = 0.001
    help_lr = "The ratio from the entry price for the next long order,"
    help_lr += f" default: {default_long_ratio}"
    parser.add_argument(
        "long_ratio",
        type=float,
        default=default_long_ratio,
        help=help_lr,
    )

    default_qty = 1
    parser.add_argument(
        "initial_quantity",
        type=int,
        default=default_qty,
        help=f"The initial number of contract to buy (one contract cost one dollar), default: {default_qty}",
    )

    default_ex = 'bybit'
    parser.add_argument(
        "exchange_name",
        nargs='?',
        choices=["bybit"],
        default=default_ex,
        help=f"The exchange on which CharlieBot should run, default: {default_ex}",
    )

    args = parser.parse_args()
    bot = CharlieBot(
        args.short_big_spread,
        args.short_small_spread,
        args.long_ratio,
        args.initial_quantity,
        args.exchange_name,
    )

    try:
        LOGGER.info("Start of trading ...")
        bot.exchange.position
    except KeyboardInterrupt:
        logging.info("End of trading")
