# Standard Library
import logging
from argparse import ArgumentParser
from datetime import datetime
from itertools import count, zip_longest
from os import environ
from time import sleep
from typing import Dict, NamedTuple, Iterator, Tuple, List

import bybit  # type: ignore
import BybitWebsocket  # type: ignore

LOGGER = logging.getLogger("crypto_bot")
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER.setLevel(logging.INFO)


SLEEP_REST = 5
TRESHOLD_REST = 5
SLEEP_WS = 1


class NotInCycle(Exception):
    """ We are not yet in a cycle """


class Position(NamedTuple):
    """ The order that has been executed and added to the portfolio """

    entry_price: float
    real_entry_price: float
    quantity: int
    rate_limit_status: int
    rate_limit_reset: str
    rate_limit: int


class Order(NamedTuple):
    order_id: str
    side: str
    price: float
    quantity: int
    order_status: str


class Orders(NamedTuple):
    longs: Dict[str, Order]
    shorts: Dict[str, Order]

    def head_longs(self) -> Order:
        """ head of the longs orders """
        return list(self.longs.values())[0]

    def shorts_qty(self) -> int:
        """ Provide the sum of quantity """
        return sum([short.quantity for short in self.shorts.values()])


class Exchange:  # pragma: no cover
    @property
    def bid(self) -> float:
        ...

    @property
    def ask(self) -> float:
        ...

    @property
    def orders(self) -> Orders:
        ...

    @property
    def position(self) -> Position:
        ...

    def long(self, price: float, quantity: int) -> None:
        ...

    def short(self, price: float, quantity: int) -> None:
        ...

    def cancel_all(self) -> None:
        ...

    def cancel(self, order_id: str) -> None:
        ...


def convert_epoch(epoch_ms: int) -> str:
    """ Convert a ms epoch to a human readable format """
    return datetime.fromtimestamp(epoch_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S.%f")


def round_point(entry: float) -> float:
    """ Round the float number to 0 or 5 """
    left, right = str(round(float(entry), 1)).split(".")
    floor = "5" if int(right) // 5 == 1 else "0"
    return float(left + "." + floor)


def bankruptcy_price(
    order_value: float,
    quantity: int,
    account_balance: float,
    order_margin: float,
    fee_to_open: float,
) -> float:
    """Compute the Bankruptcy price for long position in cross margin

    https://help.bybit.com/hc/en-us/articles/360039261334-How-to-calculate-Liquidation-Price-Inverse-Contract-
    """
    return (1.00075 * quantity) / (
        order_value + (account_balance - order_margin - fee_to_open)
    )


def liquidation_price(
    quantity: int,
    entry_price: float,
    account_balance: float,
    order_margin: float,
    fee_to_open: float,
    maintenance_margin: float,
) -> float:
    """Compute the liquidaction price for long position in cross margin

    https://help.bybit.com/hc/en-us/articles/360039261334-How-to-calculate-Liquidation-Price-Inverse-Contract
    """
    bp = bankruptcy_price(
        quantity / entry_price, quantity, account_balance, order_margin, fee_to_open
    )
    Z = -(
        account_balance
        - order_margin
        - quantity / entry_price * maintenance_margin
        - quantity * 0.00075 / bp
    )
    Y = Z / quantity - 1 / entry_price
    return -1 / Y


def allocate_longs(
    price: float,
    qty: int,
    idx: int = 1,
    multiplicator: int = 10,
    intercept: int = 7,
    growth_factor: float = 1.3,
) -> Iterator[Tuple[float, int, float]]:
    """ compute the series of long orders """
    if qty > 2048:
        return
    new_price = round_point(
        round_point(price) - multiplicator * intercept * (growth_factor ** idx)
    )
    yield new_price, qty, round(new_price - price)
    yield from allocate_longs(new_price, qty * 2, idx + 1)


class BybitExchange(Exchange):
    def __init__(self, symbol: str = "BTCUSD"):
        self.symbol = symbol
        self.rest = bybit.bybit(
            test=True,
            api_key=environ["BYBIT_MAINNET_API_KEY"],
            api_secret=environ["BYBIT_MAINNET_API_SECRET"],
        )
        self.ws = BybitWebsocket.BybitWebsocket(
            wsURL="wss://stream-testnet.bybit.com/realtime",
            api_key=environ["BYBIT_MAINNET_API_KEY"],
            api_secret=environ["BYBIT_MAINNET_API_SECRET"],
        )
        self.ws.subscribe_order()
        self._orders = Orders(longs={}, shorts={})

    def _wait_feedback(self) -> None:
        """ Wait Bybit feedback and update states """
        LOGGER.info('Wait for feedback')
        for _ in count():
            feedback = self.ws.get_data("order")
            if feedback:
                LOGGER.debug(f"Feedback Received: {feedback}")
                self.orders = [Order(  # type: ignore
                    order["order_id"],
                    order["side"],
                    float(order["price"]),
                    int(order["qty"]),
                    order["order_status"],
                ) for order in feedback]
                return
            sleep(SLEEP_WS)

    @property
    def bid(self) -> float:
        """ return the bid price """
        return float(
            self.rest.Market.Market_symbolInfo().result()[0]["result"][0]["bid_price"]
        )

    @property
    def ask(self) -> float:
        """ return the bid price """
        return float(
            self.rest.Market.Market_symbolInfo().result()[0]["result"][0]["ask_price"]
        )

    # @property
    # def rest_orders(self) -> Orders:
    #     """Return the active orders"""
    #     return self._orders
    #     all_orders = self.rest.Order.Order_getOrders(
    #         symbol=self.symbol, order_status="New"
    #     ).result()[0]["result"]["data"]

    #     return Orders(
    #         longs=[
    #             Order(order["order_id"], float(order["price"]), int(order["qty"]))
    #             for order in all_orders
    #             if order["side"] == "Buy"
    #         ],
    #         shorts=[
    #             Order(order["order_id"], float(order["price"]), int(order["qty"]))
    #             for order in all_orders
    #             if order["side"] == "Sell"
    #         ],
    #     )

    @property
    def orders(self) -> Orders:
        feedback = self.ws.get_data("order")
        if feedback:
            self.orders = [Order(  # type: ignore
                order["order_id"],
                order["side"],
                float(order["price"]),
                int(order["qty"]),
                order["order_status"],
            ) for order in feedback]
        return self._orders

    @orders.setter
    def orders(self, new_orders: List[Order]) -> None:
        # 1. Update all the orders
        for new_order in new_orders:
            if new_order.side == "Buy":
                self._orders.longs[new_order.order_id] = new_order
            else:
                self._orders.shorts[new_order.order_id] = new_order

        # 2. Remove all none New order
        # 3. Make sure that the orders are sorted by quantity
        self._orders = Orders(
            {
                order.order_id: order
                for order in sorted(
                    self._orders.longs.values(), key=lambda o: o.quantity
                )
                if order.order_status == "New"
            },
            {
                order.order_id: order
                for order in sorted(
                    self._orders.shorts.values(), key=lambda o: o.quantity
                )
                if order.order_status == "New"
            },
        )
        LOGGER.info(f"Orders status: {self._orders}")

    @property
    def position(self) -> Position:
        """ Return the position """
        my_position = self.rest.Positions.Positions_myPosition(
            symbol=self.symbol
        ).result()[0]

        LOGGER.debug(f"Position: {my_position}")

        if my_position["result"]["size"] == 0:
            raise NotInCycle

        return Position(
            round_point(float(my_position["result"]["entry_price"])),
            float(my_position["result"]["entry_price"]),
            my_position["result"]["size"],
            my_position["rate_limit_status"],
            convert_epoch(my_position["rate_limit_reset_ms"]),
            my_position["rate_limit"],
        )

    def cancel_all(self) -> None:
        output = self.rest.Order.Order_cancelAll(symbol=self.symbol).result()

        LOGGER.debug(output)
        self._wait_feedback()
        return

    def cancel(self, order_id: str) -> None:
        output = self.rest.Order.Order_cancel(
            symbol=self.symbol, order_id=order_id
        ).result()

        LOGGER.debug(output)
        self._wait_feedback()
        return

    def long(self, price: float, quantity: int) -> None:
        """ Put a buy order to on the exchange """
        LOGGER.info(f'Long({price}, {quantity}')
        output = self.rest.Order.Order_new(
            side="Buy",
            symbol=self.symbol,
            order_type="Limit",
            qty=quantity,
            price=price,
            time_in_force="PostOnly",
        ).result()

        LOGGER.debug(output)
        self._wait_feedback()
        return

    def short(self, price: float, quantity: int) -> None:
        """ Put a buy order to on the exchange """
        LOGGER.info(f'Long({price}, {quantity}')
        output = self.rest.Order.Order_new(
            side="Sell",
            symbol=self.symbol,
            order_type="Limit",
            qty=quantity,
            price=price,
            time_in_force="PostOnly",
        ).result()

        LOGGER.debug(output)
        self._wait_feedback()
        return


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
        init_quantity: int,
        exchange_name: str,
    ) -> None:
        self.short_small_spread = short_small_spread
        self.short_big_spread = short_big_spread
        self.init_quantity = init_quantity

        self.exchange_name = exchange_name
        self.exchange = exchange_factory(exchange_name)

    def trigger_long(self) -> None:
        """ trigger the start of a trading with the best long """

        current_bid = self.exchange.bid
        LOGGER.info(
            f"Starting by taking a position: {current_bid}, {self.init_quantity} ..."
        )
        self.exchange.long(current_bid, self.init_quantity)
        for _ in count():
            sleep(SLEEP_REST)
            try:
                LOGGER.info("Checking for position ...")
                position = self.exchange.position
            except NotInCycle:
                new_bid = self.exchange.bid
                info_msg = (
                    f"No position found current_bid/new_bid: {current_bid}/{new_bid}."
                )
                info_msg += f" Spread current_bid/new_bid: ({new_bid - current_bid})"
                LOGGER.info(info_msg)
                if current_bid + TRESHOLD_REST < new_bid:
                    for order_id in self.exchange.orders.longs:
                        LOGGER.info(f"Cancel orders: {order_id}")
                        self.exchange.cancel(order_id)
                    current_bid = new_bid
                    info_msg = (
                        f"Trying to take position: {self.init_quantity}, {current_bid}"
                    )
                    LOGGER.info(info_msg)
                    self.exchange.long(current_bid, self.init_quantity)
                    LOGGER.info(f"Sleeping {SLEEP_REST} second.")

            else:
                position_spread = float(position.real_entry_price) - current_bid
                info_msg = f"Position found: {position}."
                info_msg += f"Spread (V): {current_bid} - {position.real_entry_price} = {position_spread}"
                info_msg += f"Spread (%): ({position_spread / current_bid * 100} %)"
                LOGGER.info(info_msg)
                return

    def trigger_complete(self) -> None:
        """ Complete the trigger with a short and a long """
        position = self.exchange.position
        short_price = position.entry_price + self.short_big_spread
        LOGGER.info(f"Take a short order: {short_price}, {self.init_quantity}")
        self.exchange.short(short_price, self.init_quantity)

        for long_price, quantity, spread in allocate_longs(
            position.entry_price, position.quantity
        ):
            LOGGER.info(f"Take a long order: {long_price}, {quantity}, {spread}")
            self.exchange.long(long_price, quantity)
        return

    def start_cycle(self) -> None:
        """ """
        # INVARIANTS:
        # ----------
        # 1. The sum of the shorts quantity is equal to the quantity of the position
        # 2. The head(new_orders.qty) == position.qty * 2 and in general Qn+1 = Qn * 2
        for _ in count():
            sleep(SLEEP_WS)
            try:
                position = self.exchange.position
            except NotInCycle:
                LOGGER.info("Cancel all orders: trade successful!")
                self.exchange.cancel_all()
                return

            orders = self.exchange.orders
            # 1. A long order has been filled.  This increased the quantity position.
            # we need to equalize the shorts orders with two short orders.
            if orders.shorts_qty() < position.quantity:
                LOGGER.info('Shorts Quanty < Position Quantity: {orders.shorts_qty} < {position.quantity}')
                for short in orders.shorts.values():
                    self.exchange.cancel(short.order_id)
                # We want to reduce the exposure by putting an order close to our entry price
                self.exchange.short(
                    position.entry_price + self.short_small_spread,
                    position.quantity - self.init_quantity,
                )
                # We put a second orders in order to make a profit on our trade which correspond to the
                # initital quantity
                self.exchange.short(
                    position.entry_price + self.short_big_spread, self.init_quantity
                )

            if orders.head_longs().quantity != position.quantity * 2:
                LOGGER.info('Head long quantity != Position Quantity: {orders.head_longs()} < {position.quantity}')
                for _long, long_settings in zip_longest(
                    orders.longs.values(),
                    allocate_longs(position.entry_price, position.quantity),
                ):
                    if _long:
                        self.exchange.cancel(_long.order_id)
                    long_price, quantity, spread = long_settings
                    self.exchange.long(long_price, quantity)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.dict__)


def main():
    """ Entry point to the script """
    parser = ArgumentParser(description="CharlieBot")

    default_short_big_spread = 250
    help_bs = "The number of point we take from the entry price for the next short order to make a profit,"
    help_bs += f" default: {default_short_big_spread}"
    parser.add_argument(
        "short_big_spread", type=int, default=default_short_big_spread, help=help_bs
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

    default_qty = 1
    parser.add_argument(
        "initial_quantity",
        type=int,
        default=default_qty,
        help=f"The initial number of contract to buy (one contract cost one dollar), default: {default_qty}",
    )

    default_ex = "bybit"
    parser.add_argument(
        "exchange_name",
        nargs="?",
        choices=["bybit"],
        default=default_ex,
        help=f"The exchange on which CharlieBot should run, default: {default_ex}",
    )

    args = parser.parse_args()
    bot = CharlieBot(
        args.short_big_spread,
        args.short_small_spread,
        args.initial_quantity,
        args.exchange_name,
    )

    try:
        LOGGER.info("Start of trading ...")
        bot.exchange.position
    except KeyboardInterrupt:
        logging.info("End of trading")
