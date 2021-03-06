# primitives from bybit

.. code-block:: python

        # [ins] In [41]: %time client.Market.Market_symbolInfo().result()[0]['result'][0]['bid_price'] # CPU times: user 3.06 ms, sys: 220 µs, total: 3.28 ms
        # Wall time: 329 ms
        # Out[41]: '56742.00'

        [ins] In [5]: my_position = client.Positions.Positions_myPosition(symbol="BTCUSD").result()

        [ins] In [6]: my_position
        Out[6]:
        ({'ret_code': 0,
        'ret_msg': 'OK',
        'ext_code': '',
        'ext_info': '',
        'result': {'id': 0,
        'position_idx': 0,
        'mode': 0,
        'user_id': 2681267,
        'risk_id': 1,
        'symbol': 'BTCUSD',
        'side': 'Sell',
        'size': 1,
        'position_value': '0.00001644',
        'entry_price': '60827.25060827',
        'is_isolated': False,
        'auto_add_margin': 0,
        'leverage': '100',
        'effective_leverage': '100',
        'position_margin': '0.00000019',
        'liq_price': '999999',
        'bust_price': '999999',
        'occ_closing_fee': '0.00000001',
        'occ_funding_fee': '0',
        'take_profit': '0',
        'stop_loss': '0',
        'trailing_stop': '0',
        'position_status': 'Normal',
        'deleverage_indicator': 4,
        'oc_calc_data': '{"blq":1,"blv":"0.00001648","slq":0,"bmp":60679.6117,"smp":0,"bv2c":0.0115075,"sv2c":0.0114925}',
        'order_margin': '0',
        'wallet_balance': '0.00698916',
        'realised_pnl': '0',
        'unrealised_pnl': 0,
        'cum_realised_pnl': '-0.0002553',
        'cross_seq': 5918591755,
        'position_seq': 0,
        'created_at': '2021-04-12T10:29:40.395983654Z',
        'updated_at': '2021-04-16T12:56:06.01065233Z'},
        'time_now': '1618577766.291858',
        'rate_limit_status': 118,
        'rate_limit_reset_ms': 1618577766288,
        'rate_limit': 120},
        <bravado.requests_client.RequestsResponseAdapter at 0x7fe561e92280>)


            [{'user_id': 2681267,
            'position_idx': 0,
            'order_status': 'New',
            'symbol': 'BTCUSD',
            'side': 'Buy',
            'order_type': 'Limit',
            'price': '55600',
            'qty': '2',
            'time_in_force': 'PostOnly',
            'order_link_id': '',
            'order_id': 'd0aa620e-bcbd-41c6-9315-f1be7570bfe3',
            'created_at': '2021-04-20T12:35:28.941Z',
            'updated_at': '2021-04-20T12:35:28.941Z',
            'leaves_qty': '2',
            'leaves_value': '0.00003597',
            'cum_exec_qty': '0',
            'cum_exec_value': '0',
            'cum_exec_fee': '0',
            'reject_reason': 'EC_NoError'},
            {'user_id': 2681267,
            'position_idx': 0,
            'order_status': 'New',
            'symbol': 'BTCUSD',
            'side': 'Sell',
            'order_type': 'Limit',
            'price': '56300',
            'qty': '1',
            'time_in_force': 'PostOnly',
            'order_link_id': '',
            'order_id': '5b7eebcf-c43c-4396-8aea-07c6d9dad76e',
            'created_at': '2021-04-20T12:35:09.135Z',
            'updated_at': '2021-04-20T12:35:09.135Z',
            'leaves_qty': '1',
            'leaves_value': '0.00001776',
            'cum_exec_qty': '0',
            'cum_exec_value': '0',
            'cum_exec_fee': '0',
            'reject_reason': 'EC_NoError'},
            {'user_id': 2681267,
            'position_idx': 0,
            'order_status': 'New',
            'symbol': 'BTCUSD',
            'side': 'Sell',
            'order_type': 'Limit',
            'price': '56500',
            'qty': '1',
            'time_in_force': 'PostOnly',
            'order_link_id': '',
            'order_id': '88d6be9c-c6f4-4c2b-87c4-05cb67d2bfc4',
            'created_at': '2021-04-20T12:35:00.350Z',
            'updated_at': '2021-04-20T12:35:00.350Z',
            'leaves_qty': '1',
            'leaves_value': '0.00001769',
            'cum_exec_qty': '0',
            'cum_exec_value': '0',
            'cum_exec_fee': '0',
            'reject_reason': 'EC_NoError'}]


::

    # subscribe to topics
    ws.subscribe_orderBookL2("BTCUSD")
    ws.subscribe_kline("BTCUSD", '1m')
    ws.subscribe_order()
    ws.subscribe_execution()
    ws.subscribe_position()
    ws.subscribe_instrument_info('BTCUSD')
    ws.subscribe_insurance()

    # get responses forever
    while(1):
        logger.info(ws.get_data("orderBookL2_25.BTCUSD"))
        logger.info(ws.get_data('kline.BTCUSD.1m'))
        logger.info(ws.get_data('order'))
        logger.info(ws.get_data("execution"))
        logger.info(ws.get_data("position"))
        logger.info(ws.get_data("instrument_info.100ms.BTCUSD"))
        logger.info(ws.get_data('insurance.BTC'))
        logger.info(ws.get_data('insurance.EOS'))
        sleep(1)  # wait one second before checking for new responses

