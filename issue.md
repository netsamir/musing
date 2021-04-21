Dear,

We are executing the following command:

    client.Order.Order_new(
        side="Buy",
        symbol=self.symbol,
        order_type="Limit",
        qty=quantity,
        price=price,
        time_in_force="PostOnly",
    ).result()

It returns the following output:

    ({'ret_code': 0, 'ret_msg': 'OK', 'ext_code': '', 'ext_info': '', 'result':
    {'user_id': 2681267, 'order_id': 'df5cf5ba-2aba-4edd-90e3-f8034b30ca1d',
    'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 54949,
    'qty': 1, 'time_in_force': 'PostOnly', 'order_status': 'Created',
    'last_exec_time': 0, 'last_exec_price': 0, 'leaves_qty': 1, 'cum_exec_qty':
    0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'EC_NoError',
    'order_link_id': '', 'created_at': '2021-04-20T15:37:17.697Z',
    'updated_at': '2021-04-20T15:37:17.697Z'}, 'time_now': '1618933037.697975',
    'rate_limit_status': 99, 'rate_limit_reset_ms': 1618933037696,
    'rate_limit': 100}, <bravado.requests_client.RequestsResponseAdapter object
    at 0x7f6ac8c465b0>)


We can see that we buy Limit, PostOnly at 54949. However, the position shows that that the entry_price is '54975.26113249'.

Could you please tell if it works as design ?

Regards
