# q_bot/mt5_connector.py

"""
Handles all communication with the MetaTrader 5 terminal.

This module is responsible for initializing the connection, logging in,
fetching data (account info, prices, positions), and executing,
modifying, and closing trade orders.
"""

import logging
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

from . import config

log = logging.getLogger(__name__)


def initialize():
    """
    Initializes the connection to the MetaTrader 5 terminal.

    Returns:
        bool: True if connection and login are successful, False otherwise.
    """
    log.info("Initializing MetaTrader 5 connection...")
    if not mt5.initialize(
        login=config.MT5_LOGIN,
        password=config.MT5_PASSWORD,
        server=config.MT5_SERVER,
        path=config.MT5_TERMINAL_PATH
    ):
        log.error(f"MT5 initialize() failed, error code = {mt5.last_error()}")
        return False

    log.info("MT5 connection initialized successfully.")
    account_info = mt5.account_info()
    if account_info is None:
        log.error(f"Failed to get account info, error code = {mt5.last_error()}")
        return False

    log.info(f"Logged in to account #{account_info.login} on {account_info.server}.")
    return True


def shutdown():
    """Shuts down the connection to the MetaTrader 5 terminal."""
    log.info("Shutting down MT5 connection.")
    mt5.shutdown()


def get_account_info():
    """Retrieves account information."""
    return mt5.account_info()


def get_symbol_info_tick(symbol):
    """Retrieves the latest tick information for a symbol."""
    return mt5.symbol_info_tick(symbol)

def get_symbol_info(symbol):
    """
    Retrieves information for a specific symbol and ensures it's selected.

    Args:
        symbol (str): The trading symbol (e.g., "EURUSD").

    Returns:
        mt5.SymbolInfo or None: The symbol info object or None if it fails.
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        log.warning(f"Symbol {symbol} not found, cannot get info.")
        return None

    if not info.visible:
        log.info(f"Symbol {symbol} is not visible, trying to select it.")
        if not mt5.symbol_select(symbol, True):
            log.warning(f"Failed to select symbol {symbol}.")
            return None

    return info


def get_rates(symbol, timeframe_mt5, count):
    """
    Retrieves historical rates for a symbol.

    Args:
        symbol (str): The trading symbol.
        timeframe_mt5: The MT5 timeframe constant (e.g., mt5.TIMEFRAME_M15).
        count (int): The number of candles to retrieve.

    Returns:
        pd.DataFrame or None: A DataFrame with the rates or None on failure.
    """
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, count)
        if rates is None:
            log.error(f"Failed to get rates for {symbol}, error: {mt5.last_error()}")
            return None

        rates_df = pd.DataFrame(rates)
        rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')
        return rates_df
    except Exception as e:
        log.error(f"An exception occurred while getting rates for {symbol}: {e}")
        return None


def get_open_positions(symbol=None):
    """
    Retrieves all open positions, optionally filtered by symbol.

    Args:
        symbol (str, optional): The symbol to filter positions by. Defaults to None.

    Returns:
        list: A list of MT5 position objects.
    """
    if symbol:
        return mt5.positions_get(symbol=symbol)
    return mt5.positions_get()


def place_order(symbol, order_type, volume, stop_loss, take_profit, comment=""):
    """
    Places a new market order.

    Args:
        symbol (str): The trading symbol.
        order_type (int): mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL.
        volume (float): The lot size.
        stop_loss (float): The stop loss price.
        take_profit (float): The take profit price.
        comment (str): A comment for the order.

    Returns:
        mt5.OrderSendResult or None: The result of the order placement.
    """
    symbol_info = get_symbol_info(symbol)
    if not symbol_info:
        return None

    if order_type == mt5.ORDER_TYPE_BUY:
        price = mt5.symbol_info_tick(symbol).ask
    elif order_type == mt5.ORDER_TYPE_SELL:
        price = mt5.symbol_info_tick(symbol).bid
    else:
        log.error(f"Invalid order type: {order_type}")
        return None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 20,  # Slippage
        "magic": config.MAGIC_NUMBER,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    log.info(f"Placing order: {request}")
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log.error(f"Order failed: retcode={result.retcode}, comment={result.comment}")
    else:
        log.info(f"Order placed successfully: ticket={result.order}")

    return result


def close_position(position, comment=""):
    """
    Closes an existing position.

    Args:
        position (mt5.TradePosition): The position object to close.
        comment (str): A comment for the closing order.

    Returns:
        mt5.OrderSendResult or None: The result of the closing order.
    """
    order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": order_type,
        "position": position.ticket,
        "price": price,
        "deviation": 20,
        "magic": config.MAGIC_NUMBER,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    log.info(f"Closing position {position.ticket}: {request}")
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log.error(f"Failed to close position {position.ticket}: retcode={result.retcode}, comment={result.comment}")
    else:
        log.info(f"Position {position.ticket} closed successfully.")

    return result


def modify_position(position_ticket, stop_loss, take_profit):
    """
    Modifies the Stop Loss and Take Profit of an open position.

    Args:
        position_ticket (int): The ticket of the position to modify.
        stop_loss (float): The new stop loss price.
        take_profit (float): The new take profit price.

    Returns:
        mt5.OrderSendResult or None: The result of the modification.
    """
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": position_ticket,
        "sl": stop_loss,
        "tp": take_profit,
    }

    log.info(f"Modifying position {position_ticket}: SL={stop_loss}, TP={take_profit}")
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log.error(f"Failed to modify position {position_ticket}: retcode={result.retcode}, comment={result.comment}")
    else:
        log.info(f"Position {position_ticket} modified successfully.")

    return result
